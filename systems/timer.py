from config import FPS, TIMER_BASE_SECONDS, TIMER_PENALTY_SECONDS, TIME_BONUS_PER_SECOND


class QuestionTimer:
    """每题倒计时"""

    def __init__(self):
        self.base_frames = TIMER_BASE_SECONDS * FPS
        self.remaining = self.base_frames
        self.penalty_frames = TIMER_PENALTY_SECONDS * FPS

    def reset(self):
        """重置计时器"""
        self.remaining = self.base_frames

    def tick(self):
        """每帧扣减（每秒扣 60 帧 = 1 秒）"""
        if self.remaining > 0:
            self.remaining -= 1

    def penalize(self):
        """吃错字母惩罚扣时"""
        self.remaining = max(0, self.remaining - self.penalty_frames)

    @property
    def expired(self) -> bool:
        return self.remaining <= 0

    @property
    def seconds_left(self) -> int:
        return max(0, self.remaining // FPS)

    @property
    def elapsed_ratio(self) -> float:
        """已用时间比例 0.0 ~ 1.0，用于 HUD 进度条"""
        used = self.base_frames - self.remaining
        return min(1.0, used / self.base_frames)

    @property
    def remaining_ratio(self) -> float:
        return self.remaining / self.base_frames

    def time_bonus(self) -> int:
        """剩余时间奖励分"""
        return self.seconds_left * TIME_BONUS_PER_SECOND
