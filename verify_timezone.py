from datetime import datetime, timezone, timedelta

# Define Taiwan Timezone
TZ_TW = timezone(timedelta(hours=8))

# Simulate a UTC time from Discord (e.g., 10:00 UTC)
# In reality, Discord returns aware UTC datetimes, but let's simulate what happens
utc_now = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)

print(f"Original UTC Time: {utc_now}")

# 1. The BUGGY way: replace
# This just changes the timezone info WITHOUT adjusting the time.
# So 10:00 UTC becomes 10:00 TW time (which is 02:00 UTC).
# This is WRONG because it changes the absolute point in time.
buggy_time = utc_now.replace(tzinfo=TZ_TW)
print(f"Buggy Time (replace): {buggy_time} (This is 10:00 TW time)")
print(f"Buggy Time as UTC: {buggy_time.astimezone(timezone.utc)}")

# 2. The CORRECT way: astimezone
# This converts the time to the new timezone.
# 10:00 UTC becomes 18:00 TW time.
# This preserves the absolute point in time.
correct_time = utc_now.astimezone(TZ_TW)
print(f"Correct Time (astimezone): {correct_time} (This is 18:00 TW time)")
print(f"Correct Time as UTC: {correct_time.astimezone(timezone.utc)}")

# Verification
assert buggy_time != correct_time
print("\nVerification: The two methods produce DIFFERENT results.")
