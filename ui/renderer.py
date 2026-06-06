import math
import pygame
from config import (
    COLS, ROWS, GRID_SIZE, GRID_Y_OFFSET, BG_COLOR, GREEN, DARK_GREEN, WHITE, BLACK,
    SNAKE_HEAD_COLOR, SNAKE_TAIL_COLOR, SNAKE_EYE_WHITE, SNAKE_EYE_PUPIL,
    GRID_LINE_COLOR, SNAKE_BORDER_RADIUS, Direction,
)
from ui.hud import HUD

# 字母颜色
CORRECT_COLOR = (100, 200, 255)
DISTRACTOR_COLOR = (200, 200, 80)
FONT_SIZE = GRID_SIZE - 12


class Renderer:
    """游戏画面渲染器"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._font = pygame.font.SysFont("arial", FONT_SIZE, bold=True)
        self._hud = HUD(screen)

    def _gy(self, row: int) -> int:
        """网格行坐标 → 屏幕 y 坐标"""
        return GRID_Y_OFFSET + row * GRID_SIZE

    def _gcy(self, row: int) -> int:
        """网格行中心 → 屏幕 y 中心"""
        return GRID_Y_OFFSET + row * GRID_SIZE + GRID_SIZE // 2

    @staticmethod
    def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
        """线性插值两个颜色"""
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def _draw_eyes(self, col: int, row: int, direction: tuple):
        """在蛇头上绘制方向眼睛"""
        cx = col * GRID_SIZE + GRID_SIZE // 2
        cy = self._gcy(row)
        eye_r = 4      # 眼白半径
        pupil_r = 2     # 瞳孔半径
        offset = 5      # 眼睛中心偏移量
        spread = 6      # 两只眼睛间距

        dx, dy = direction
        if direction == Direction.RIGHT:
            left = (cx + offset, cy - spread)
            right = (cx + offset, cy + spread)
            pupil_off = (2, 0)
        elif direction == Direction.LEFT:
            left = (cx - offset, cy - spread)
            right = (cx - offset, cy + spread)
            pupil_off = (-2, 0)
        elif direction == Direction.UP:
            left = (cx - spread, cy - offset)
            right = (cx + spread, cy - offset)
            pupil_off = (0, -2)
        else:  # DOWN
            left = (cx - spread, cy + offset)
            right = (cx + spread, cy + offset)
            pupil_off = (0, 2)

        # 眼白
        pygame.draw.circle(self.screen, SNAKE_EYE_WHITE, left, eye_r)
        pygame.draw.circle(self.screen, SNAKE_EYE_WHITE, right, eye_r)
        # 瞳孔
        pygame.draw.circle(self.screen, SNAKE_EYE_PUPIL,
                           (left[0] + pupil_off[0], left[1] + pupil_off[1]), pupil_r)
        pygame.draw.circle(self.screen, SNAKE_EYE_PUPIL,
                           (right[0] + pupil_off[0], right[1] + pupil_off[1]), pupil_r)

    def draw_grid(self):
        """绘制游戏背景 + 淡灰色网格线"""
        game_rect = pygame.Rect(0, GRID_Y_OFFSET, 800, 600 - GRID_Y_OFFSET)
        self.screen.fill(BG_COLOR, game_rect)

        # 竖线
        for c in range(COLS + 1):
            x = c * GRID_SIZE
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (x, GRID_Y_OFFSET), (x, 600))
        # 横线
        for r in range(ROWS + 1):
            y = GRID_Y_OFFSET + r * GRID_SIZE
            pygame.draw.line(self.screen, GRID_LINE_COLOR,
                             (0, y), (800, y))

    def draw_snake(self, snake):
        """绘制蛇（渐变色 + 圆角 + 蛇头眼睛）"""
        body_len = len(snake.body)
        for i, (col, row) in enumerate(snake.body):
            # 渐变色：蛇头亮绿 → 蛇尾深绿
            t = i / max(body_len - 1, 1)
            color = self._lerp_color(SNAKE_HEAD_COLOR, SNAKE_TAIL_COLOR, t)

            rect = pygame.Rect(
                col * GRID_SIZE + 1,
                self._gy(row) + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=SNAKE_BORDER_RADIUS)

        # 蛇头眼睛
        if body_len > 0:
            head_col, head_row = snake.body[0]
            self._draw_eyes(head_col, head_row, snake.direction)

    def draw_letters(self, letter_manager):
        """绘制所有字母"""
        for letter in letter_manager.letters:
            if letter.eaten:
                continue
            color = CORRECT_COLOR if letter.is_correct else DISTRACTOR_COLOR
            self._draw_letter(letter.col, letter.row, letter.char, color)

    def _draw_letter(self, col: int, row: int, char: str, color: tuple):
        """在指定网格绘制一个字母"""
        cx = col * GRID_SIZE + GRID_SIZE // 2
        cy = self._gcy(row)

        pygame.draw.circle(self.screen, color, (cx, cy), GRID_SIZE // 2 - 4)
        text = self._font.render(char.upper(), True, BLACK)
        text_rect = text.get_rect(center=(cx, cy))
        self.screen.blit(text, text_rect)

    def draw_hud(self, question, letter_manager, score_mgr, timer,
                 feedback_text, feedback_type):
        """绘制 HUD 覆盖层"""
        self._hud.draw(question, letter_manager, score_mgr, timer,
                       feedback_text, feedback_type)

    # ── 开始菜单 ──

    def draw_menu(self):
        """绘制开始菜单"""
        self.screen.fill(BG_COLOR)

        # 标题
        title_font = pygame.font.SysFont("arial", 64, bold=True)
        title_surf = title_font.render("Grammar Snake", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(400, 220))
        self.screen.blit(title_surf, title_rect)

        # 蛇图标（简单装饰）
        icon_y = 300
        for i in range(5):
            x = 340 + i * 28
            color = GREEN if i == 0 else DARK_GREEN
            pygame.draw.rect(self.screen, color, (x, icon_y, 24, 24), border_radius=6)

        # 副标题（闪烁效果）
        tick = pygame.time.get_ticks()
        alpha = int(128 + 127 * math.sin(tick * 0.004))
        sub_font = pygame.font.SysFont("arial", 24)
        sub_surf = sub_font.render("Press any key to start", True, WHITE)
        sub_surf.set_alpha(alpha)
        sub_rect = sub_surf.get_rect(center=(400, 380))
        self.screen.blit(sub_surf, sub_rect)

        # 操作提示
        hint_font = pygame.font.SysFont("arial", 16)
        hints = [
            "Arrow Keys - Move",
            "P - Pause",
            "ESC - Quit",
        ]
        for i, hint in enumerate(hints):
            h_surf = hint_font.render(hint, True, (120, 120, 140))
            h_rect = h_surf.get_rect(center=(400, 440 + i * 24))
            self.screen.blit(h_surf, h_rect)

    # ── 暂停画面 ──

    def draw_pause_overlay(self):
        """在游戏画面上叠加暂停遮罩"""
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # PAUSED 文字
        font = pygame.font.SysFont("arial", 56, bold=True)
        surf = font.render("PAUSED", True, WHITE)
        rect = surf.get_rect(center=(400, 270))
        self.screen.blit(surf, rect)

        # 提示
        hint_font = pygame.font.SysFont("arial", 22)
        hint_surf = hint_font.render("Press P to resume", True, (180, 180, 200))
        hint_rect = hint_surf.get_rect(center=(400, 330))
        self.screen.blit(hint_surf, hint_rect)

    # ── Game Over 画面 ──

    def draw_game_over(self, score_mgr):
        """在游戏画面上叠加结算画面"""
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # GAME OVER
        title_font = pygame.font.SysFont("arial", 56, bold=True)
        title_surf = title_font.render("GAME OVER", True, (220, 60, 60))
        title_rect = title_surf.get_rect(center=(400, 180))
        self.screen.blit(title_surf, title_rect)

        # 统计信息
        stat_font = pygame.font.SysFont("arial", 26, bold=True)
        label_font = pygame.font.SysFont("arial", 18)

        stats = [
            ("SCORE", str(score_mgr.score), (255, 215, 0)),
            ("WORDS", str(score_mgr.word_count), (100, 255, 120)),
            ("MAX COMBO", f"{score_mgr.max_combo}x", (255, 220, 80)),
        ]

        y = 250
        for label, value, color in stats:
            label_surf = label_font.render(label, True, (140, 150, 170))
            val_surf = stat_font.render(value, True, color)
            label_rect = label_surf.get_rect(center=(400, y))
            val_rect = val_surf.get_rect(center=(400, y + 26))
            self.screen.blit(label_surf, label_rect)
            self.screen.blit(val_surf, val_rect)
            y += 65

        # 重启提示
        hint_font = pygame.font.SysFont("arial", 20)
        hint_surf = hint_font.render("Press R to restart / ESC to quit", True, (180, 180, 200))
        hint_rect = hint_surf.get_rect(center=(400, 480))
        self.screen.blit(hint_surf, hint_rect)
