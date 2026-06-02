import pygame
from config import (
    WINDOW_WIDTH, HUD_HEIGHT, HUD_PADDING, HUD_BG_COLOR,
    FEEDBACK_BAR_HEIGHT, WHITE,
)

# ── 调色板 ──
COLOR_SENTENCE = (220, 230, 255)       # 句子
COLOR_CATEGORY = (150, 190, 240)       # 分类标签
COLOR_SCORE = (200, 220, 255)          # 分数
COLOR_COMBO = (255, 220, 80)           # 连击
COLOR_TITLE = (255, 215, 0)            # 称号
COLOR_TIME_GREEN = (80, 200, 80)
COLOR_TIME_YELLOW = (220, 200, 50)
COLOR_TIME_RED = (220, 60, 60)

COLOR_PROGRESS_EATEN = (80, 200, 80)   # 已吃字母
COLOR_PROGRESS_ACTIVE = (255, 210, 60) # 当前字母
COLOR_PROGRESS_PENDING = (70, 70, 70)  # 未轮到
COLOR_PROGRESS_BG = (35, 35, 45)       # 方块背景

COLOR_FEEDBACK_CORRECT = (100, 255, 120)
COLOR_FEEDBACK_WRONG = (255, 100, 100)
COLOR_FEEDBACK_COMPLETE = (255, 215, 0)
COLOR_FEEDBACK_INFO = (180, 200, 230)

# ── 字体（懒加载） ──
FONT = {}


def _get_font(name, size, bold=False):
    key = f"{name}_{size}_{bold}"
    if key not in FONT:
        FONT[key] = pygame.font.SysFont(name, size, bold)
    return FONT[key]


# ============================================================


