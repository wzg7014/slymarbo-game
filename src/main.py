"""
像素魂斗罗 - 主程序入口
"""
import pygame
import sys
from src.constants import *
from src import utils
from src.game import Game


def main():
    # 初始化pygame
    pygame.mixer.pre_init(44100, -16, 1, 2048)
    pygame.init()
    pygame.mixer.set_num_channels(16)

    # 创建屏幕
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Adventures of Slymarbo")
    clock = pygame.time.Clock()

    # 禁用IME文本输入，防止中文输入法拦截WASD按键
    try:
        pygame.key.stop_text_input()
    except AttributeError:
        pass  # pygame < 2.2 没有此方法

    # 初始化资源（字体和音效）
    utils.init_all()

    # 创建游戏实例
    game = Game(screen)

    # 主循环
    running = True
    while running:
        try:
            events = pygame.event.get()
            keys = pygame.key.get_pressed()

            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            if not running:
                break

            if game.state == 'start':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            game.state = 'level_select'
                        elif event.key == pygame.K_ESCAPE:
                            game.prev_state = 'start'
                            game.state = 'settings'
                game.draw_start(screen)

            elif game.state == 'level_select':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_a, pygame.K_LEFT):
                            game.level_select_idx = (game.level_select_idx - 1) % TOTAL_LEVELS
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            game.level_select_idx = (game.level_select_idx + 1) % TOTAL_LEVELS
                        elif event.key == pygame.K_RETURN:
                            game.start_from_level(game.level_select_idx + 1)
                        elif event.key == pygame.K_ESCAPE:
                            game.state = 'start'
                game.draw_level_select(screen)

            elif game.state == 'settings':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game.state = game.prev_state
                        elif event.key == pygame.K_LEFT:
                            game.difficulty_index = max(0, game.difficulty_index - 1)
                            game.difficulty_name = game.difficulty_options[game.difficulty_index]
                            game.difficulty = DIFFICULTY_SETTINGS[game.difficulty_name]
                        elif event.key == pygame.K_RIGHT:
                            game.difficulty_index = min(2, game.difficulty_index + 1)
                            game.difficulty_name = game.difficulty_options[game.difficulty_index]
                            game.difficulty = DIFFICULTY_SETTINGS[game.difficulty_name]
                        elif event.key == pygame.K_c:
                            game.codex_idx = 0
                            game.codex_page = 0
                            game.state = 'codex'
                game.draw_settings(screen)

            elif game.state == 'codex':
                entries = game._codex_current_list()
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game.state = 'settings'
                        elif event.key in (pygame.K_w, pygame.K_UP):
                            game.codex_idx = max(0, game.codex_idx - 1)
                        elif event.key in (pygame.K_s, pygame.K_DOWN):
                            game.codex_idx = min(len(entries) - 1, game.codex_idx + 1)
                        elif event.key in (pygame.K_a, pygame.K_LEFT):
                            game.codex_page = (game.codex_page - 1) % 2
                            game.codex_idx = 0
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            game.codex_page = (game.codex_page + 1) % 2
                            game.codex_idx = 0
                        elif event.key == pygame.K_RETURN:
                            game.state = 'codex_detail'
                game.draw_codex(screen)

            elif game.state == 'codex_detail':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game.state = 'codex'
                game.draw_codex_detail(screen)

            elif game.state == 'playing':
                game.handle_playing(events, keys)
                if game.state == 'playing':
                    game.draw_playing(screen)

            elif game.state == 'paused':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game.state = 'playing'
                        elif event.key == pygame.K_s:
                            game.prev_state = 'paused'
                            game.state = 'settings'
                        elif event.key == pygame.K_q:
                            running = False
                game.draw_paused(screen)

            elif game.state == 'gameover':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            game.reset_game()
                            game.state = 'start'
                        elif event.key == pygame.K_q:
                            running = False
                game.draw_gameover(screen)

            elif game.state == 'victory':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            game.reset_game()
                            game.state = 'start'
                        elif event.key == pygame.K_q:
                            running = False
                game.draw_victory(screen)

            elif game.state == 'level_complete':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            game.advance_to_next_level()
                        elif event.key == pygame.K_q:
                            running = False
                game.draw_level_complete(screen)

            elif game.state == 'levelup_select':
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        n = len(game.levelup_options)
                        if event.key in (pygame.K_a, pygame.K_LEFT):
                            game.levelup_selected = (game.levelup_selected - 1) % n
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            game.levelup_selected = (game.levelup_selected + 1) % n
                        elif event.key == pygame.K_RETURN:
                            uid = game.levelup_options[game.levelup_selected]
                            game.player.apply_upgrade(uid)
                            game.state = 'playing'
                game.draw_levelup_select(screen)

            pygame.display.flip()
            clock.tick(FPS)

        except Exception as e:
            print(f"[错误] {e}")
            import traceback
            traceback.print_exc()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
