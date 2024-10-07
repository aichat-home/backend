from datetime import datetime, timedelta


def already_claimed_today(last_claimed: datetime) -> bool:
    if not last_claimed:
        return True
    now = datetime.now()
    
    return last_claimed.day == now.day


def calculate_reward(streak: int) -> int:
    if streak <= 5:
        return 50
    return 350


def check_streak(last_claimed: datetime) -> bool:
    if not last_claimed:
        return False
    now = datetime.now()
    return now.day - last_claimed.day != 1
