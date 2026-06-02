import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, HUD_HEIGHT, FEEDBACK_BAR_HEIGHT

# 特效颜色
FLASH_CORRECT = (50, 200, 50)    # 正确：绿色
FLASH_WRONG = (200, 50, 50)      # 错误：红色
FLASH_COMPLETE = (255, 215, 0)   # 完成：金色


class ScreenEffects:
    """屏幕特效：闪光、震动"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        # 闪光层
        self._flash_color = None
        self._flash_alpha = 0
        self._flash_max_alpha = 80
        self._flash_decay = 3  # 每帧衰减

    def flash(self, color: tuple, max_alpha: int = 80, decay: int = 3):
        """触发闪光"""
        self._flash_color = color
        self._flash_alpha = max_alpha
        self._flash_max_alpha = max_alpha
        self._flash_decay = decay

    def tick(self):
        """每帧衰减"""
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, self._flash_alpha - self._flash_decay)

    @property
    def active(self) -> bool:
        return self._flash_alpha > 0

    def draw(self):
        """绘制闪光覆盖层"""
        if not self.active or self._flash_color is None:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*self._flash_color, self._flash_alpha))
        # 只在游戏区域显示（HUD 区域以下）
        game_top = HUD_HEIGHT + FEEDBACK_BAR_HEIGHT
        game_rect = pygame.Rect(0, game_top, WINDOW_WIDTH, WINDOW_HEIGHT - game_top)
        self.screen.blit(overlay, (0, 0), game_rect)
