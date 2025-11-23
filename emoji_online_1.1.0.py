import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta, date, time
import io
import csv
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from keep_alive import keep_alive

# 載入 .env 檔案 (本地開發用)
load_dotenv()

VERSION = "1.1.0 Online"

# ====== 設定參數 (從環境變數讀取) ======
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
FORUM_ID = int(os.getenv("FORUM_ID", 0))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID", 0)) # 需在 .env 設定
BOT_ID = 1436621968601514054  # Bot 的 ID (通常固定，也可改環境變數)
TEACHER_IDS = [983244573289623592]
EMOJI_TO_USE = "🆗"

# 定義台灣時區 (UTC+8)
TZ_TW = timezone(timedelta(hours=8))

def get_week_range(year: int, week: int):
    """回傳指定 ISO 週的 (start_time, end_time)"""
    start_date = date.fromisocalendar(year, week, 1)
    end_date = date.fromisocalendar(year, week, 7)
    start_time = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=TZ_TW)
    end_time = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=TZ_TW)
    return start_time, end_time

def get_month_range(year: int, month: int):
    """回傳指定月份的 (start_time, end_time)"""
    start_date = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    end_date = next_month - timedelta(days=1)
    
    start_time = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=TZ_TW)
    end_time = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=TZ_TW)
    return start_time, end_time

# ====== 資料結構 ======
class UserStats:
    def __init__(self, uid: int, name: str):
        self.uid = uid
        self.name = name
        self.message_count = 0
        self.reaction_count = 0
        self.threads_participated: Dict[str, datetime] = {}  # Thread Name -> Last Interaction Time
        self.active_days: set = set()
        self.bonus = 0
        self.grade = "F/X"
        self.gpa = 0.0
        self.percent_score = 0.0
        self.rank = 0
        self.achievements: List[str] = []

    @property
    def total_interactions(self):
        return self.message_count + self.reaction_count

# ====== 計算等級與 GPA ======
def calculate_grade_gpa(percent_score):
    percent_score = min(percent_score, 100)
    if percent_score >= 90: return "A+", 4.3
    elif percent_score >= 85: return "A", 4.0
    elif percent_score >= 80: return "A-", 3.7
    elif percent_score >= 77: return "B+", 3.3
    elif percent_score >= 73: return "B", 3.0
    elif percent_score >= 70: return "B-", 2.7
    elif percent_score >= 67: return "C+", 2.3
    elif percent_score >= 63: return "C", 2.0
    elif percent_score >= 60: return "C-", 1.7
    else: return "F/X", 0

