from dataclasses import dataclass, field


@dataclass
class Question:
    """英语题目数据模型"""
    id: int
    sentence: str            # 含空白的句子，如 "She ____ TV yesterday."
    answer: str              # 正确答案，如 "watched"
    type: str                # 题型：grammar / vocabulary / spelling / collocation
    category: str            # 语法分类：past_tense / present_continuous ...
    hint: str                # 语法提示 / 解释
    difficulty: int = 1      # 难度 1-5
    distractors: list[str] | None = field(default=None)
    error_patterns: list[str] | None = field(default=None)
    # distractors: 自定义干扰字母，None 则由 LetterManager 自动生成
    # error_patterns: 常见错误答案，用于生成有意义的干扰和反馈

    def answer_letters(self) -> list[str]:
        """返回答案的字母列表，如 "watched" → ['w','a','t','c','h','e','d']"""
        return list(self.answer)

    def display_text(self) -> str:
        """带高亮标记的显示文本（供 UI 使用）"""
        return self.sentence.replace("____", "______")
