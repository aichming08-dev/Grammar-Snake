#!/usr/bin/env python3
"""Grammar Snake — 英语教育贪吃蛇游戏入口"""

from game.director import GameDirector


def main():
    director = GameDirector()
    director.run()


if __name__ == "__main__":
    main()
