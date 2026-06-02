# 窗口
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 32
COLS = WINDOW_WIDTH // GRID_SIZE
FPS = 60
TITLE = "Grammar Snake"

# HUD + 游戏区分离
HUD_HEIGHT = 120
FEEDBACK_BAR_HEIGHT = 36
GRID_Y_OFFSET = HUD_HEIGHT + FEEDBACK_BAR_HEIGHT
ROWS = (WINDOW_HEIGHT - GRID_Y_OFFSET) // GRID_SIZE  # (600-156)//40 = 11

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
BG_COLOR = (30, 30, 30)

# 方向
class Direction:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# 游戏状态
class GameState:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    QUESTION_DONE = "question_done"
    GAME_OVER = "game_over"

# 评分配置
SCORE_PER_LETTER = 10
SCORE_PENALTY = 5
WORD_BONUS = 50
COMBO_BONUS = 30

# 连击倍率
COMBO_MULTIPLIER_STEP = 5
COMBO_MULTIPLIER_INC = 0.5

# 称号门槛
TITLES = [
    (0, "Beginner"),
    (3, "Word Learner"),
    (7, "Spelling Bee"),
    (15, "Grammar Master"),
]

# HUD
HUD_PADDING = 14
HUD_BG_COLOR = (15, 15, 30)

# 反馈显示时长（帧数）
FEEDBACK_DURATION = 90
QUESTION_DONE_DURATION = 90

# 计时器
TIMER_BASE_SECONDS = 60
TIMER_PENALTY_SECONDS = 5
TIME_BONUS_PER_SECOND = 2

# 里程碑
MILESTONE_WORDS = 5
MILESTONE_BONUS = 100

# 连击播报门槛
COMBO_SHOUT_LEVELS = [5, 10, 15, 20]
COMBO_SHOUTS = {
    5: "Nice!",
    10: "Great!",
    15: "Amazing!",
    20: "Perfect!",
}
