import pygame as pg

import impasse
from impasse.constants import *

FPS = 60
SEC = pg.USEREVENT


def get_cell_from_mouse(pos):
    return (pos[0] // SQUARE_SIZE, (HEIGHT - pos[1]) // SQUARE_SIZE)


def play(secs=None, ai_player=None):
    """
    Main loop controlling the gameplay.
    """
    WINDOW = pg.display.set_mode((WIDTH + INFO_WIDTH, HEIGHT))
    pg.display.set_caption("IMPASSE")
    run = True
    clock = pg.time.Clock()
    game = impasse.GUI(WINDOW, secs, ai_player)
    pg.time.set_timer(SEC, 1000)

    while run:
        clock.tick(FPS)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False

            if event.type == SEC:
                game.update_time()

            if event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()
                cell = get_cell_from_mouse(pos)
                game.select(cell)

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_c:
                    game.change_show_cells()

                if event.key == pg.K_z:
                    game.undo_move()

                if event.key == pg.K_n:
                    game.new_game(secs, ai_player)

        game.board_update()

    pg.quit()


if __name__ == "__main__":
    play(ai_player=BLACK)
