import pygame
from config import (
    COLS, ROWS, GRID_SIZE, GRID_Y_OFFSET, BG_COLOR, GREEN, DARK_GREEN, WHITE, BLACK,
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

    def draw_grid(self):
        """绘制纯色游戏背景（无网格线）"""
        game_rect = pygame.Rect(0, GRID_Y_OFFSET, 800, 600 - GRID_Y_OFFSET)
        self.screen.fill(BG_COLOR, game_rect)

    def draw_snake(self, snake):
        """绘制蛇"""
        for i, (col, row) in enumerate(snake.body):
            color = GREEN if i == 0 else DARK_GREEN
            rect = pygame.Rect(
                col * GRID_SIZE + 1,
                self._gy(row) + 1,
                GRID_SIZE - 2,
                GRID_SIZE - 2,
            )
            pygame.draw.rect(self.screen, color, rect)

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
