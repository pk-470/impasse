import pygame as pg
import pickle
import os

from impasse.constants import *
from impasse.ai import *
from impasse.position import *


class GUI(Position):
    """
    A GUI wrapper running on top of the Position class to play the game graphically.
    """

    def __init__(self, window: pg.Surface, secs=None, ai_player=None):
        pg.init()
        self.window = window
        self.timed = True if secs and not ai_player else False
        self.fonts = {
            "info": pg.font.SysFont("georgia", 24),
            "cell": pg.font.SysFont("georgia", 14),
        }
        self.new_game(secs, ai_player)

    def new_game(self, secs, ai_player):
        """
        Creates a new game from the starting position.
        """
        self.make_position()
        self.last_move_data = {"cells": [], "color": None, "tag": None}
        self.undo_activated = False
        self.times = {WHITE: secs, BLACK: secs}
        self.export_position_data()
        self.selection_activated = True
        self.selected = None
        self.show_cells = True
        self.ai_player = AI(ai_player) if ai_player else None
        self.print_intro_message()
        if ai_player == WHITE:
            self.ai_play_turn_full()

    def print_intro_message(self):
        print("--------------------------------------------------")
        print()
        print("Welcome to Impasse!")
        print()
        print("--------------------------------------------------")
        print()

    def export_position_data(self):
        """
        Saves the position data in an external file for recovery.
        """
        position_data = {
            "state": self.state,
            "turn": self.turn,
            "all_legal_moves": self.all_legal_moves,
            "checkers_total": self.checkers_total,
            "winner": self.winner,
            "last_move_data": self.last_move_data,
            "undo_activated": self.undo_activated,
            "times": self.times,
        }
        with open(
            os.path.join("impasse", "current_game_history", "last_position_data.p"),
            "wb",
        ) as file:
            pickle.dump(position_data, file)

    def load_position(self):
        """
        Loads position data from external file.
        """
        position_data = pickle.load(
            open(
                os.path.join("impasse", "current_game_history", "last_position_data.p"),
                "rb",
            )
        )
        self.state = position_data["state"]
        self.turn = position_data["turn"]
        self.all_legal_moves = position_data["all_legal_moves"]
        self.checkers_total = position_data["checkers_total"]
        self.winner = position_data["winner"]
        self.last_move_data = position_data["last_move_data"]
        self.undo_activated = position_data["undo_activated"]
        self.times = position_data["times"]
        self.selection_activated = False if self.winner else True
        self.selected = None

    def update_time(self):
        """
        Updates the time left for each player (called every second from the main loop).
        """
        if self.timed:
            if self.times[self.turn] > 1:
                self.times[self.turn] -= 1
            elif self.times[self.turn] > 0:
                self.times[self.turn] -= 1
                self.winner = OPPOSITE_COLOR[self.turn]

    # Drawing functions

    def board_update(self):
        """
        Updates the board and info boxes.
        """
        self.draw_board()
        self.show_info()
        self.show_cell_names()
        if self.winner:
            self.show_winner()
            self.selection_activated = False
        else:
            self.show_last_move()
            self.show_checkers_that_can_move()
            self.show_selected()
            self.show_legal_moves_for_selected()
        pg.display.update()

    def change_show_cells(self):
        self.show_cells = not self.show_cells

    def draw_checker(self, cell):
        """
        Draws the checkers on the board.
        """
        x, y = calculate_coords(cell)
        color, type = self.state[cell]
        pg.draw.circle(self.window, color, (x, y), RADIUS)
        if type == 2:
            pg.draw.circle(self.window, OPPOSITE_COLOR[color], (x, y), 2 * RADIUS / 3)
            pg.draw.circle(self.window, color, (x, y), RADIUS / 2)

    def draw_board(self):
        """
        Draws the actual 8x8 board.
        """
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    pg.draw.rect(self.window, DARK, square_draw_tuple((i, j)))
                    if self.is_occupied((i, j)):
                        self.draw_checker((i, j))
                else:
                    pg.draw.rect(self.window, LIGHT, square_draw_tuple((i, j)))

    def make_time_string(self, time):
        mins = time // 60
        mins = "0" + str(mins) if mins < 10 else str(mins)
        secs = time % 60
        secs = "0" + str(secs) if secs < 10 else str(secs)
        return mins + ":" + secs

    def make_last_move_string(self):
        return (
            " to ".join(cell_to_string(cell) for cell in self.last_move_data["cells"])
            + f" ({self.last_move_data['tag']})"
        )

    def make_info_box(self, color):
        """
        Makes the info box for each player.
        """
        pg.draw.rect(self.window, color, info_box_draw_tuple(color))
        checkers = self.checkers_total[color]
        # Checkers count
        if checkers and (
            not self.timed or self.timed and self.times[OPPOSITE_COLOR[color]]
        ):
            checkers_num = self.fonts["info"].render(
                f"{COLOR_NAME[color]}: {checkers}",
                True,
                OPPOSITE_COLOR[color],
            )
            self.window.blit(checkers_num, (WIDTH, INFO_HEIGHT_PLACEMENT[color]))
        # Time
        if self.timed:
            time = self.fonts["info"].render(
                self.make_time_string(self.times[color]),
                True,
                OPPOSITE_COLOR[color],
            )
            self.window.blit(
                time,
                (
                    WIDTH + INFO_WIDTH - time.get_width(),
                    INFO_HEIGHT_PLACEMENT[color] + HEIGHT // 2 - time.get_height(),
                ),
            )
        # Last move
        if self.last_move_data["color"] == color:
            last_move = self.fonts["info"].render(
                self.make_last_move_string(), True, OPPOSITE_COLOR[color]
            )
            self.window.blit(
                last_move,
                (
                    WIDTH,
                    INFO_HEIGHT_PLACEMENT[color] + last_move.get_height(),
                ),
            )

    def show_cell_names(self):
        if self.show_cells:
            for i in range(8):
                for j in range(8):
                    color = LIGHT if (i + j) % 2 == 0 else DARK
                    img = self.fonts["cell"].render(cell_to_string((i, j)), True, color)
                    self.window.blit(img, square_draw_tuple((i, j)))

    def show_winner(self):
        img = self.fonts["info"].render(
            f"{COLOR_NAME[self.winner]} WINS!!!",
            True,
            OPPOSITE_COLOR[self.winner],
        )
        self.window.blit(img, (WIDTH, INFO_HEIGHT_PLACEMENT[self.winner]))

    def show_info(self):
        self.make_info_box(WHITE)
        self.make_info_box(BLACK)

    def highlight(self, cell, color):
        x, y = calculate_coords(cell)
        pg.draw.circle(self.window, color, (x, y), SQUARE_SIZE // 8)

    def show_checkers_that_can_move(self):
        if not (self.ai_player and self.turn == self.ai_player.color):
            for cell in self.all_legal_moves:
                self.highlight(cell, ORANGE)

    def show_legal_moves_for_selected(self):
        if self.selected:
            for move in self.all_legal_moves[self.selected]:
                if move:
                    self.highlight(move, BLUE)

    def show_selected(self):
        if self.selected:
            self.highlight(self.selected, RED)

    def show_last_move(self):
        for cell in self.last_move_data["cells"]:
            self.highlight(cell, YELLOW)

    # Gameplay functions

    def select(self, cell):
        """
        A function that determines what happens when you select a cell (selects checker
        or moves previously selected checker to newly selected cell).
        """
        if not self.selection_activated:
            return
        if last_selected := self.selected:
            # If there is a selected cell already, then that cell contains a checker
            # that can be moved on the board. If moving to the newly selected cell is
            # legal, then move. Otherwise, unselect the previous cell and try to select
            # the new one.
            self.selected = None
            if cell in self.all_legal_moves[last_selected]:
                tag = self.all_legal_moves[last_selected][cell]
                self.complete_move(last_selected, cell, tag)
            else:
                self.select(cell)
        # Check if the cell contains a checker that can be moved
        elif cell in self.all_legal_moves:
            # Bear off
            if self.all_legal_moves[cell].get(None) == "B":
                self.complete_move(cell, None, "B")
            # Select cell
            else:
                self.selected = cell

    def complete_move(self, origin, target, tag):
        """
        Activates undo, exports position, updates the shown info and
        updates the board.
        """
        self.undo_activated = True
        if not (self.ai_player and self.ai_player.color == self.turn):
            self.export_position_data()
        state_update = self.apply_move(origin, target, tag)
        self.last_move_data = {
            "cells": list(state_update),
            "color": self.turn,
            "tag": tag,
        }
        self.update(state_update, tag)

    def undo_move(self):
        """
        Goes back to the board state before the last human move.
        Can only go back one move.
        """
        if self.undo_activated:
            self.load_position()
            self.undo_activated = False

    def change_turn(self):
        """
        Overrides Position's change_turn function to print the evaluation
        of each position and to account for an AI player.
        """
        Position.change_turn(self)
        if not self.ai_player:
            print("Last move:", self.make_last_move_string())
            print(f"Evaluation after move: {self.evaluate()}")
            print()
            print("--------------------------------------------------")
            print()
        elif not self.winner and self.turn == self.ai_player.color:
            self.ai_play_turn_full()

    def ai_play_turn(self):
        """
        Plays a full turn (which may consist of multiple moves) for the AI.
        Also prints the best move suggested by the AI and the evaluation after
        the move (along with the evaluations printed by the suggested_move
        function).
        """
        self.selection_activated = False
        self.board_update()
        print("AI calculating...")
        print()
        origin, target, tag, unique_move = self.ai_player.suggested_move(self)
        self.complete_move(origin, target, tag)
        print("Best move:", self.make_last_move_string())
        print(f"Evaluation after move: {self.evaluate()}")
        print()
        if unique_move:
            pg.time.wait(500)
        self.board_update()
        if not self.winner and self.turn == self.ai_player.color:
            self.ai_play_turn()
        self.selection_activated = True

    def ai_play_turn_full(self):
        """
        Plays a full turn for the AI while also printing the evaluation
        of the position before the AI starts thinking.
        """
        print(f"Current evaluation: {self.evaluate()}")
        print()
        self.ai_play_turn()
        print("--------------------------------------------------")
        print()
