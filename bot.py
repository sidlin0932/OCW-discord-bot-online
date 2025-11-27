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
from motor.motor_asyncio import AsyncIOMotorClient

# 載入 .env 檔案 (本地開發用)
load_dotenv()

VERSION = "1.3.1"

# ====== 設定參數 (從環境變數讀取) ======
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
FORUM_ID = int(os.getenv("FORUM_ID", 0))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID", 0)) # 需在 .env 設定
IMAGE_CHANNEL_ID = int(os.getenv("IMAGE_CHANNEL_ID", 0))  # Bot 專區頻道 ID
RENDER_URL = os.getenv("RENDER_URL", "")  # Render 部署的網址
BOT_ID = 1436621968601514054  # Bot 的 ID
MONGO_URI = os.getenv("MONGO_URI")

# 文件對應的 Thread ID (從環境變數讀取)
THREAD_ID_README = int(os.getenv("THREAD_ID_README", 0))
THREAD_ID_ROADMAP = int(os.getenv("THREAD_ID_ROADMAP", 0))
THREAD_ID_CHANGELOG = int(os.getenv("THREAD_ID_CHANGELOG", 0))
THREAD_ID_RELEASE_NOTE = int(os.getenv("THREAD_ID_RELEASE_NOTE", 0))

TEACHER_IDS = [983244573289623592]
EMOJI_TO_USE = "🆗"

# 定義台灣時區 (UTC+8)
TZ_TW = timezone(timedelta(hours=8))

# ====== MongoDB Setup ======
if MONGO_URI:
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["ocw_bot_db"]
    users_collection = db["users"]
    weekly_reports_collection = db["weekly_reports"]
    print("✅ MongoDB 連線設定完成")
