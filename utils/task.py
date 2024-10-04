


rewards = {
    2: 1500,
    3: 2000,
    5: 3000,
    7: 3500,
    10: 5000,
    15: 7500,
    20: 10000
}



def get_reward_for_reffers(count: int):

    reward = rewards.get(count)
    return reward


def get_rewards():
    return rewards