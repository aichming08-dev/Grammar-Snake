from config import COLS, ROWS, Direction


class Snake:
    """贪吃蛇核心类"""

    def __init__(self):
        # 蛇身：列表 of (col, row)，下标 0 为蛇头
        self.body = [(COLS // 2, ROWS // 2)]
        self.direction = Direction.RIGHT
        self._next_direction = Direction.RIGHT
        self._growing = False

    def set_direction(self, direction):
        """防止反向移动"""
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }
        if direction != opposites.get(self.direction):
            self._next_direction = direction

    def move(self):
        """前进一格"""
        self.direction = self._next_direction
        head = self.body[0]
        dx, dy = self.direction
        new_head = (head[0] + dx, head[1] + dy)

        self.body.insert(0, new_head)

        if not self._growing:
            self.body.pop()
        else:
            self._growing = False

    def grow(self):
        """下次 move 时尾部不缩短"""
        self._growing = True

    def shrink(self):
        """蛇身缩短（惩罚）"""
        if len(self.body) > 1:
            self.body.pop()

    @property
    def head(self):
        return self.body[0]

    def hits_boundary(self, cols=COLS, rows=ROWS):
        """是否撞墙"""
        c, r = self.head
        return c < 0 or c >= cols or r < 0 or r >= rows

    def hits_self(self):
        """是否撞到自己"""
        return self.head in self.body[1:]

    def occupies(self, col, row):
        """检测某个格子是否被蛇占据"""
        return (col, row) in self.body
