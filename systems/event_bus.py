"""事件总线 — 解耦核心，所有系统通过事件通信"""


class EventBus:
    """全局事件总线"""

    def __init__(self):
        self._listeners: dict[str, list[tuple]] = {}

    def on(self, event: str, handler, priority: int = 0):
        """订阅事件 (priority 越高越先执行)"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append((handler, priority))
        self._listeners[event].sort(key=lambda x: -x[1])

    def off(self, event: str, handler):
        """取消订阅"""
        if event in self._listeners:
            self._listeners[event] = [
                (h, p) for h, p in self._listeners[event] if h != handler
            ]

    def emit(self, event: str, data: dict = None):
        """发布事件，所有订阅者按优先级执行"""
        if event in self._listeners:
            for handler, _ in self._listeners[event]:
                handler(data or {})


# ── 预定义事件名 ──

# 游戏生命周期
GAME_START = "game:start"
GAME_OVER = "game:over"

# 蛇
SNAKE_MOVE = "snake:move"

# 字母
LETTER_EATEN = "letter:eaten"
LETTER_CORRECT = "letter:correct"
LETTER_WRONG = "letter:wrong"
WORD_COMPLETE = "word:complete"

# 连击
COMBO_UPDATE = "combo:update"
COMBO_MILESTONE = "combo:milestone"
COMBO_BREAK = "combo:break"

# 计时
TIME_TICK = "time:tick"
TIME_UP = "time:up"

# 反馈
FEEDBACK_SHOW = "feedback:show"
