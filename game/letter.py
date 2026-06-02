class Letter:
    """单个字母食物"""

    def __init__(self, char: str, col: int, row: int,
                 is_correct: bool = False, order: int = -1):
        self.char = char          # 字母字符，如 'w'
        self.col = col            # 网格列
        self.row = row            # 网格行
        self.is_correct = is_correct  # 是否属于正确答案
        self.order = order        # 在答案中的顺序（0-based），干扰字母为 -1
        self.eaten = False        # 是否已被吃掉