class HUD:
    """HUD — 清晰的三行布局，适合英语学习界面"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        # HUD 表面（半透明）
        self.surf = pygame.Surface((WINDOW_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)
        # 反馈条表面（单独，绘在游戏区顶部）
        self.fb_surf = pygame.Surface((WINDOW_WIDTH, FEEDBACK_BAR_HEIGHT), pygame.SRCALPHA)
        # 动画偏移量（预留扩展用）
        self.feedback_offset = 0
        self.feedback_alpha = 255

    # ── 主入口 ──

    def draw(self, question, letter_manager, score_mgr, timer,
             feedback_text, feedback_type):
        """每帧调用：绘制完整 HUD + 反馈条"""
        self._draw_hud(question, letter_manager, score_mgr, timer)
        self._draw_feedback_bar(feedback_text, feedback_type)
        self._blit()

    # ── HUD 主体 ──

    def _draw_hud(self, question, letter_manager, score_mgr, timer):
        """HUD 主体：背景 + 三行信息"""
        self.surf.fill(HUD_BG_COLOR)

        y = HUD_PADDING

        # ---- 第 1 行：句子 ----
        font_s = _get_font("arial", 24, True)
        display = question.sentence.replace("____", " ______ ")
        text_surf = font_s.render(display, True, COLOR_SENTENCE)
        self.surf.blit(text_surf, (HUD_PADDING, y))

        # 右上：分数 + 连击
        self._draw_status_top_right(score_mgr, timer, y)

        y += 30

        # ---- 第 2 行：分类标签 ----
        font_m = _get_font("arial", 16)
        tag = font_m.render(f"{question.category}", True, COLOR_CATEGORY)
        self.surf.blit(tag, (HUD_PADDING, y))

        y += 24

        # ---- 第 3 行：拼写进度 ----
        self._draw_progress(question.answer, letter_manager, y)

    # ── 右上状态栏 ──

    def _draw_status_top_right(self, score_mgr, timer, y_top):
        """右上角：分数 / 连击 / 倒计时"""
        font = _get_font("arial", 18, True)
        font_sm = _get_font("arial", 15)
        right_x = WINDOW_WIDTH - HUD_PADDING
        line_h = 20

        # 分数
        score_surf = font.render(str(score_mgr.score), True, COLOR_SCORE)
        score_label = font_sm.render("SCORE", True, (140, 160, 190))
        r1 = score_label.get_rect(topright=(right_x, y_top))
        r2 = score_surf.get_rect(topright=(right_x, y_top + 16))
        self.surf.blit(score_label, r1)
        self.surf.blit(score_surf, r2)

        # 连击 + 倍率
        combo_text = score_mgr.combo_display()
        if combo_text:
            mult_text = score_mgr.multiplier_display()
            display = f"{combo_text}"
            if mult_text:
                display += f"  {mult_text}"
            combo_surf = font.render(display, True, COLOR_COMBO)
            combo_label = font_sm.render("COMBO", True, (140, 120, 60))
            r3 = combo_label.get_rect(topright=(right_x, y_top + 40))
            r4 = combo_surf.get_rect(topright=(right_x, y_top + 56))
            self.surf.blit(combo_label, r3)
            self.surf.blit(combo_surf, r4)

        # 倒计时（进度条 + 数字）
        bar_w = 120
        bar_h = 12
        bar_x = right_x - bar_w
        bar_y = y_top + 82

        # 标签
        time_label = font_sm.render("TIME", True, (140, 160, 190))
        self.surf.blit(time_label, (bar_x, bar_y - 16))

        # 背景
        pygame.draw.rect(self.surf, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)

        # 填充
        ratio = timer.remaining_ratio
        if ratio > 0.5:
            bar_color = COLOR_TIME_GREEN
        elif ratio > 0.25:
            bar_color = COLOR_TIME_YELLOW
        else:
            bar_color = COLOR_TIME_RED
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.surf, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        # 秒数
        sec_surf = _get_font("arial", 16, True).render(
            f"{timer.seconds_left}s", True, WHITE)
        sec_rect = sec_surf.get_rect(midleft=(bar_x + bar_w + 8, bar_y + bar_h // 2))
        self.surf.blit(sec_surf, sec_rect)

    # ── 拼写进度 ──

    def _draw_progress(self, answer, letter_manager, y):
        """绘制单词拼写进度方块"""
        letters = list(answer)
        next_order = letter_manager._next_order
        box_size = 28
        gap = 5

        start_x = HUD_PADDING

        for i, ch in enumerate(letters):
            x = start_x + i * (box_size + gap)

            if i < next_order:
                # 已吃 → 绿色实心
                bg = COLOR_PROGRESS_EATEN
                border = None
                fg = WHITE
            elif i == next_order:
                # 当前 → 亮色边框 + 暗背景
                bg = COLOR_PROGRESS_BG
                border = COLOR_PROGRESS_ACTIVE
                fg = COLOR_PROGRESS_ACTIVE
            else:
                bg = COLOR_PROGRESS_BG
                border = (55, 55, 65)
                fg = (100, 100, 110)

            rect = pygame.Rect(x, y, box_size, box_size)
            pygame.draw.rect(self.surf, bg, rect)
            if border:
                pygame.draw.rect(self.surf, border, rect, 2)

            char_surf = _get_font("arial", 20, True).render(ch.upper(), True, fg)
            cr = char_surf.get_rect(center=rect.center)
            self.surf.blit(char_surf, cr)

    # ── 反馈条（游戏区顶部） ──

    def _draw_feedback_bar(self, text: str, ftype: str):
        """绘制反馈条（位于 HUD 和游戏区之间）"""
        self.fb_surf.fill(HUD_BG_COLOR)

        if not text:
            self.feedback_offset = 0
            self.feedback_alpha = 255
            return

        # 类型颜色
        if ftype == "correct":
            color = COLOR_FEEDBACK_CORRECT
        elif ftype == "wrong":
            color = COLOR_FEEDBACK_WRONG
        elif ftype == "complete":
            color = COLOR_FEEDBACK_COMPLETE
        else:
            color = COLOR_FEEDBACK_INFO

        # 文字 — 左对齐，显示提示性内容
        font = _get_font("arial", 18, True)
        surf = font.render(text, True, color)

        # 水平滚动效果（预留：可加 offset）
        x = HUD_PADDING + self.feedback_offset
        y = (FEEDBACK_BAR_HEIGHT - surf.get_height()) // 2

        # 应用 alpha
        surf.set_alpha(max(0, min(255, self.feedback_alpha)))
        self.fb_surf.blit(surf, (x, y))

    # ── 合成输出 ──

    def _blit(self):
        self.screen.blit(self.surf, (0, 0))
        self.screen.blit(self.fb_surf, (0, HUD_HEIGHT))
