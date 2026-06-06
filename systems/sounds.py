"""程序化音效生成，无需外部音频文件"""

import pygame

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def _generate_tone(frequency: float, duration: float, volume: float = 0.4,
                   fade_out: bool = True) -> pygame.mixer.Sound:
    """生成单频音效"""
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t) * volume

    # 淡出避免爆音
    if fade_out:
        fade_len = min(samples // 4, sample_rate // 20)
        if fade_len > 0:
            fade = np.linspace(1.0, 0.0, fade_len)
            wave[-fade_len:] *= fade

    stereo = np.column_stack((wave, wave))
    sound_array = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)


def _generate_chord(frequencies: list, duration: float, volume: float = 0.3) -> pygame.mixer.Sound:
    """生成和弦（多个频率叠加）"""
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    wave = np.zeros(samples)
    for freq in frequencies:
        wave += np.sin(2 * np.pi * freq * t) * (volume / len(frequencies))

    fade_len = min(samples // 3, sample_rate // 15)
    if fade_len > 0:
        fade = np.linspace(1.0, 0.0, fade_len)
        wave[-fade_len:] *= fade

    stereo = np.column_stack((wave, wave))
    sound_array = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)


class _NullSound:
    """静音占位，当 numpy 不可用时使用"""
    def play(self): pass
    def stop(self): pass
    def set_volume(self, v): pass


class SoundManager:
    """游戏音效管理器"""

    def __init__(self):
        if not _HAS_NUMPY:
            self.eat_correct = _NullSound()
            self.eat_wrong = _NullSound()
            self.word_complete = _NullSound()
            self.death = _NullSound()
            return

        try:
            pygame.mixer.pre_init(44100, -16, 2, 1024)
            pygame.mixer.init()
            self.eat_correct = _generate_tone(660, 0.12, 0.35)
            self.eat_wrong = _generate_tone(200, 0.25, 0.3)
            self.word_complete = _generate_chord([523, 659, 784], 0.4, 0.35)
            self.death = _generate_tone(120, 0.5, 0.4)
        except Exception:
            # mixer 初始化失败，退化为静音
            self.eat_correct = _NullSound()
            self.eat_wrong = _NullSound()
            self.word_complete = _NullSound()
            self.death = _NullSound()

    def play_eat_correct(self):
        self.eat_correct.play()

    def play_eat_wrong(self):
        self.eat_wrong.play()

    def play_word_complete(self):
        self.word_complete.play()

    def play_death(self):
        self.death.play()
