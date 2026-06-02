import random
from game.letter import Letter


# 全字母表，用于生成干扰字母
ALL_LETTERS = [chr(ord('a') + i) for i in range(26)]


class LetterManager:
    """字母生成与管理"""

    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.letters: list[Letter] = []
        self._next_order = 0  # 玩家接下来该吃第几个正确字母

    def spawn(self, answer: str, distractors: list[str] | None = None,
              occupied: set[tuple[int, int]] | None = None):
        """
        在地图上生成字母。

        参数：
            answer: 正确答案字符串，如 "watched"
            distractors: 干扰字母列表，None 则自动生成
            occupied: 已被占据的位置（蛇身等）
        """
        self.letters.clear()
        self._next_order = 0
        occupied_set = set(occupied) if occupied else set()

        # 1. 按顺序放置正确答案字母
        for order, char in enumerate(answer):
            pos = self._random_free_pos(occupied_set)
            if pos is None:
                continue  # 棋盘满了，跳过（正常情况下不会发生）
            col, row = pos
            self.letters.append(Letter(char, col, row, is_correct=True, order=order))
            occupied_set.add(pos)

        # 2. 生成干扰字母
        if distractors is None:
            distractors = self._auto_distractors(answer)

        for char in distractors:
            pos = self._random_free_pos(occupied_set)
            if pos is None:
                break
            col, row = pos
            self.letters.append(Letter(char, col, row, is_correct=False))
            occupied_set.add(pos)

    def get_letter_at(self, col: int, row: int) -> Letter | None:
        """获取某格上的字母（未被吃掉的）"""
        for letter in self.letters:
            if not letter.eaten and letter.col == col and letter.row == row:
                return letter
        return None

    def eat_letter(self, letter: Letter) -> dict:
        """
        吃掉一个字母。返回结果：
        {
            "correct": bool,    # 是否正确
            "in_order": bool,   # 顺序是否正确
            "combo_ok": bool,   # 是否应该继续连击
        }
        """
        letter.eaten = True

        if not letter.is_correct:
            return {"correct": False, "in_order": False, "combo_ok": False}

        # 检查顺序
        if letter.order == self._next_order:
            self._next_order += 1
            return {"correct": True, "in_order": True, "combo_ok": True}
        else:
            return {"correct": True, "in_order": False, "combo_ok": False}

    def is_word_complete(self) -> bool:
        """答案单词是否已被完整拼出"""
        return self._next_order > 0 and all(
            l.eaten for l in self.letters if l.is_correct
        )

    def remain_correct_count(self) -> int:
        """剩余未吃的正确字母数"""
        return sum(1 for l in self.letters if l.is_correct and not l.eaten)

    def current_needed_char(self, answer: str) -> str:
        """当前需要吃的字母"""
        if self._next_order < len(answer):
            return answer[self._next_order]
        return ""

    # ---- 内部辅助 ----

    def _random_free_pos(self, occupied: set) -> tuple[int, int] | None:
        """在未被占据的位置中随机找一个"""
        candidates = []
        for c in range(self.cols):
            for r in range(self.rows):
                if (c, r) not in occupied:
                    candidates.append((c, r))

        if not candidates:
            return None
        return random.choice(candidates)

    @staticmethod
    def _auto_distractors(answer: str, count: int = 8) -> list[str]:
        """自动从字母表中选择干扰字母（排除答案中的字母）"""
        answer_set = set(answer.lower())
        pool = [ch for ch in ALL_LETTERS if ch not in answer_set]
        return random.sample(pool, min(count, len(pool)))
