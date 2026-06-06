import os
import pygame
from config import (
    TITLE, FPS, COLS, ROWS, Direction, GameState,
    FEEDBACK_DURATION, QUESTION_DONE_DURATION, TIMER_PENALTY_SECONDS,
    MOVE_INTERVAL_BASE, MOVE_INTERVAL_MIN, SPEED_UP_PER_WORD,
    DEATH_ANIM_SPEED,
)
from game.snake import Snake
from game.letter_manager import LetterManager
from education.question_bank import QuestionBank
from systems.score import ScoreManager
from systems.timer import QuestionTimer
from systems.event_bus import EventBus, SNAKE_MOVE, LETTER_CORRECT, LETTER_WRONG, WORD_COMPLETE, GAME_OVER, TIME_UP
from ui.renderer import Renderer
from ui.effects import ScreenEffects, FLASH_CORRECT, FLASH_WRONG, FLASH_COMPLETE
from systems.sounds import SoundManager


class GameDirector:
    """游戏主循环 + 状态机"""

    def __init__(self, question_path: str = None):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.renderer = Renderer(self.screen)
        self.effects = ScreenEffects(self.screen)

        # 游戏对象
        self.snake = Snake()
        self.letter_manager = LetterManager(COLS, ROWS)
        self.score_mgr = ScoreManager()
        self.timer = QuestionTimer()
        self._move_counter = 0
        self._move_interval = MOVE_INTERVAL_BASE

        # 题库
        if question_path is None:
            question_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "questions.json"
            )
        self.question_bank = QuestionBank(question_path)
        self.current_question = None

        # 反馈系统
        self.feedback_text = ""
        self.feedback_type = ""
        self.feedback_timer = 0

        # 答案输入阶段
        self._input_text = ""
        self._q_feedback_text = ""
        self._q_feedback_type = ""

        # 连击播报（短暂显示在屏幕上）
        self.shout_text = ""
        self.shout_timer = 0

        # 状态计时器
        self._state_timer = 0

        # 事件总线
        self.events = EventBus()

        # 音效
        self.sounds = SoundManager()

        # 死亡动画
        self._death_timer = 0

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)
        pygame.quit()

    # ── 事件处理 ──

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type != pygame.KEYDOWN:
                continue

            # ── MENU：任意键开始 ──
            if self.state == GameState.MENU:
                self._start_game()
                return

            # ── QUESTION：输入答案 ──
            if self.state == GameState.QUESTION:
                self._handle_question_input(event)
                return

            # ── PAUSED：P/空格恢复，ESC 退出 ──
            if self.state == GameState.PAUSED:
                if event.key in (pygame.K_p, pygame.K_SPACE):
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                return

            # ── DYING：忽略所有输入 ──
            if self.state == GameState.DYING:
                return

            # ── GAME_OVER：R 重启，ESC 退出 ──
            if self.state == GameState.GAME_OVER:
                if event.key == pygame.K_r:
                    self._reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                return

            # ── PLAYING：方向键、暂停、退出 ──
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in (pygame.K_p, pygame.K_SPACE):
                self.state = GameState.PAUSED
            elif event.key == pygame.K_UP:
                self.snake.set_direction(Direction.UP)
            elif event.key == pygame.K_DOWN:
                self.snake.set_direction(Direction.DOWN)
            elif event.key == pygame.K_LEFT:
                self.snake.set_direction(Direction.LEFT)
            elif event.key == pygame.K_RIGHT:
                self.snake.set_direction(Direction.RIGHT)

    # ── 题目管理 ──

    def _start_game(self):
        """从菜单开始游戏"""
        self._next_question()

    def _handle_question_input(self, event):
        """处理 QUESTION 状态下的键盘输入"""
        if event.key == pygame.K_BACKSPACE:
            self._input_text = self._input_text[:-1]
            self._q_feedback_text = ""
            self._q_feedback_type = ""
        elif event.key == pygame.K_RETURN:
            self._check_answer()
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.unicode and event.unicode.isalpha() and len(self._input_text) < 20:
            self._input_text += event.unicode.lower()
            self._q_feedback_text = ""
            self._q_feedback_type = ""

    def _check_answer(self):
        """验证玩家输入的答案"""
        if not self._input_text:
            return
        if self._input_text == self.current_question.answer:
            # 正确 → 进入蛇阶段
            self._q_feedback_text = "Correct! Get ready..."
            self._q_feedback_type = "correct"
            self.sounds.play_eat_correct()
            self._start_snake_phase()
        else:
            # 错误 → 清空输入，显示提示
            self._q_feedback_text = f"Wrong! Try again. (Answer: {len(self.current_question.answer)} letters)"
            self._q_feedback_type = "wrong"
            self.sounds.play_eat_wrong()
            self._input_text = ""

    def _reset_game(self):
        """重置所有游戏状态，重新开始"""
        self.snake = Snake()
        self.score_mgr = ScoreManager()
        self.timer = QuestionTimer()
        self._move_counter = 0
        self._move_interval = MOVE_INTERVAL_BASE
        self.feedback_text = ""
        self.feedback_type = ""
        self.feedback_timer = 0
        self.shout_text = ""
        self.shout_timer = 0
        self._input_text = ""
        self._q_feedback_text = ""
        self._q_feedback_type = ""
        self.question_bank = QuestionBank(self.question_bank._file_path)
        self._next_question()

    def _next_question(self):
        """加载下一题，进入输入答案阶段"""
        self.current_question = self.question_bank.get_next()
        self._input_text = ""
        self._q_feedback_text = ""
        self._q_feedback_type = ""
        self.state = GameState.QUESTION

    def _start_snake_phase(self):
        """答案正确，进入蛇吃字母巩固阶段"""
        self.snake = Snake()
        # 速度递增：每完成1个单词，移动间隔减少1帧（更快）
        self._move_interval = max(
            MOVE_INTERVAL_MIN,
            MOVE_INTERVAL_BASE - self.score_mgr.word_count * SPEED_UP_PER_WORD,
        )
        occupied = set(self.snake.body)
        self.letter_manager.spawn(
            self.current_question.answer,
            self.current_question.distractors,
            occupied,
        )
        self.timer.reset()
        self.state = GameState.PLAYING

    # ── 主更新逻辑 ──

    def _update(self):
        self.effects.tick()
        self._tick_feedback()
        self._tick_shout()

        # MENU / QUESTION / PAUSED / GAME_OVER：不更新游戏逻辑
        if self.state in (GameState.MENU, GameState.QUESTION, GameState.PAUSED, GameState.GAME_OVER):
            return

        # DYING：死亡动画（蛇身逐节消失）
        if self.state == GameState.DYING:
            self._death_timer += 1
            if self._death_timer % DEATH_ANIM_SPEED == 0 and len(self.snake.body) > 0:
                self.snake.body.pop()
            if len(self.snake.body) == 0:
                self.state = GameState.GAME_OVER
            return

        # QUESTION_DONE 等待 → 下一题
        if self.state == GameState.QUESTION_DONE:
            self._state_timer -= 1
            if self._state_timer <= 0:
                self._next_question()
            return

        if self.state != GameState.PLAYING:
            return

        # 倒计时
        self.timer.tick()
        if self.timer.expired:
            self._on_time_up()
            return

        self._move_counter += 1
        if self._move_counter < self._move_interval:
            return
        self._move_counter = 0

        self.snake.move()
        self.events.emit(SNAKE_MOVE, {"head": self.snake.head})

        # 碰撞检测
        if self.snake.hits_boundary() or self.snake.hits_self():
            self.state = GameState.DYING
            self._death_timer = 0
            self.sounds.play_death()
            self.events.emit(GAME_OVER, {"reason": "collision", "score": self.score_mgr.score})
            return

        # 吃字母检测
        head = self.snake.head
        letter = self.letter_manager.get_letter_at(head[0], head[1])
        if letter is not None:
            self._handle_letter(letter)

    def _on_time_up(self):
        """超时处理"""
        self.events.emit(TIME_UP, {"seconds_left": 0, "question": self.current_question})
        info = self.score_mgr.on_time_up()
        self._show_feedback(
            f"时间到！-{info['penalty']}  {self.current_question.hint}",
            "time_up", FEEDBACK_DURATION,
        )
        self.effects.flash(FLASH_WRONG, max_alpha=100)
        self.snake.shrink()
        self.state = GameState.QUESTION_DONE
        self._state_timer = QUESTION_DONE_DURATION

    def _handle_letter(self, letter):
        """吃字母事件处理"""
        result = self.letter_manager.eat_letter(letter)

        if result["correct"] and result["in_order"]:
            # ── 正确 ──
            self.snake.grow()
            info = self.score_mgr.on_correct_letter()
            self.sounds.play_eat_correct()

            self.effects.flash(FLASH_CORRECT, max_alpha=60)
            self.events.emit(LETTER_CORRECT, {
                "letter": letter.char,
                "earned": info["earned"],
                "combo": self.score_mgr.combo,
                "multiplier": self.score_mgr.multiplier,
                "combo_shout": info.get("combo_shout", ""),
            })

            # 连击播报
            shout = info.get("combo_shout", "")
            if shout:
                self._show_shout(shout)

            self._show_feedback(
                f"+{info['earned']}  '{letter.char.upper()}'  正确！",
                "correct", FEEDBACK_DURATION,
            )

            # 检查单词是否完成
            if self.letter_manager.is_word_complete():
                bonus_info = self.score_mgr.on_word_complete(
                    self.timer.seconds_left
                )
                parts = [f"单词完成！+{bonus_info['total_bonus']}"]
                if bonus_info["time_bonus"] > 0:
                    parts.append(f"(时间奖励 +{bonus_info['time_bonus']})")
                if bonus_info["milestone_bonus"] > 0:
                    parts.append(f"里程碑 +{bonus_info['milestone_bonus']}！")
                parts.append(self.current_question.hint)

                self._show_feedback("  ".join(parts), "complete", QUESTION_DONE_DURATION)
                self.effects.flash(FLASH_COMPLETE, max_alpha=100, decay=2)
                self.sounds.play_word_complete()

                self.events.emit(WORD_COMPLETE, {
                    "question": self.current_question,
                    "bonus": bonus_info,
                    "combo": self.score_mgr.combo,
                    "score": self.score_mgr.score,
                })

                self.state = GameState.QUESTION_DONE
                self._state_timer = QUESTION_DONE_DURATION
        else:
            # ── 错误 ──
            self.snake.shrink()
            info = self.score_mgr.on_wrong_letter()
            self.sounds.play_eat_wrong()

            # 干扰字母被吃掉后补充一个新的
            if not result["correct"]:
                occupied = set(self.snake.body)
                self.letter_manager.replenish_distractor(
                    self.current_question.answer, occupied,
                )

            # 倒计时惩罚
            self.timer.penalize()

            if not result["correct"]:
                msg = f"'{letter.char.upper()}' 不属于答案 -{info['penalty']}"
            else:
                msg = f"顺序错误！当前需要 '{self.letter_manager.current_needed_char(self.current_question.answer)}'"

            self._show_feedback(
                f"{msg}  时间-{TIMER_PENALTY_SECONDS}s  {self.current_question.hint}",
                "wrong", FEEDBACK_DURATION,
            )
            self.effects.flash(FLASH_WRONG, max_alpha=80)

            self.events.emit(LETTER_WRONG, {
                "letter": letter.char,
                "penalty": info["penalty"],
                "combo_broken": info["combo_broken"],
                "question": self.current_question,
            })

    # ── 反馈管理 ──

    def _show_feedback(self, text: str, ftype: str, duration: int):
        self.feedback_text = text
        self.feedback_type = ftype
        self.feedback_timer = duration

    def _tick_feedback(self):
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer <= 0:
                self.feedback_text = ""

    def _show_shout(self, text: str):
        """连击播报（大号文字短暂显示）"""
        self.shout_text = text
        self.shout_timer = 45  # 0.75 秒

    def _tick_shout(self):
        if self.shout_timer > 0:
            self.shout_timer -= 1
            if self.shout_timer <= 0:
                self.shout_text = ""

    # ── 渲染 ──

    def _render(self):
        # ── MENU：独立菜单画面 ──
        if self.state == GameState.MENU:
            self.renderer.draw_menu()
            pygame.display.flip()
            return

        # ── QUESTION：输入答案画面 ──
        if self.state == GameState.QUESTION:
            self.renderer.draw_question_screen(
                self.current_question,
                self._input_text,
                self._q_feedback_text,
                self._q_feedback_type,
            )
            pygame.display.flip()
            return

        # ── 游戏画面（PLAYING / PAUSED / QUESTION_DONE / GAME_OVER 共用） ──
        self.renderer.draw_grid()
        self.renderer.draw_snake(self.snake)

        if self.state in (GameState.PLAYING, GameState.QUESTION_DONE):
            self.renderer.draw_letters(self.letter_manager)

        # 屏幕特效（覆盖在游戏区域上）
        self.effects.draw()

        # HUD（在最上层）
        if self.current_question:
            self.renderer.draw_hud(
                self.current_question,
                self.letter_manager,
                self.score_mgr,
                self.timer,
                self.feedback_text,
                self.feedback_type,
            )

        # 连击播报（游戏区域中央）
        if self.shout_text:
            self._draw_shout(self.shout_text)

        # ── PAUSED：叠加暂停遮罩 ──
        if self.state == GameState.PAUSED:
            self.renderer.draw_pause_overlay()

        # ── GAME_OVER：叠加结算画面 ──
        if self.state == GameState.GAME_OVER:
            self.renderer.draw_game_over(self.score_mgr)

        pygame.display.flip()

    def _draw_shout(self, text: str):
        """在游戏区域中央绘制大号连击文字"""
        font = pygame.font.SysFont("arial", 56, bold=True)
        color = (255, 220, 80)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(400, 350))
        self.screen.blit(surf, rect)
