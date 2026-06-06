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
from systems.learning_tracker import LearningTracker
from systems.achievements import AchievementManager


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

        # 学习追踪
        from config import LEARNING_DATA_PATH
        base_dir = os.path.dirname(os.path.dirname(__file__))
        learn_path = os.path.join(base_dir, LEARNING_DATA_PATH)
        self.tracker = LearningTracker(learn_path)

        # 成就系统
        ach_path = os.path.join(base_dir, "data", "achievements.json")
        self.achievements = AchievementManager(ach_path)

        # 死亡动画
        self._death_timer = 0

        # 上一题结果（用于复习画面）
        self._last_answer_correct = True
        self._game_mode = "normal"

        # 蛇阶段追踪
        self._distractors_eaten = 0

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)
        self.tracker.save()
        self.achievements.save()
        pygame.quit()

    def _check_achievements(self):
        """检查并解锁成就"""
        wc = self.score_mgr.word_count
        streak = self.tracker.get_streak_count()
        mastery = self.tracker.get_category_mastery()

        self.achievements.check_and_unlock("first_word", wc >= 1)
        self.achievements.check_and_unlock("streak_5", streak >= 5)
        self.achievements.check_and_unlock("streak_10", streak >= 10)
        self.achievements.check_and_unlock("streak_20", streak >= 20)
        self.achievements.check_and_unlock("word_10", wc >= 10)
        self.achievements.check_and_unlock("word_50", wc >= 50)
        self.achievements.check_and_unlock("word_100", wc >= 100)
        self.achievements.check_and_unlock("perfect_snake",
                                           self._distractors_eaten == 0 and wc > 0)
        self.achievements.check_and_unlock("category_master",
                                           any(v >= 0.9 for v in mastery.values()))
        self.achievements.check_and_unlock("all_categories",
                                           len(mastery) >= 10)

        # 显示新解锁的成就
        for ach in self.achievements.get_newly_unlocked():
            self._show_shout(f"🏆 {ach.name}")

    # ── 事件处理 ──

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type != pygame.KEYDOWN:
                continue

            # ── MENU：选择模式 ──
            if self.state == GameState.MENU:
                if event.key == pygame.K_1:
                    self._start_game()
                elif event.key == pygame.K_2:
                    self._start_practice_mode()
                elif event.key == pygame.K_3:
                    self._start_challenge_mode()
                return

            # ── QUESTION：输入答案 ──
            if self.state == GameState.QUESTION:
                self._handle_question_input(event)
                return

            # ── QUESTION_DONE：复习画面，任意键继续 ──
            if self.state == GameState.QUESTION_DONE:
                self._next_question()
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
        """从菜单开始游戏（正常模式）"""
        self._game_mode = "normal"
        self._next_question()

    def _start_practice_mode(self):
        """练习模式：优先出弱分类题目"""
        self._game_mode = "practice"
        self._next_question()

    def _start_challenge_mode(self):
        """挑战模式：高速 + 无提示"""
        self._game_mode = "challenge"
        self._move_interval = max(MOVE_INTERVAL_MIN, MOVE_INTERVAL_BASE - 3)
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
        q = self.current_question
        if self._input_text == q.answer:
            # 正确 → 记录学习数据，进入蛇阶段
            self.tracker.record_answer(q.id, q.category, True)
            self._q_feedback_text = "Correct! Get ready..."
            self._q_feedback_type = "correct"
            self.sounds.play_eat_correct()
            self._start_snake_phase()
        else:
            # 错误 → 记录学习数据，清空输入，显示反馈
            self.tracker.record_answer(q.id, q.category, False)
            self._q_feedback_text = self._get_error_feedback(self._input_text, q)
            self._q_feedback_type = "wrong"
            self.sounds.play_eat_wrong()
            self._input_text = ""

    def _get_error_feedback(self, user_input: str, question) -> str:
        """根据用户输入生成具体的错误反馈"""
        answer = question.answer
        # 检查常见错误模式
        if question.error_patterns:
            for pattern in question.error_patterns:
                if user_input == pattern:
                    return f"'{pattern}' 是常见错误！{question.hint}"

        # 检查 -ing / -ed 混淆
        if answer.endswith("ed") and user_input == answer[:-2] + "ing":
            return f"句子需要过去式(-ed)，不是进行时(-ing)。{question.hint}"
        if answer.endswith("ing") and user_input == answer[:-3] + "ed":
            return f"句子需要进行时(-ing)，不是过去式(-ed)。{question.hint}"

        # 检查 -s / 原形 混淆
        if answer.endswith("s") and user_input == answer[:-1]:
            return f"主语是第三人称单数，动词需要加 -s。{question.hint}"
        if not answer.endswith("s") and user_input == answer + "s":
            return f"主语不是第三人称单数，不需要加 -s。{question.hint}"

        # 长度提示
        if len(user_input) != len(answer):
            return f"答案有 {len(answer)} 个字母，你输入了 {len(user_input)} 个。再试试！"

        # 通用回退
        return f"不对哦，再想想！(答案: {len(answer)} 个字母)"

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
        self._game_mode = "normal"
        self._distractors_eaten = 0
        self.question_bank = QuestionBank(self.question_bank._file_path)
        self._next_question()

    def _next_question(self):
        """加载下一题，进入输入答案阶段"""
        if self._game_mode == "practice":
            self.current_question = self.question_bank.get_next_adaptive(self.tracker)
        else:
            self.current_question = self.question_bank.get_next(self.tracker)
        self._input_text = ""
        self._q_feedback_text = ""
        self._q_feedback_type = ""
        self.state = GameState.QUESTION

    def _start_snake_phase(self):
        """答案正确，进入蛇吃字母巩固阶段"""
        self._distractors_eaten = 0
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
            self.current_question.error_patterns,
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
            self.tracker.save()
            self.achievements.save()
            self.events.emit(GAME_OVER, {"reason": "collision", "score": self.score_mgr.score})
            return

        # 吃字母检测
        head = self.snake.head
        letter = self.letter_manager.get_letter_at(head[0], head[1])
        if letter is not None:
            self._handle_letter(letter)

    def _on_time_up(self):
        """超时处理"""
        self.tracker.record_answer(self.current_question.id, self.current_question.category, False)
        self.tracker.save()
        self.events.emit(TIME_UP, {"seconds_left": 0, "question": self.current_question})
        info = self.score_mgr.on_time_up()
        self._show_feedback(
            f"时间到！-{info['penalty']}  {self.current_question.hint}",
            "time_up", FEEDBACK_DURATION,
        )
        self.effects.flash(FLASH_WRONG, max_alpha=100)
        self.snake.shrink()
        self._last_answer_correct = False
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
                # 完美通关奖励
                if self._distractors_eaten == 0:
                    self.score_mgr.score += 100
                    parts.append("★ 完美通关 +100！")
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

                self._last_answer_correct = True
                self.state = GameState.QUESTION_DONE
                self._state_timer = QUESTION_DONE_DURATION
                self._check_achievements()
        else:
            # ── 错误 ──
            self.snake.shrink()
            info = self.score_mgr.on_wrong_letter()
            self.sounds.play_eat_wrong()

            # 干扰字母被吃掉后补充一个新的
            if not result["correct"]:
                self._distractors_eaten += 1
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

        # ── QUESTION_DONE：复习画面 ──
        if self.state == GameState.QUESTION_DONE:
            self.renderer.draw_review_screen(
                self.current_question,
                self.score_mgr,
                self._last_answer_correct,
            )
            pygame.display.flip()
            return

        # ── 游戏画面（PLAYING / PAUSED / GAME_OVER 共用） ──
        self.renderer.draw_grid()
        self.renderer.draw_snake(self.snake)

        if self.state == GameState.PLAYING:
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
