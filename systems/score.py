from config import (
    SCORE_PER_LETTER, SCORE_PENALTY, WORD_BONUS, COMBO_BONUS,
    COMBO_MULTIPLIER_STEP, COMBO_MULTIPLIER_INC, TITLES,
    TIME_BONUS_PER_SECOND, MILESTONE_WORDS, MILESTONE_BONUS,
    COMBO_SHOUT_LEVELS, COMBO_SHOUTS,
)


class ScoreManager:
    """分数 + 连击 + 称号管理"""

    def __init__(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.multiplier = 1.0
        self.correct_count = 0
        self.wrong_count = 0
        self.word_count = 0
        self._combo_just_broken = False
        self._last_shouted = 0  # 上次播报的连击门槛

    def on_correct_letter(self) -> dict:
        """吃对字母。返回 {earned, multiplier, combo_shout}"""
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self._combo_just_broken = False

        self.multiplier = 1.0 + (self.combo // COMBO_MULTIPLIER_STEP) * COMBO_MULTIPLIER_INC

        earned = int(SCORE_PER_LETTER * self.multiplier)
        self.score += earned
        self.correct_count += 1

        title = self._check_title()
        combo_shout = self._check_combo_shout()

        return {
            "earned": earned,
            "multiplier": self.multiplier,
            "title": title,
            "combo_shout": combo_shout,
        }

    def on_wrong_letter(self) -> dict:
        """吃错字母/顺序错误。返回 {penalty, combo_broken}"""
        penalty = min(self.score, SCORE_PENALTY)
        self.score -= penalty
        self.score = max(0, self.score)

        if self.combo > 0:
            self._combo_just_broken = True
        self.combo = 0
        self.multiplier = 1.0
        self.wrong_count += 1

        return {"penalty": penalty, "combo_broken": self._combo_just_broken}

    def on_word_complete(self, seconds_left: int = 0) -> dict:
        """完成单词奖励。返回 {bonus, time_bonus, milestone_bonus, title}"""
        # 基础完成奖励
        base_bonus = WORD_BONUS + int(COMBO_BONUS * self.multiplier)

        # 时间奖励
        time_bonus = seconds_left * TIME_BONUS_PER_SECOND

        # 里程碑奖励
        self.word_count += 1
        milestone_bonus = MILESTONE_BONUS if self.word_count % MILESTONE_WORDS == 0 else 0

        total_bonus = base_bonus + time_bonus + milestone_bonus
        self.score += total_bonus

        title = self._check_title()

        return {
            "base_bonus": base_bonus,
            "time_bonus": time_bonus,
            "milestone_bonus": milestone_bonus,
            "total_bonus": total_bonus,
            "title": title,
        }

    def on_time_up(self) -> dict:
        """超时惩罚。返回 {penalty}"""
        penalty = 30
        self.score = max(0, self.score - penalty)
        self.combo = 0
        self.multiplier = 1.0
        return {"penalty": penalty}

    # ── 显示 ──

    def combo_display(self) -> str:
        if self.combo >= 2:
            return f"{self.combo}x"
        return ""

    def multiplier_display(self) -> str:
        if self.multiplier > 1.0:
            return f"x{self.multiplier:.1f}"
        return ""

    # ── 内部 ──

    def _check_title(self) -> str:
        for threshold, title in reversed(TITLES):
            if self.word_count >= threshold:
                return title
        return ""

    def _check_combo_shout(self) -> str:
        """达到连击门槛时返回播报文字"""
        for level in reversed(COMBO_SHOUT_LEVELS):
            if self.combo >= level and self._last_shouted < level:
                self._last_shouted = level
                return COMBO_SHOUTS[level]
        return ""