# ====== Cog ======
class OCWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_stats: Dict[int, UserStats] = {}
        self.last_range_str = "尚無資料" # 儲存上次計算的日期範圍字串
        self.weekly_report_task.start() # 啟動排程任務

    def cog_unload(self):
        self.weekly_report_task.cancel()

    async def _fetch_data(self, interaction: Optional[discord.Interaction], start_time: datetime, end_time: datetime) -> Dict[int, UserStats]:
        """核心資料抓取邏輯"""
        # 如果是自動排程，interaction 為 None，需手動獲取 guild
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            print("❌ 找不到伺服器")
            return {}

        forum = self.bot.get_channel(FORUM_ID)
        if forum is None or not isinstance(forum, discord.ForumChannel):
            if interaction:
                await interaction.followup.send("❌ 找不到論壇頻道或不是 ForumChannel")
            else:
                print("❌ 找不到論壇頻道")
            return {}

        stats_map = {}
        for member in guild.members:
            if not member.bot or member.id == BOT_ID:
                 stats_map[member.id] = UserStats(member.id, member.display_name)
        
        if BOT_ID not in stats_map:
             stats_map[BOT_ID] = UserStats(BOT_ID, "Bot")

        threads_to_process = []
        # 處理非封存貼文
        for thread in forum.threads:
            if start_time <= thread.created_at <= end_time:
                threads_to_process.append(thread)
        # 處理封存貼文
        try:
            async for thread in forum.archived_threads(limit=None):
                if start_time <= thread.created_at <= end_time:
                    threads_to_process.append(thread)
        except discord.Forbidden:
            print("⚠️ 無法抓封存貼文，缺少權限")

        print(f"🔍 開始處理 {len(threads_to_process)} 個貼文...")

        for thread in threads_to_process:
            was_archived = thread.archived
            if was_archived:
                try:
                    await thread.edit(archived=False, locked=False)
                    thread = await thread.fetch()
                except:
                    pass

            async for msg in thread.history(limit=None, after=start_time, before=end_time):
                if msg.author.id in stats_map:
                    user_stat = stats_map[msg.author.id]
                    user_stat.message_count += 1
                    user_stat.threads_participated[thread.name] = msg.created_at
                    user_stat.active_days.add(msg.created_at.date())

                for reaction in msg.reactions:
                    if str(reaction.emoji) == EMOJI_TO_USE:
                        async for user in reaction.users():
                            if user.id in stats_map:
                                r_stat = stats_map[user.id]
                                r_stat.reaction_count += 1
                                r_stat.threads_participated[thread.name] = datetime.now(TZ_TW) # 近似時間

            if was_archived:
                try:
                    await thread.edit(archived=True)
                except:
                    pass
        
        return stats_map

    def _calculate_scores(self, stats_map: Dict[int, UserStats]):
        """計算分數與成就"""
        bot_stat = stats_map.get(BOT_ID)
        bot_reacts = bot_stat.reaction_count if bot_stat else 1
        if bot_reacts == 0: bot_reacts = 1

        for uid, stat in stats_map.items():
            stat.bonus = self.bot.bonus_points.get(uid, 0)
            raw_score = (stat.reaction_count / bot_reacts * 20 + 80) + stat.bonus
            stat.percent_score = min(raw_score, 100)
            stat.grade, stat.gpa = calculate_grade_gpa(stat.percent_score)

            if stat.message_count > 50:
                stat.achievements.append("🗣️ Chatterbox")
            if stat.reaction_count > 100:
                stat.achievements.append("❤️ Supporter")
            if len(stat.threads_participated) > 3:
                stat.achievements.append("🚀 Early Bird")
            if len(stat.active_days) >= 4:
                stat.achievements.append("🐢 Slow & Steady")

        sorted_stats = sorted([s for s in stats_map.values() if s.uid != BOT_ID], key=lambda x: (-x.percent_score, x.name))
        for i, stat in enumerate(sorted_stats, 1):
            stat.rank = i
        
        if BOT_ID in stats_map:
            stats_map[BOT_ID].rank = 0

    # ====== 自動化排程任務 ======
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=TZ_TW))
    async def weekly_report_task(self):
        """每週一凌晨 00:00 (UTC+8) 執行"""
        now = datetime.now(TZ_TW)
        # 檢查是否為星期一 (Monday = 0)
        if now.weekday() == 0:
            print("⏰ 執行週報自動化任務...")
            channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if not channel:
                print("❌ 找不到公告頻道，無法發送週報")
                return

            # 計算上一週的範圍
            current_year, current_week, _ = now.isocalendar()
            last_week_date = now - timedelta(days=7)
            target_year, target_week, _ = last_week_date.isocalendar()
            
            s_time, e_time = get_week_range(target_year, target_week)
            
            # 執行計算
            stats = await self._fetch_data(None, s_time, e_time)
            self._calculate_scores(stats)
            self.last_stats = stats
            
            # 更新日期範圍字串
            self.last_range_str = f"Week {target_week} | {s_time.date()} ~ {e_time.date()}"

            # 產生報告
            msg = f"📢 **自動週報** ({self.last_range_str})\n"
            sorted_users = sorted(stats.values(), key=lambda x: x.rank if x.rank > 0 else 999)
            
            for s in sorted_users:
                if s.uid == BOT_ID: continue
                badges = " ".join(s.achievements)
                msg += f"**{s.rank}. {s.name}**: {s.percent_score:.1f}% ({s.grade}) | 💬 {s.message_count} | 👍 {s.reaction_count} {badges}\n"
            
            await channel.send(msg[:2000])
            
            # 產生排行榜 (前 10 名)
            leaderboard_msg = f"🏆 **本週排行榜** ({self.last_range_str})\n"
            for s in sorted_users[:10]:
                medal = "🥇" if s.rank == 1 else "🥈" if s.rank == 2 else "🥉" if s.rank == 3 else f"{s.rank}."
                leaderboard_msg += f"{medal} **{s.name}** - {s.percent_score:.1f}%\n"
            
            await channel.send(leaderboard_msg)
            print("✅ 週報發送完成")

    @weekly_report_task.before_loop
    async def before_weekly_report_task(self):
        await self.bot.wait_until_ready()

    # ====== 指令區 ======
    @app_commands.command(name="addpoints", description="給使用者加分")
    @app_commands.guilds(GUILD_ID)
    async def addpoints(self, interaction: discord.Interaction, member: discord.Member, points: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 你沒有權限", ephemeral=True)
            return
        self.bot.bonus_points[member.id] = self.bot.bonus_points.get(member.id, 0) + points
        await interaction.response.send_message(f"✅ 已給 {member.display_name} 加 {points} 分", ephemeral=False)

    @app_commands.command(name="resetpoints", description="重置所有使用者加分")
    @app_commands.guilds(GUILD_ID)
    async def resetpoints(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 你沒有權限", ephemeral=True)
            return
        self.bot.bonus_points.clear()
        await interaction.response.send_message("✅ 已重置所有加分", ephemeral=True)

    @app_commands.command(name="compute", description="計算成績與統計 (支援週/月/自訂)")
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(
        week="ISO 週數 (例如 45)", 
        month="月份 (例如 11)", 
        year="年份 (預設今年)",
        start_date="開始日期 (YYYY-MM-DD)",
        end_date="結束日期 (YYYY-MM-DD)"
    )
    async def compute(self, interaction: discord.Interaction, 
                      week: int = None, month: int = None, year: int = None,
                      start_date: str = None, end_date: str = None):
        await interaction.response.defer()
        
        now = datetime.now(TZ_TW)
        target_year = year or now.year
        
        try:
            if start_date and end_date:
                # 自訂日期模式
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                s_time = datetime.combine(s_date, datetime.min.time()).replace(tzinfo=TZ_TW)
                e_time = datetime.combine(e_date, datetime.max.time()).replace(tzinfo=TZ_TW)
                range_label = f"Custom | {s_date} ~ {e_date}"
            elif month:
                # 月份模式
                s_time, e_time = get_month_range(target_year, month)
                range_label = f"Month {month} | {s_time.date()} ~ {e_time.date()}"
            else:
                # 週模式 (預設)
                target_week = week or now.isocalendar()[1]
                s_time, e_time = get_week_range(target_year, target_week)
                range_label = f"Week {target_week} | {s_time.date()} ~ {e_time.date()}"
                
            if s_time > e_time:
                raise ValueError("開始時間不能晚於結束時間")
                
        except ValueError as e:
            await interaction.followup.send(f"❌ 日期錯誤: {e}")
            return

        stats = await self._fetch_data(interaction, s_time, e_time)
        self._calculate_scores(stats)
        self.last_stats = stats
        self.last_range_str = range_label

        msg = f"📊 **統計結果** ({range_label})\n"
        sorted_users = sorted(stats.values(), key=lambda x: x.rank if x.rank > 0 else 999)
        
        for s in sorted_users:
            if s.uid == BOT_ID: continue
            badges = " ".join(s.achievements)
            msg += f"**{s.rank}. {s.name}**: {s.percent_score:.1f}% ({s.grade}) | 💬 {s.message_count} | 👍 {s.reaction_count} {badges}\n"
        
        await interaction.followup.send(msg[:2000])

    @app_commands.command(name="attendance", description="查詢出席率")
    @app_commands.guilds(GUILD_ID)
    async def attendance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        if target.id not in self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return
        
        stat = self.last_stats[target.id]
        
        msg = f"📅 **{target.display_name} 的出席狀況** ({self.last_range_str})\n"
        msg += f"活躍天數: {len(stat.active_days)} 天\n"
        msg += f"活躍日期: {', '.join([str(d) for d in sorted(stat.active_days)])}"
        await interaction.response.send_message(msg)

    @app_commands.command(name="leaderboard", description="顯示排行榜")
    @app_commands.guilds(GUILD_ID)
    async def leaderboard(self, interaction: discord.Interaction):
        if not self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return
            
        sorted_users = sorted([s for s in self.last_stats.values() if s.uid != BOT_ID], key=lambda x: x.rank)
        msg = f"🏆 **排行榜** ({self.last_range_str})\n"
        for s in sorted_users[:10]:
            medal = "🥇" if s.rank == 1 else "🥈" if s.rank == 2 else "🥉" if s.rank == 3 else f"{s.rank}."
            msg += f"{medal} **{s.name}** - {s.percent_score:.1f}%\n"
        
        await interaction.response.send_message(msg)

    @app_commands.command(name="inactive", description="列出未活躍學生 (老師專用)")
    @app_commands.guilds(GUILD_ID)
    async def inactive(self, interaction: discord.Interaction, days: int = 7):
        if interaction.user.id not in TEACHER_IDS:
            await interaction.response.send_message("❌ 只有老師可以使用", ephemeral=True)
            return
            
        if not self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return

        threshold = datetime.now(TZ_TW) - timedelta(days=days)
        inactive_users = []
        
        for stat in self.last_stats.values():
            if stat.uid == BOT_ID: continue
            last_active = datetime.min.replace(tzinfo=TZ_TW)
            if stat.threads_participated:
                last_active = max(stat.threads_participated.values())
            
            if last_active < threshold:
                inactive_users.append(f"{stat.name} (最後互動: {last_active.date() if last_active.year > 1 else '無'})")
        
        if inactive_users:
            await interaction.response.send_message(f"⚠️ **過去 {days} 天未活躍學生** ({self.last_range_str}):\n" + "\n".join(inactive_users))
        else:
            await interaction.response.send_message(f"✅ 所有學生近期都很活躍！ ({self.last_range_str})")

    @app_commands.command(name="matrix", description="顯示參與度矩陣")
    @app_commands.guilds(GUILD_ID)
    async def matrix(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        if target.id not in self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return

        stat = self.last_stats[target.id]
        msg = f"🧩 **{target.display_name} 的參與矩陣** ({self.last_range_str})\n"
        
        if not stat.threads_participated:
            msg += "尚無參與紀錄"
        else:
            for thread_name in stat.threads_participated:
                msg += f"🟩 {thread_name}\n"
        
        await interaction.response.send_message(msg)

    @app_commands.command(name="profile", description="查看個人檔案與成就")
    @app_commands.guilds(GUILD_ID)
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        if target.id not in self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return

        stat = self.last_stats[target.id]
        embed = discord.Embed(title=f"👤 {target.display_name} 的個人檔案", description=f"統計範圍: {self.last_range_str}", color=discord.Color.blue())
        embed.add_field(name="等級", value=f"{stat.grade} ({stat.gpa})", inline=True)
        embed.add_field(name="分數", value=f"{stat.percent_score:.1f}", inline=True)
        embed.add_field(name="排名", value=f"#{stat.rank}", inline=True)
        embed.add_field(name="互動數", value=f"💬 {stat.message_count} | 👍 {stat.reaction_count}", inline=False)
        
        achievements_str = "\n".join(stat.achievements) if stat.achievements else "尚無成就"
        embed.add_field(name="🏆 成就", value=achievements_str, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trycompute", description="試算分數 (私密)")
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(
        start_month="開始月份", start_day="開始日期",
        end_month="結束月份", end_day="結束日期",
        year="年份 (預設今年)", target="指定學生 (老師專用)"
    )
    async def trycompute(self, interaction: discord.Interaction, 
                         start_month: int, start_day: int, 
                         end_month: int, end_day: int, 
                         year: int = None, target: discord.Member = None):
        
        is_teacher = interaction.user.id in TEACHER_IDS
        if target and not is_teacher:
            await interaction.response.send_message("❌ 只有老師可以查詢其他人", ephemeral=True)
            return
        
        target_user = target or interaction.user
        year = year or datetime.now(TZ_TW).year
        
        try:
            s_time = datetime(year, start_month, start_day, tzinfo=TZ_TW)
            e_time = datetime(year, end_month, end_day, 23, 59, 59, tzinfo=TZ_TW)
            if s_time > e_time:
                raise ValueError("開始時間不能晚於結束時間")
        except ValueError as e:
            await interaction.response.send_message(f"❌ 日期錯誤: {e}", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        stats = await self._fetch_data(interaction, s_time, e_time)
        self._calculate_scores(stats)
        
        if target_user.id not in stats:
            await interaction.followup.send("❌ 找不到該使用者的資料 (可能不在伺服器成員列表中)")
            return

        s = stats[target_user.id]
        badges = " ".join(s.achievements)
        
        msg = f"🔍 **試算結果** ({s_time.date()} ~ {e_time.date()})\n"
        msg += f"👤 **{s.name}**\n"
        msg += f"分數: {s.percent_score:.1f}% ({s.grade} / {s.gpa})\n"
        msg += f"互動: 💬 {s.message_count} | 👍 {s.reaction_count}\n"
        msg += f"成就: {badges if badges else '無'}\n"
        msg += f"排名: #{s.rank} (在 {len(stats)} 人中)"
        
        await interaction.followup.send(msg)

    @app_commands.command(name="export", description="匯出成績資料 (CSV)")
    @app_commands.guilds(GUILD_ID)
    async def export(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 只有管理員可以使用", ephemeral=True)
            return
            
        if not self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Grade", "GPA", "Score", "Messages", "Reactions", "Active Days"])
        
        for stat in self.last_stats.values():
            writer.writerow([
                stat.uid, stat.name, stat.grade, stat.gpa, 
                f"{stat.percent_score:.2f}", stat.message_count, 
                stat.reaction_count, len(stat.active_days)
            ])
        
        output.seek(0)
        file = discord.File(io.BytesIO(output.getvalue().encode('utf-8-sig')), filename="grades.csv")
        await interaction.response.send_message(f"✅ 資料匯出完成 ({self.last_range_str})", file=file)

# ====== Bot class ======
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.reactions = True
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.bonus_points = {}

    async def setup_hook(self):
        await self.add_cog(OCWCog(self))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ 指令已同步到伺服器 {GUILD_ID}")

    async def on_ready(self):
        print(f"✅ Bot 已登入: {self.user}")

# ====== Run ======
if __name__ == "__main__":
    # 啟動 Web Server (Keep Alive)
    keep_alive()
    
    if not TOKEN:
        print("❌ 錯誤: 找不到 TOKEN，請檢查 .env 檔案或環境變數")
    else:
        bot = MyBot()
        bot.run(TOKEN)
