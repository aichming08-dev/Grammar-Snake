"""学习追踪器：间隔重复 + 分类掌握度 + 持久化"""

import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class QuestionStat:
    """单题学习数据"""
    attempts: int = 0
    correct: int = 0
    wrong: int = 0
    streak: int = 0          # 当前连续答对次数
    interval: int = 1        # 复习间隔（题数）
    seen_count: int = 0      # 已出过的次数（用于间隔计数）


@dataclass
class CategoryStat:
    """分类学习数据"""
    attempts: int = 0
    correct: int = 0
    wrong: int = 0

    @property
    def mastery_pct(self) -> float:
        return self.correct / self.attempts if self.attempts > 0 else 0.0


class LearningTracker:
    """学习数据追踪、间隔重复、掌握度分析"""

    def __init__(self, save_path: str = None):
        self.question_stats: dict[int, QuestionStat] = {}
        self.category_stats: dict[str, CategoryStat] = {}
        self.total_seen: int = 0  # 全局已出题计数
        self.save_path = save_path
        if save_path and os.path.exists(save_path):
            self.load(save_path)

    def record_answer(self, q_id: int, category: str, correct: bool):
        """记录一次答题结果"""
        # 更新题目统计
        if q_id not in self.question_stats:
            self.question_stats[q_id] = QuestionStat()
        qs = self.question_stats[q_id]
        qs.attempts += 1
        if correct:
            qs.correct += 1
            qs.streak += 1
            # 间隔翻倍（连续答对越多，间隔越长）
            qs.interval = min(64, qs.interval * 2)
        else:
            qs.wrong += 1
            qs.streak = 0
            qs.interval = 1  # 答错立即重来

        # 更新分类统计
        if category not in self.category_stats:
            self.category_stats[category] = CategoryStat()
        cs = self.category_stats[category]
        cs.attempts += 1
        if correct:
            cs.correct += 1
        else:
            cs.wrong += 1

        self.total_seen += 1

    def get_due_questions(self, questions: list) -> list:
        """返回到期应复习的题目（按优先级排序）"""
        due = []
        for q in questions:
            qs = self.question_stats.get(q.id)
            if qs is None:
                # 从未见过的题，优先出
                due.append((0, q))
            elif self.total_seen - qs.seen_count >= qs.interval:
                # 已到期
                due.append((qs.interval, q))
        # 按 interval 升序（最急需复习的排前面）
        due.sort(key=lambda x: x[0])
        return [q for _, q in due]

    def mark_shown(self, q_id: int):
        """标记题目已出示"""
        if q_id in self.question_stats:
            self.question_stats[q_id].seen_count = self.total_seen

    def get_weakest_categories(self, top_n: int = 3) -> list[str]:
        """返回最弱的分类（正确率最低）"""
        scored = []
        for cat, cs in self.category_stats.items():
            if cs.attempts >= 2:  # 至少答过 2 题才有意义
                scored.append((cs.mastery_pct, cat))
        scored.sort()  # 正确率升序
        return [cat for _, cat in scored[:top_n]]

    def get_category_mastery(self) -> dict[str, float]:
        """返回所有分类的掌握度 {category: mastery_pct}"""
        return {cat: cs.mastery_pct for cat, cs in self.category_stats.items()}

    def get_overall_mastery(self) -> float:
        """返回整体正确率"""
        total_correct = sum(cs.correct for cs in self.category_stats.values())
        total_attempts = sum(cs.attempts for cs in self.category_stats.values())
        return total_correct / total_attempts if total_attempts > 0 else 0.0

    def get_streak_count(self) -> int:
        """返回当前最大连续答对数"""
        return max((qs.streak for qs in self.question_stats.values()), default=0)

    def save(self, path: str = None):
        """保存到 JSON"""
        save_path = path or self.save_path
        if not save_path:
            return
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        data = {
            "total_seen": self.total_seen,
            "question_stats": {
                str(k): asdict(v) for k, v in self.question_stats.items()
            },
            "category_stats": {
                k: asdict(v) for k, v in self.category_stats.items()
            },
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str = None):
        """从 JSON 加载"""
        load_path = path or self.save_path
        if not load_path or not os.path.exists(load_path):
            return
        with open(load_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.total_seen = data.get("total_seen", 0)
        self.question_stats = {
            int(k): QuestionStat(**v) for k, v in data.get("question_stats", {}).items()
        }
        self.category_stats = {
            k: CategoryStat(**v) for k, v in data.get("category_stats", {}).items()
        }
