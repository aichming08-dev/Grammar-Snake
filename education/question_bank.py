import json
import random
from education.question import Question


class QuestionBank:
    """题库管理器：加载、随机出题、间隔重复、自适应难度"""

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

    def get_next(self, tracker=None) -> Question:
        """获取下一题（优先出到期复习题）"""
        if not self.questions:
            raise RuntimeError("题库为空，请先加载题目")

        if tracker:
            due = tracker.get_due_questions(self.questions)
            if due:
                q = due[0]
                tracker.mark_shown(q.id)
                return q

        # 无 tracker 或无到期题，随机出
        if self._index >= len(self.questions):
            self._index = 0
            random.shuffle(self.questions)
        q = self.questions[self._index]
        self._index += 1
        if tracker:
            tracker.mark_shown(q.id)
        return q

    def get_next_adaptive(self, tracker) -> Question:
        """根据掌握度自适应出题"""
        if not self.questions:
            raise RuntimeError("题库为空，请先加载题目")

        # 优先出弱分类的题
        weak_cats = tracker.get_weakest_categories(top_n=3)
        if weak_cats:
            weak_questions = [q for q in self.questions if q.category in weak_cats]
            if weak_questions:
                due = tracker.get_due_questions(weak_questions)
                if due:
                    q = due[0]
                    tracker.mark_shown(q.id)
                    return q

        # 回退到普通间隔重复
        return self.get_next(tracker)

    def get_practice(self, category: str, tracker=None) -> Question:
        """按分类出题（练习模式）"""
        filtered = [q for q in self.questions if q.category == category]
        if not filtered:
            raise RuntimeError(f"分类 '{category}' 无题目")
        if tracker:
            due = tracker.get_due_questions(filtered)
            if due:
                q = due[0]
                tracker.mark_shown(q.id)
                return q
        q = random.choice(filtered)
        if tracker:
            tracker.mark_shown(q.id)
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
