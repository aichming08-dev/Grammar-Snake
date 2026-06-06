"""成就系统：解锁条件 + 持久化"""

import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    unlocked: bool = False


# 成就定义
ACHIEVEMENT_DEFS = [
    Achievement("first_word", "初次拼写", "完成第一个单词"),
    Achievement("streak_5", "小试牛刀", "连续答对5题"),
    Achievement("streak_10", "连续答对10题", "连续答对10题"),
    Achievement("streak_20", "语法达人", "连续答对20题"),
    Achievement("perfect_snake", "完美主义者", "蛇阶段不吃任何干扰字母通关"),
    Achievement("speed_demon", "闪电手", "蛇阶段10秒内通关"),
    Achievement("word_10", "初学者", "累计完成10个单词"),
    Achievement("word_50", "进阶学习者", "累计完成50个单词"),
    Achievement("word_100", "语法大师", "累计完成100个单词"),
    Achievement("category_master", "分类专家", "某个语法分类正确率达到90%"),
    Achievement("all_categories", "全面发展", "所有语法分类都有答题记录"),
]


class AchievementManager:
    """成就管理器"""

    def __init__(self, save_path: str = None):
        self.achievements: dict[str, Achievement] = {
            a.id: Achievement(a.id, a.name, a.description, False)
            for a in ACHIEVEMENT_DEFS
        }
        self.save_path = save_path
        self._newly_unlocked: list[Achievement] = []
        if save_path and os.path.exists(save_path):
            self.load(save_path)

    def check_and_unlock(self, condition_id: str, condition: bool) -> Achievement | None:
        """检查条件，满足则解锁成就"""
        if condition_id in self.achievements and condition:
            ach = self.achievements[condition_id]
            if not ach.unlocked:
                ach.unlocked = True
                self._newly_unlocked.append(ach)
                return ach
        return None

    def get_newly_unlocked(self) -> list[Achievement]:
        """获取并清空新解锁的成就"""
        result = list(self._newly_unlocked)
        self._newly_unlocked.clear()
        return result

    def get_unlocked_count(self) -> int:
        return sum(1 for a in self.achievements.values() if a.unlocked)

    def get_total_count(self) -> int:
        return len(self.achievements)

    def get_all(self) -> list[Achievement]:
        return list(self.achievements.values())

    def save(self, path: str = None):
        save_path = path or self.save_path
        if not save_path:
            return
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        data = {k: asdict(v) for k, v in self.achievements.items()}
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str = None):
        load_path = path or self.save_path
        if not load_path or not os.path.exists(load_path):
            return
        with open(load_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if k in self.achievements:
                self.achievements[k].unlocked = v.get("unlocked", False)
