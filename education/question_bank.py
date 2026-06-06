import json
import random
from education.question import Question


class QuestionBank:
    """题库管理器：加载、随机出题、筛选"""

    def __init__(self, json_path: str = None):
        self.questions: list[Question] = []
        self._index = 0
        self._file_path = json_path
        if json_path:
            self.load(json_path)

    def load(self, json_path: str):
        """从 JSON 文件加载题库"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_list = data.get("questions", [])
        self.questions = [Question(**q) for q in raw_list]
        random.shuffle(self.questions)
        self._index = 0

    def get_next(self) -> Question:
        """获取下一题（循环取题，题库耗尽后自动重洗牌）"""
        if not self.questions:
            raise RuntimeError("题库为空，请先加载题目")

        if self._index >= len(self.questions):
            self._index = 0
            random.shuffle(self.questions)

        q = self.questions[self._index]
        self._index += 1
        return q

    def peek(self) -> Question:
        """预览下一题（不移动指针）"""
        if not self.questions:
            raise RuntimeError("题库为空")
        idx = self._index if self._index < len(self.questions) else 0
        return self.questions[idx]

    def filter_by_difficulty(self, level: int) -> list[Question]:
        """按难度筛选"""
        return [q for q in self.questions if q.difficulty == level]

    def filter_by_category(self, category: str) -> list[Question]:
        """按语法分类筛选"""
        return [q for q in self.questions if q.category == category]

    def total(self) -> int:
        return len(self.questions)

    def remaining(self) -> int:
        return max(0, len(self.questions) - self._index)
