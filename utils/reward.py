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


rewards = {
    1: 0.01,
    2: 0.02,
    3: 0.03,
    4: 0.03,
    5: 0.04,
    6: 0.04,
    7: 0.05,
}


def get_plus_every_second_for_day(day: int):
    if day not in rewards:
        day = 1
    next_day = 1 if day == 7 else day + 1
    return rewards[day], rewards[next_day]


def get_rewards():
    return rewards