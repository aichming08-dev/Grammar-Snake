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

# 蛇身渐变色
SNAKE_HEAD_COLOR = (80, 255, 80)      # 蛇头亮绿
SNAKE_TAIL_COLOR = (20, 100, 20)      # 蛇尾深绿
SNAKE_EYE_WHITE = (255, 255, 255)
SNAKE_EYE_PUPIL = (0, 0, 0)

# 网格线
GRID_LINE_COLOR = (40, 40, 40)

# 圆角
SNAKE_BORDER_RADIUS = 6

# 方向
class Direction:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# 游戏状态
class GameState:
    MENU = "menu"
    QUESTION = "question"      # 输入答案阶段
    PLAYING = "playing"        # 蛇吃字母阶段
    PAUSED = "paused"
    QUESTION_DONE = "question_done"
    DYING = "dying"
    GAME_OVER = "game_over"

# 死亡动画
DEATH_ANIM_SPEED = 3        # 每 N 帧擦除一节蛇身

# 评分配置
SCORE_PER_LETTER = 10
SCORE_PENALTY = 5
WORD_BONUS = 50
COMBO_BONUS = 30

# 连击倍率
COMBO_MULTIPLIER_STEP = 5
COMBO_MULTIPLIER_INC = 0.5

# 学习引擎
LEARNING_DATA_PATH = "data/learning.json"
ADAPTIVE_HIGH_THRESHOLD = 0.8   # 正确率 >80% 升难度
ADAPTIVE_LOW_THRESHOLD = 0.5    # 正确率 <50% 降难度

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

# 移动速度（帧/步，越小越快）
MOVE_INTERVAL_BASE = 10      # 初始速度 = 6 步/秒
MOVE_INTERVAL_MIN = 6        # 最快速度 = 10 步/秒
SPEED_UP_PER_WORD = 1        # 每完成1个单词，间隔减1

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