else:
    print("⚠️ 未設定 MONGO_URI，資料庫功能將無法使用")
    mongo_client = None
    db = None
    users_collection = None
    weekly_reports_collection = None

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

    def to_dict(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "message_count": self.message_count,
            "reaction_count": self.reaction_count,
            "bonus": self.bonus,
            "grade": self.grade,
            "gpa": self.gpa,
            "percent_score": self.percent_score,
            "rank": self.rank,
            "achievements": self.achievements,
            "active_days_count": len(self.active_days)
        }

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
# ====== Cog ======
class OCWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_stats: Dict[int, UserStats] = {}
        self.last_range_str = "尚無資料" 
        self.last_gpa_info: Dict[int, Dict] = {}  # 儲存最後一次的 GPA 資訊
        self.weekly_report_task.start()
        self.daily_chart_task.start()  # 啟動每日圖表任務 

    def cog_unload(self):
        self.weekly_report_task.cancel()
        self.daily_chart_task.cancel()  # 停止每日圖表任務

    async def _fetch_data(self, interaction: Optional[discord.Interaction], start_time: datetime, end_time: datetime) -> Dict[int, UserStats]:
        """核心資料抓取邏輯 (基於互動時間)"""
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

        # 從 DB 讀取 Bonus Points
        if users_collection is not None:
            async for user_doc in users_collection.find():
                uid = user_doc["_id"]
                if uid in stats_map:
                    stats_map[uid].bonus = user_doc.get("bonus", 0)

        # 收集所有需要檢查的貼文 (活躍 + 封存)
        threads_to_check = []
        # 1. 活躍貼文
        threads_to_check.extend(forum.threads)
        
        # 2. 封存貼文
        try:
            async for thread in forum.archived_threads(limit=None):
                threads_to_check.append(thread)
        except discord.Forbidden:
            print("⚠️ 無法抓封存貼文，缺少權限")

        print(f"🔍 掃描 {len(threads_to_check)} 個貼文中的互動 ({start_time.date()} ~ {end_time.date()})...")

        for thread in threads_to_check:
            try:
                # 抓取指定時間範圍內的訊息
                async for message in thread.history(after=start_time, before=end_time, limit=None):
                    # 排除系統訊息
                    if message.type != discord.MessageType.default and message.type != discord.MessageType.reply:
                        continue
                        
                    # 統計留言
                    if message.author.id in stats_map:
                        user_stat = stats_map[message.author.id]
                        user_stat.message_count += 1
                        user_stat.threads_participated[thread.name] = max(
                            user_stat.threads_participated.get(thread.name, datetime.min.replace(tzinfo=TZ_TW)),
                            message.created_at.replace(tzinfo=TZ_TW)
                        )
                        user_stat.active_days.add(message.created_at.date())

                    # 統計按讚 (Reaction)
                    for reaction in message.reactions:
                        if message.author.id in stats_map:
                            stats_map[message.author.id].reaction_count += reaction.count
                            
            except discord.Forbidden:
                print(f"⚠️ 無法讀取貼文 {thread.name}")
            except Exception as e:
                print(f"❌ 處理貼文 {thread.name} 時發生錯誤: {e}")

        return stats_map

    def _calculate_scores(self, stats_map: Dict[int, UserStats]):
        """計算分數與成就（綜合評分：留言50% + 按讚30% + 討論串20%）"""
        bot_stat = stats_map.get(BOT_ID)
        bot_messages = bot_stat.message_count if bot_stat and bot_stat.message_count > 0 else 1
        bot_reactions = bot_stat.reaction_count if bot_stat and bot_stat.reaction_count > 0 else 1
        bot_threads = len(bot_stat.threads_participated) if bot_stat and bot_stat.threads_participated else 1

        # 第一輪：計算原始分數
        for uid, stat in stats_map.items():
            # 檢查是否活躍
            if stat.message_count == 0 and stat.reaction_count == 0 and not stat.threads_participated:
                stat.percent_score = 0
                stat.grade = "N/A"
                continue

            # 綜合評分：留言 50% + 按讚 30% + 討論串 20%
            message_score = (stat.message_count / bot_messages) * 10  # 最高 10 分
            reaction_score = (stat.reaction_count / bot_reactions) * 6  # 最高 6 分
            thread_score = (len(stat.threads_participated) / bot_threads) * 4  # 最高 4 分
            
            raw_score = 80 + message_score + reaction_score + thread_score + stat.bonus
            stat.percent_score = raw_score  # 先不限制上限

            if stat.message_count > 50:
                stat.achievements.append("🗣️ Chatterbox")
            if stat.reaction_count > 100:
                stat.achievements.append("❤️ Supporter")
            if len(stat.threads_participated) > 3:
                stat.achievements.append("🚀 Early Bird")
            if len(stat.active_days) >= 4:
                stat.achievements.append("🐢 Slow & Steady")

        # 動態分數正規化：如果有人超過 100，以最高分為 100 基準縮放
        non_bot_stats = [s for s in stats_map.values() if s.uid != BOT_ID and s.grade != "N/A"]
        if non_bot_stats:
            max_score = max(s.percent_score for s in non_bot_stats)
            
            if max_score > 100:
                scale_factor = 100.0 / max_score
                for uid, stat in stats_map.items():
                    if stat.grade != "N/A":
                        stat.percent_score = stat.percent_score * scale_factor
            else:
                for uid, stat in stats_map.items():
                    if stat.grade != "N/A":
                        stat.percent_score = min(stat.percent_score, 100)
        
        # 計算等第和 GPA
        for uid, stat in stats_map.items():
            if stat.grade != "N/A":
                stat.grade, stat.gpa = calculate_grade_gpa(stat.percent_score)
            else:
                stat.gpa = 0.0

        sorted_stats = sorted([s for s in stats_map.values() if s.uid != BOT_ID], key=lambda x: (-x.percent_score, x.name))
        for i, stat in enumerate(sorted_stats, 1):
            stat.rank = i
        
        if BOT_ID in stats_map:
            stats_map[BOT_ID].rank = 0

    async def _calculate_cumulative_gpa(self, current_stats: Dict[int, UserStats], current_year: int, current_week: int):
        """計算累計 GPA（從 Week 40, 2025 開始，等權重平均）"""
        if weekly_reports_collection is None:
            return {}
        
        START_YEAR = 2025
        START_WEEK = 40
        gpa_data = {}
        
        try:
            query = {
                "$or": [
                    {"year": START_YEAR, "week": {"$gte": START_WEEK, "$lt": current_week}},
                    {"year": {"$gt": START_YEAR, "$lt": current_year}},
                    {"year": current_year, "week": {"$lt": current_week}}
                ]
            }
            
            historical_reports = []
            async for report in weekly_reports_collection.find().sort([("year", 1), ("week", 1)]):
                year = report.get("year")
                week = report.get("week")
                
                if year == current_year and week == current_week: continue
                if year < START_YEAR: continue
                if year == START_YEAR and week < START_WEEK: continue
                if year > current_year: continue
                if year == current_year and week > current_week: continue
                    
                historical_reports.append(report)
            
            for report in historical_reports:
                for user_stat in report.get("stats", []):
                    uid = user_stat.get("uid")
                    gpa = user_stat.get("gpa", 0)
                    
                    msg_count = user_stat.get("message_count", 0)
                    react_count = user_stat.get("reaction_count", 0)
                    active_days = user_stat.get("active_days_count", 0)
                    
                    if msg_count == 0 and react_count == 0 and active_days == 0:
                        continue
                    
                    if uid not in gpa_data:
                        gpa_data[uid] = []
                    gpa_data[uid].append(gpa)
            
            result = {}
            for uid, stat in current_stats.items():
                if uid == BOT_ID: continue
                
                past_gpas = gpa_data.get(uid, [])
                has_current_data = (stat.message_count > 0 or stat.reaction_count > 0 or len(stat.active_days) > 0)
                
                week_count = len(past_gpas)
                past_gpa = sum(past_gpas) / week_count if week_count > 0 else 0.0
                
                if has_current_data:
                    all_gpas = past_gpas + [stat.gpa]
                    with_current_gpa = sum(all_gpas) / len(all_gpas)
                else:
                    with_current_gpa = past_gpa
                
                result[uid] = {
                    "past_gpa": past_gpa,
                    "with_current_gpa": with_current_gpa,
                    "week_count": week_count
                }
            return result
        except Exception as e:
            print(f"❌ 計算累計 GPA 失敗: {e}")
            return {}
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=TZ_TW))
    async def weekly_report_task(self):
        """每週一凌晨 00:00 (UTC+8) 執行"""
        now = datetime.now(TZ_TW)
        if now.weekday() == 0:
            print("⏰ 執行週報自動化任務...")
            channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if not channel:
                print("❌ 找不到公告頻道，無法發送週報")
                return

            current_year, current_week, _ = now.isocalendar()
            last_week_date = now - timedelta(days=7)
            target_year, target_week, _ = last_week_date.isocalendar()
            
            s_time, e_time = get_week_range(target_year, target_week)
            
            stats = await self._fetch_data(None, s_time, e_time)
            self._calculate_scores(stats)
            self.last_stats = stats
            self.last_range_str = f"Week {target_week} | {s_time.date()} ~ {e_time.date()}"

            # 儲存週報到 DB
            if weekly_reports_collection is not None:
                report_doc = {
                    "year": target_year,
                    "week": target_week,
                    "start_date": s_time,
                    "end_date": e_time,
                    "range_str": self.last_range_str,
                    "stats": [s.to_dict() for s in stats.values()],
                    "created_at": datetime.now(TZ_TW)
                }
                await weekly_reports_collection.replace_one(
                    {"year": target_year, "week": target_week},
                    report_doc,
                    upsert=True
                )
                print(f"✅ 週報資料已儲存至 DB (Week {target_week})")

            # 產生報告
            msg = f"📢 **自動週報** ({self.last_range_str})\n"
            sorted_users = sorted(stats.values(), key=lambda x: x.rank if x.rank > 0 else 999)
            
            for s in sorted_users:
                if s.uid == BOT_ID: continue
                badges = " ".join(s.achievements)
                msg += f"**{s.rank}. {s.name}**: {s.percent_score:.1f}% ({s.grade}) | 💬 {s.message_count} | 👍 {s.reaction_count} {badges}\n"
            
            await channel.send(msg[:2000])
            
            leaderboard_msg = f"🏆 **本週排行榜** ({self.last_range_str})\n"
            for s in sorted_users[:10]:
                medal = "🥇" if s.rank == 1 else "🥈" if s.rank == 2 else "🥉" if s.rank == 3 else f"{s.rank}."
                leaderboard_msg += f"{medal} **{s.name}** - {s.percent_score:.1f}%\n"
            
            await channel.send(leaderboard_msg)
            print("✅ 週報發送完成")

    @weekly_report_task.before_loop
    async def before_weekly_report_task(self):
        await self.bot.wait_until_ready()

    # ====== 每日圖表發送任務 ======
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=TZ_TW))
    async def daily_chart_task(self):
        """每天凌晨 00:00 (UTC+8) 發送趨勢圖"""
        print("📊 執行每日圖表發送任務...")
        
        if not IMAGE_CHANNEL_ID or not RENDER_URL:
            print("⚠️ 未設定 IMAGE_CHANNEL_ID 或 RENDER_URL，跳過圖表發送")
            return
        
        channel = self.bot.get_channel(IMAGE_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(IMAGE_CHANNEL_ID)
            except:
                print(f"❌ 找不到圖片頻道 (ID: {IMAGE_CHANNEL_ID})")
                return
        
        # 生成趨勢圖連結
        trends_url = f"{RENDER_URL.rstrip('/')}/trends"
        now = datetime.now(TZ_TW)
        
        embed = discord.Embed(
            title="📈 每日學習趨勢圖",
            description=f"查看所有學生的學習進度與得分趨勢",
            color=discord.Color.blue(),
            timestamp=now
        )
        embed.add_field(name="📊 趨勢圖表", value=f"[點擊查看互動式圖表]({trends_url})", inline=False)
        embed.add_field(name="📅 更新時間", value=now.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.set_footer(text=f"OCW Bot v{VERSION}")
        
        try:
            await channel.send(embed=embed)
            print(f"✅ 趨勢圖已發送至頻道 {channel.name}")
        except Exception as e:
            print(f"❌ 發送趨勢圖失敗: {e}")

    @daily_chart_task.before_loop
    async def before_daily_chart_task(self):
        await self.bot.wait_until_ready()

    # ====== 指令區 ======
    @app_commands.command(name="addpoints", description="給使用者加分")
    @app_commands.guilds(GUILD_ID)
    async def addpoints(self, interaction: discord.Interaction, member: discord.Member, points: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 你沒有權限", ephemeral=True)
            return
        
        if users_collection is None:
            await interaction.response.send_message("❌ 資料庫未連接", ephemeral=True)
            return

        # 更新 DB
        await users_collection.update_one(
            {"_id": member.id},
            {"$inc": {"bonus": points}, "$set": {"name": member.display_name}},
            upsert=True
        )
        
        # 讀取新分數
        user_doc = await users_collection.find_one({"_id": member.id})
        new_bonus = user_doc.get("bonus", 0)
        
        await interaction.response.send_message(f"✅ 已給 {member.display_name} 加 {points} 分 (目前總加分: {new_bonus})", ephemeral=False)

    @app_commands.command(name="resetpoints", description="重置所有使用者加分")
    @app_commands.guilds(GUILD_ID)
    async def resetpoints(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 你沒有權限", ephemeral=True)
            return
        
        if users_collection is None:
            await interaction.response.send_message("❌ 資料庫未連接", ephemeral=True)
            return

        await users_collection.update_many({}, {"$set": {"bonus": 0}})
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
        
        # 檢查是否有有效數據
        active_users = [s for s in stats.values() if s.uid != BOT_ID and s.grade != "N/A"]
        if not active_users:
            await interaction.followup.send(f"📅 **統計結果** ({range_label})\n\n該週沒有任何課程活動紀錄 (無互動數據)。")
            return

        # 計算累計 GPA（如果是週模式）
        gpa_info = {}
        if not month and not start_date:  # 週模式
            target_week = week or now.isocalendar()[1]
            gpa_info = await self._calculate_cumulative_gpa(stats, target_year, target_week)
            self.last_gpa_info = gpa_info  # 保存 GPA 資訊供 /leaderboard 使用

        msg = f"📊 **統計結果** ({range_label})\n\n"
        
        # 計算基準值
        bot_stat = stats.get(BOT_ID)
        bot_messages = bot_stat.message_count if bot_stat and bot_stat.message_count > 0 else 1
        bot_reactions = bot_stat.reaction_count if bot_stat and bot_stat.reaction_count > 0 else 1
        bot_threads = len(bot_stat.threads_participated) if bot_stat and bot_stat.threads_participated else 1
        
        msg += f"📌 **評分基準**: 留言 {bot_messages}(50%) + 按讚 {bot_reactions}(30%) + 討論串 {bot_threads}(20%)\n"
        msg += f"{'─'*40}\n\n"

        sorted_users = sorted(active_users, key=lambda x: x.rank if x.rank > 0 else 999)
        
        for s in sorted_users:
            # 計算各項得分細節
            message_score = (s.message_count / bot_messages) * 10
            reaction_score = (s.reaction_count / bot_reactions) * 6
            thread_score = (len(s.threads_participated) / bot_threads) * 4
            
            # 排名勳章
            rank_medal = "🥇" if s.rank == 1 else "🥈" if s.rank == 2 else "🥉" if s.rank == 3 else f"{s.rank}."
            
            # 主要資訊：排名 + 姓名 + 成績 + 等第 + GPA
            msg += f"{rank_medal} **{s.name}** → **{s.percent_score:.1f}分 ({s.grade})**"
            
            # GPA 資訊（放在主要資訊行，更突出）
            if s.uid in gpa_info:
                gpa_data = gpa_info[s.uid]
                if gpa_data["week_count"] > 0:
                    msg += f" | **GPA: {gpa_data['with_current_gpa']:.2f}** ({gpa_data['past_gpa']:.2f}→)"
                else:
                    msg += f" | **GPA: {gpa_data['with_current_gpa']:.2f}** (新)"
            
            if s.bonus > 0:
                msg += f" [+{s.bonus}]"
            msg += f"\n"
            
            # 次要資訊：互動細節
            msg += f"    留言 {s.message_count}({message_score:.1f}) · 按讚 {s.reaction_count}({reaction_score:.1f}) · 討論串 {len(s.threads_participated)}({thread_score:.1f}) · 活躍 {len(s.active_days)}天"
            
            # 成就（若有）
            if s.achievements:
                badges = " ".join(s.achievements)
                msg += f"\n    {badges}"
            
            msg += "\n\n"
        
        # 避免超過 2000 字元
        if len(msg) > 2000:
            # 簡單的分段發送策略
            parts = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
            for part in parts:
                await interaction.followup.send(part)
        else:
            await interaction.followup.send(msg)



    @app_commands.command(name="history", description="查詢歷史週報 (從資料庫)")
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(week="ISO 週數", year="年份 (預設今年)")
    async def history(self, interaction: discord.Interaction, week: int, year: int = None):
        year = year or datetime.now(TZ_TW).year
        await interaction.response.defer()
        
        if weekly_reports_collection is None:
            await interaction.followup.send("❌ 資料庫未連接")
            return

        doc = await weekly_reports_collection.find_one({"year": year, "week": week})
        if not doc:
            await interaction.followup.send(f"❌ 找不到 {year} Week {week} 的歷史資料")
            return
            
        range_str = doc.get("range_str", "Unknown Range")
        stats_list = doc.get("stats", [])
        
        msg = f"📜 **歷史週報查詢** ({range_str})\n"
        # 簡單排序
        sorted_stats = sorted(stats_list, key=lambda x: x.get("rank", 999) if x.get("rank", 0) > 0 else 999)
        
        for s in sorted_stats:
            if s["uid"] == BOT_ID: continue
            badges = " ".join(s.get("achievements", []))
            msg += f"**{s['rank']}. {s['name']}**: {s['percent_score']:.1f}% ({s['grade']}) | 💬 {s['message_count']} | 👍 {s['reaction_count']} {badges}\n"
            
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
    @app_commands.describe(
        week="週數 (例如 48)",
        month="月份 (例如 11)",
        year="年份 (預設今年)",
        from_oct1="從 10/1 開始計算 (True/False)",
        start_date="自訂開始日期 (YYYY-MM-DD)",
        end_date="自訂結束日期 (YYYY-MM-DD)"
    )
    async def leaderboard(self, interaction: discord.Interaction, 
                         week: int = None, 
                         month: int = None, 
                         year: int = None,
                         from_oct1: bool = False,
                         start_date: str = None,
                         end_date: str = None):
        
        await interaction.response.defer()
        
        now = datetime.now(TZ_TW)
        target_year = year or now.year
        
        # 決定時間範圍
        try:
            if from_oct1:
                # 從 10/1 到現在
                s_time = datetime(2025, 10, 1, tzinfo=TZ_TW)
                e_time = datetime.now(TZ_TW)
                range_label = f"從 10/1 至今 | {s_time.date()} ~ {e_time.date()}"
            elif start_date and end_date:
                # 自訂日期模式
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                s_time = datetime.combine(s_date, datetime.min.time()).replace(tzinfo=TZ_TW)
                e_time = datetime.combine(e_date, datetime.max.time()).replace(tzinfo=TZ_TW)
                range_label = f"自訂 | {s_date} ~ {e_date}"
            elif month:
                # 月份模式
                s_time, e_time = get_month_range(target_year, month)
                range_label = f"本月 ({target_year}/{month})"
            elif year and not week and not month:
                # 年度模式
                s_time = datetime(target_year, 1, 1, tzinfo=TZ_TW)
                e_time = datetime(target_year, 12, 31, 23, 59, 59, tzinfo=TZ_TW)
                range_label = f"本年 ({target_year})"
            else:
                # 週模式 (預設本週)
                target_week = week or now.isocalendar()[1]
                s_time, e_time = get_week_range(target_year, target_week)
                range_label = f"本週 (Week {target_week})"
                
            if s_time > e_time:
                raise ValueError("開始時間不能晚於結束時間")
                
        except ValueError as e:
            await interaction.followup.send(f"❌ 日期錯誤: {e}")
            return
        
        # 重新計算數據
        stats = await self._fetch_data(None, s_time, e_time)
        self._calculate_scores(stats)
        
        # 計算 GPA（如果是週模式）
        gpa_info = {}
        if week or (not month and not year and not from_oct1 and not start_date):
            target_week = week or now.isocalendar()[1]
            gpa_info = await self._calculate_cumulative_gpa(stats, target_year, target_week)
        
        # 排序
        sorted_users = sorted([s for s in stats.values() if s.uid != BOT_ID], key=lambda x: x.rank)
        
        if not sorted_users:
            await interaction.followup.send(f"❌ 該時間範圍內沒有資料")
            return
        
        msg = f"🏆 **排行榜** ({range_label})\n\n"
        
        for s in sorted_users[:10]:
            medal = "🥇" if s.rank == 1 else "🥈" if s.rank == 2 else "🥉" if s.rank == 3 else f"{s.rank}."
            msg += f"{medal} **{s.name}** - {s.percent_score:.1f}分 ({s.grade})"
            
            # 顯示 GPA（若有）
            if s.uid in gpa_info:
                gpa_data = gpa_info[s.uid]
                msg += f" | **GPA: {gpa_data['with_current_gpa']:.2f}**"
            
            msg += "\n"
        
        await interaction.followup.send(msg)



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
        if not self.last_stats:
            await interaction.response.send_message("❌ 無資料，請先執行 `/compute`", ephemeral=True)
            return

        await interaction.response.defer()
        
        # 如果指定成員，只顯示該成員
        if member:
            if member.id not in self.last_stats:
                await interaction.followup.send(f"❌ 找不到 {member.display_name} 的資料")
                return
            
            stat = self.last_stats[member.id]
            msg = f"🧩 **{member.display_name} 的參與矩陣** ({self.last_range_str})\n\n"
            
            if not stat.threads_participated:
                msg += "尚無參與紀錄"
            else:
                for thread_name in stat.threads_participated:
                    msg += f"🟩 {thread_name}\n"
            
            await interaction.followup.send(msg)
            return
        
        # 顯示所有成員的參與矩陣
        # 收集所有討論串
        all_threads = set()
        for stat in self.last_stats.values():
            if stat.uid == BOT_ID:
                continue
            all_threads.update(stat.threads_participated.keys())
        
        if not all_threads:
            await interaction.followup.send("❌ 目前沒有任何討論串參與記錄")
            return
        
        all_threads = sorted(all_threads)
        sorted_users = sorted([s for s in self.last_stats.values() if s.uid != BOT_ID], 
                            key=lambda x: x.rank if x.rank > 0 else 999)
        
        # 建立矩陣
        msg = f"🧩 **參與度矩陣** ({self.last_range_str})\n\n"
        msg += f"📊 共 {len(sorted_users)} 位成員 × {len(all_threads)} 個討論串\n"
        msg += f"{'─'*40}\n\n"
        
        for user_stat in sorted_users:
            participated_threads = list(user_stat.threads_participated.keys())
            participation_count = len(participated_threads)
            
            msg += f"**{user_stat.name}** ({participation_count}/{len(all_threads)})\n"
            
            # 顯示參與的討論串
            if participated_threads:
                # 限制每行長度，避免訊息過長
                thread_list = ", ".join(participated_threads[:5])
                if len(participated_threads) > 5:
                    thread_list += f" ... (+{len(participated_threads)-5})"
                msg += f"  └ {thread_list}\n"
            else:
                msg += f"  └ 無參與記錄\n"
            
            msg += "\n"
        
        # 分段發送（避免超過 2000 字元）
        if len(msg) > 2000:
            parts = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
            for part in parts:
                await interaction.followup.send(part)
        else:
            await interaction.followup.send(msg)


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

    @app_commands.command(name="sendchart", description="手動發送趨勢圖到 Bot 專區")
    @app_commands.guilds(GUILD_ID)
    async def sendchart(self, interaction: discord.Interaction):
        """手動觸發趨勢圖發送"""
        await interaction.response.defer(ephemeral=True)
        
        if not IMAGE_CHANNEL_ID or not RENDER_URL:
            await interaction.followup.send("❌ 未設定 IMAGE_CHANNEL_ID 或 RENDER_URL")
            return
        
        channel = self.bot.get_channel(IMAGE_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(IMAGE_CHANNEL_ID)
            except:
                await interaction.followup.send(f"❌ 找不到圖片頻道 (ID: {IMAGE_CHANNEL_ID})")
                return
        
        # 生成趨勢圖連結
        trends_url = f"{RENDER_URL.rstrip('/')}/trends"
        now = datetime.now(TZ_TW)
        
        embed = discord.Embed(
            title="📈 學習趨勢圖",
            description=f"查看所有學生的學習進度與得分趨勢",
            color=discord.Color.blue(),
            timestamp=now
        )
        embed.add_field(name="📊 趨勢圖表", value=f"[點擊查看互動式圖表]({trends_url})", inline=False)
        embed.add_field(name="📅 更新時間", value=now.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.add_field(name="👤 發送者", value=interaction.user.mention, inline=False)
        embed.set_footer(text=f"OCW Bot v{VERSION}")
        
        try:
            await channel.send(embed=embed)
            await interaction.followup.send(f"✅ 趨勢圖已發送至 {channel.mention}")
        except Exception as e:
            await interaction.followup.send(f"❌ 發送失敗: {e}")

class PolicyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ 我同意 (I Agree)", style=discord.ButtonStyle.success, custom_id="policy_agree_btn")
    async def agree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ 感謝您的確認！我們已記錄您的同意。", ephemeral=True)

# ====== Bot class ======
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.reactions = True
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.bonus_points = {} # 這裡保留作為 cache，但主要操作都直接對 DB

    async def setup_hook(self):
        await self.add_cog(OCWCog(self))
        self.add_view(PolicyView()) # 註冊 Persistent View
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ 指令已同步到伺服器 {GUILD_ID}")

    async def on_ready(self):
        print(f"✅ Bot 已登入: {self.user}")
        # 啟動時檢查並更新文件
        self.bg_task = self.loop.create_task(self.check_and_update_docs())
        # 啟動時自動計算所有歷史數據（供儀表板使用）
        self.loop.create_task(self.auto_compute_all_weeks())
        # 發布 Policy 公告
        self.loop.create_task(self.announce_policy())

    async def announce_policy(self):
        """發布成績計算 Policy 公告"""
        POLICY_CHANNEL_ID = 1423838070649782272
        try:
            channel = self.get_channel(POLICY_CHANNEL_ID)
            if not channel:
                channel = await self.fetch_channel(POLICY_CHANNEL_ID)
        except:
            print("❌ 無法找到 Policy 公告頻道")
            return

        # 檢查是否已發布
        async for message in channel.history(limit=10):
            if message.author.id == self.user.id and message.embeds and "成績計算 Policy 更新" in message.embeds[0].title:
                print("ℹ️ Policy 公告已存在")
                return

        embed = discord.Embed(
            title="📢 成績計算 Policy 更新 (v1.3.0)",
            description="為了更公平地反映大家的學習狀況，我們對成績計算方式進行了以下調整：",
            color=discord.Color.gold()
        )
        embed.add_field(name="1. 互動時間基準", value="現在以**互動發生時間**為準。即使是舊的課程討論串，只要本週有新留言或按讚，都會計入本週成績。", inline=False)
        embed.add_field(name="2. 動態評分機制", value="若當週最高分超過 100 分，將以最高分為基準進行正規化 (Scale Down)，確保分數在 0-100 之間。", inline=False)
        embed.add_field(name="3. 累計 GPA", value="從 2025 第 40 週 (10/1) 開始計算累計 GPA。每週權重相同。", inline=False)
        embed.add_field(name="4. 空週處理", value="若該週無任何互動紀錄，將不計入 GPA 計算，亦不顯示成績。", inline=False)
        embed.add_field(name="確認", value="請閱讀以上變更，並點擊下方按鈕確認。", inline=False)

        view = PolicyView()
        await channel.send(embed=embed, view=view)
        print("✅ Policy 公告已發布")
    
    async def on_message(self, message):
        """監聽訊息事件，自動更新該週數據"""
        # 忽略 Bot 自己的訊息
        if message.author.bot:
            return

        # 檢查是否在論壇的 Thread 中 (Thread 的 parent_id 應該是 FORUM_ID)
        is_forum_thread = False
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == FORUM_ID:
            is_forum_thread = True
        
        if not is_forum_thread:
            return
        
        # 獲取訊息所屬週次
        msg_time = message.created_at.astimezone(TZ_TW)
        year, week, _ = msg_time.isocalendar()
        
        # 背景任務：重新計算該週數據
        self.loop.create_task(self._recalculate_week(year, week))
    
    async def on_raw_reaction_add(self, payload):
        """監聽按讚事件，自動更新該週數據"""
        # 獲取頻道
        try:
            channel = self.get_channel(payload.channel_id)
            
            # 檢查是否在論壇的 Thread 中
            if not isinstance(channel, discord.Thread) or channel.parent_id != FORUM_ID:
                return

            message = await channel.fetch_message(payload.message_id)
            
            # 獲取訊息所屬週次
            msg_time = message.created_at.astimezone(TZ_TW)
            year, week, _ = msg_time.isocalendar()
            
            # 背景任務：重新計算該週數據
            self.loop.create_task(self._recalculate_week(year, week))
        except:
            pass
    
    async def on_raw_reaction_remove(self, payload):
        """監聽取消按讚事件，自動更新該週數據"""
        try:
            channel = self.get_channel(payload.channel_id)
            
            # 檢查是否在論壇的 Thread 中
            if not isinstance(channel, discord.Thread) or channel.parent_id != FORUM_ID:
                return

            message = await channel.fetch_message(payload.message_id)
            
            msg_time = message.created_at.astimezone(TZ_TW)
            year, week, _ = msg_time.isocalendar()
            
            self.loop.create_task(self._recalculate_week(year, week))
        except:
            pass
    
    async def _recalculate_week(self, year: int, week: int):
        """重新計算指定週次的數據"""
        try:
            cog = self.get_cog("OCWCog")
            if not cog or weekly_reports_collection is None:
                return
            
            s_time, e_time = get_week_range(year, week)
            stats = await cog._fetch_data(None, s_time, e_time)
            cog._calculate_scores(stats)
            
            # 如果目前記憶體中的數據剛好是這一週，則同步更新記憶體
            if cog.last_range_str.startswith(f"Week {week} |"):
                cog.last_stats = stats
                print(f"🔄 同步更新 Cache 數據 (Week {week})")
            
            # 更新資料庫
            report_data = {
                "year": year,
                "week": week,
                "range_str": f"{s_time.strftime('%Y-%m-%d')} ~ {e_time.strftime('%Y-%m-%d')}",
                "stats": [s.to_dict() for s in stats.values()]
            }
            await weekly_reports_collection.replace_one(
                {"year": year, "week": week},
                report_data,
                upsert=True
            )
            print(f"🔄 已更新 Week {week}/{year} 數據")
        except Exception as e:
            print(f"❌ 更新 Week {week}/{year} 失敗: {e}")

    async def check_and_update_docs(self):
        """自動檢查並更新論壇文件"""
        await self.wait_until_ready()
        print("🔍 開始檢查文件更新...")
        
        # 1. README (Highlight Mode)
        await self._update_doc_highlight_mode(THREAD_ID_README, "README.md", "README")
        
        # 1.5. DEPLOY_GUIDE (作為 README 的回覆)
        await self._reply_deploy_guide_to_readme(THREAD_ID_README, "DEPLOY_GUIDE.md")
        
        # 2. ROADMAP (Highlight Mode)
        await self._update_doc_highlight_mode(THREAD_ID_ROADMAP, "ROADMAP.md", "ROADMAP")
        
        # 3. RELEASE_NOTE (Version Check Mode)
        await self._update_doc_version_check(THREAD_ID_RELEASE_NOTE, "RELEASE_NOTE.md", "Release Note")
        
        # 4. CHANGELOG (Smart History Mode)
        await self._update_doc_changelog_smart(THREAD_ID_CHANGELOG, "CHANGELOG.md")
        
        print("✅ 文件檢查完成")

    async def auto_compute_all_weeks(self):
        """Bot 啟動時自動計算所有歷史週數據（從第 40 週開始，供儀表板使用）"""
        await self.wait_until_ready()
        
        # 等待 30 秒讓 Discord Cache 完全載入
        print("📊 準備自動計算歷史數據，等待 Discord Cache 載入...")
        import asyncio
        await asyncio.sleep(30)
        
        print("📊 開始自動計算歷史數據...")
        
        try:
            # 定義起始週（2025-10-01 是第 40 週）
            START_YEAR = 2025
            START_WEEK = 40
            
            # 獲取當前週數
            now = datetime.now(TZ_TW)
            current_year, current_week, _ = now.isocalendar()
            
            # 計算需要處理的週數
            computed_count = 0
            
            # 從起始週循環到當前週
            for year in range(START_YEAR, current_year + 1):
                start_week = START_WEEK if year == START_YEAR else 1
                end_week = current_week if year == current_year else 52
                
                for week in range(start_week, end_week + 1):
                    # 強制重新計算所有週次（覆蓋舊數據）
                    cog = self.get_cog("OCWCog")
                    if cog:
                        try:
                            s_time, e_time = get_week_range(year, week)
                            stats = await cog._fetch_data(None, s_time, e_time)
                            cog._calculate_scores(stats)
                            
                            # 儲存到資料庫
                            if weekly_reports_collection is not None:
                                report_data = {
                                    "year": year,
                                    "week": week,
                                    "range_str": f"{s_time.strftime('%Y-%m-%d')} ~ {e_time.strftime('%Y-%m-%d')}",
                                    "stats": [s.to_dict() for s in stats.values()]
                                }
                                await weekly_reports_collection.replace_one(
                                    {"year": year, "week": week},
                                    report_data,
                                    upsert=True
                                )
                                computed_count += 1
                                print(f"  ✓ 已計算 Week {week}/{year}")
                        except Exception as e:
                            print(f"  ✗ Week {week}/{year} 計算失敗: {e}")
                    else:
                        print("❌ 無法找到 OCWCog，自動計算中止")
                        return
            
            print(f"✅ 自動計算完成：已更新 {computed_count} 週")
                
        except Exception as e:
            print(f"❌ 自動計算失敗: {e}")


    async def _update_doc_highlight_mode(self, thread_id: int, filename: str, title: str):
        """模式 A (增強版): 使用 Embed 標示最新版 (綠色) 與歷史版 (灰色)"""
        try:
            channel = self.get_channel(thread_id)
            if not channel or not isinstance(channel, discord.Thread):
                try:
                    channel = await self.fetch_channel(thread_id)
                except:
                    print(f"❌ 無法獲取 {title} 貼文 (ID: {thread_id})")
                    return

            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            # 檢查最後一則訊息
            last_msg = None
            async for message in channel.history(limit=1):
                last_msg = message
                break

            # 判斷是否需要更新
            # 這裡我們比較 Embed 的 description (如果有的話) 或是 content
            current_content_in_discord = ""
            if last_msg:
                if last_msg.embeds:
                    current_content_in_discord = last_msg.embeds[0].description
                else:
                    current_content_in_discord = last_msg.content

            # 正規化比較 (移除前後空白與 \r)
            if current_content_in_discord.strip().replace("\r", "") == content.strip().replace("\r", ""):
                print(f"ℹ️ {title} 已是最新")
                return

            # 需要更新：
            # 1. 把上一則 (如果是最新版) 改成灰色 [History]
            if last_msg and last_msg.author.id == self.user.id:
                # 只有當它原本是 [Latest] 才需要改，但簡單起見我們都把它變灰
                try:
                    prev_content = last_msg.embeds[0].description if last_msg.embeds else last_msg.content
                    history_embed = discord.Embed(
                        title=f"📜 {title} [History]",
                        description=prev_content,
                        color=discord.Color.light_grey() # 灰色
                    )
                    await last_msg.edit(content=None, embed=history_embed)
                except Exception as e:
                    print(f"⚠️ 無法修改舊訊息: {e}")

            # 2. 發送新的一則 (綠色 [Latest])
            new_embed = discord.Embed(
                title=f"✨ {title} [Latest]",
                description=content,
                color=0x2ecc71 # 綠色
            )
            await channel.send(embed=new_embed)
            print(f"✅ {title} 已發布新版本 (Highlight)")

        except Exception as e:
            print(f"❌ 更新 {title} 失敗: {e}")

    async def _reply_deploy_guide_to_readme(self, thread_id: int, filename: str):
        """在 README thread 下方自動回覆 DEPLOY_GUIDE.md（以文件形式）"""
        try:
            channel = await self.fetch_channel(thread_id)
            
            # 檢查是否已經有 DEPLOY_GUIDE 的回覆
            deploy_marker = "📘 部署指南 (DEPLOY_GUIDE)"
            is_posted = False
            
            async for message in channel.history(limit=50):
                if deploy_marker in message.content and message.attachments:
                    is_posted = True
                    print("ℹ️ DEPLOY_GUIDE 已存在")
                    # 注意：Discord 不支持編輯帶附件的訊息，所以如果已存在就跳過
                    return
            
            # 如果不存在，發送新回覆（文件形式）
            file = discord.File(filename, filename=filename)
            await channel.send(
                content=f"{deploy_marker}\n\n點擊下方文件查看完整的部署步驟說明 👇",
                file=file
            )
            print("✅ DEPLOY_GUIDE 已發布為 README 回覆（文件形式）")

        except Exception as e:
            print(f"❌ 發布 DEPLOY_GUIDE 失敗: {e}")


    async def _update_doc_version_check(self, thread_id: int, filename: str, title: str):
        """模式 B (增強版): 檢查版本號 (第一行) 是否存在於歷史紀錄"""
        try:
            channel = await self.fetch_channel(thread_id)
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
                f.seek(0)
                first_line = f.readline().strip() # e.g., "# Release Note: v1.1.2 Online"

            # 提取版本號特徵 (簡單用第一行整行來比對)
            version_signature = first_line
            
            is_posted = False
            async for message in channel.history(limit=20):
                # 檢查 Content 或 Embed Title/Description
                msg_text = message.content
                if message.embeds:
                    msg_text += (message.embeds[0].title or "") + (message.embeds[0].description or "")
                
                if version_signature in msg_text:
                    is_posted = True
                    break
            
            if not is_posted:
                await channel.send(content)
                print(f"✅ {title} 已發布新版本: {version_signature}")
            else:
                print(f"ℹ️ {title} ({version_signature}) 已存在")

        except Exception as e:
            print(f"❌ 更新 {title} 失敗: {e}")

    async def _update_doc_changelog_smart(self, thread_id: int, filename: str):
        """模式 C: 智慧 Changelog - 補齊缺失的舊版本"""
        try:
            channel = await self.fetch_channel(thread_id)
            with open(filename, "r", encoding="utf-8") as f:
                full_content = f.read()

            import re
            parts = re.split(r'(^## \[.*\])', full_content, flags=re.MULTILINE)
            
            version_blocks = [] 
            start_idx = 1 if len(parts) > 1 and parts[1].startswith("## [") else 0
            
            for i in range(start_idx, len(parts), 2):
                if i+1 < len(parts):
                    header = parts[i].strip()
                    body = parts[i+1]
                    full_block = header + "\n" + body
                    ver_match = re.search(r'\[(.*?)\]', header)
                    ver_key = ver_match.group(1) if ver_match else header
                    version_blocks.append({"key": ver_key, "content": full_block.strip()})

            history_contents = []
            async for msg in channel.history(limit=50):
                history_contents.append(msg.content)
            
            posted_count = 0
            for block in reversed(version_blocks):
                is_posted = False
                for h_msg in history_contents:
                    if block['key'] in h_msg: 
                        is_posted = True
                        break
                
                if not is_posted:
                    await channel.send(block['content'])
                    print(f"✅ Changelog 補齊版本: {block['key']}")
                    posted_count += 1
                    import asyncio
                    await asyncio.sleep(1)
            
            if posted_count == 0:
                print("ℹ️ Changelog 已是最新")

        except Exception as e:
            print(f"❌ 更新 Changelog 失敗: {e}")

# ====== Run ======
if __name__ == "__main__":
    # 啟動 Web Server (Keep Alive)
    keep_alive()
    
    if not TOKEN:
        print("❌ 錯誤: 找不到 TOKEN，請檢查 .env 檔案或環境變數")
    else:
        bot = MyBot()
        bot.run(TOKEN)
