from impasse.constants.position_constants import *

WIDTH, HEIGHT = 640, 640
SQUARE_SIZE = WIDTH // 8
RADIUS = 2 * SQUARE_SIZE // 5

INFO_WIDTH = 2 * WIDTH // 5
INFO_HEIGHT_PLACEMENT = {WHITE: HEIGHT // 2, BLACK: 0}
COLOR_NAME = {WHITE: "WHITE", BLACK: "BLACK"}

LIGHT = (240, 240, 210)
DARK = (120, 160, 80)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 234, 0)
ORANGE = (255, 140, 0)

COLUMN_COORDS_LETTERS = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7}
COLUMN_COORDS_NUMBERS = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H"}


def square_draw_tuple(cell):
    return (
        cell[0] * SQUARE_SIZE,
        HEIGHT - (cell[1] + 1) * SQUARE_SIZE,
        SQUARE_SIZE,
        SQUARE_SIZE,
    )


def info_box_draw_tuple(color):
    return (
        WIDTH,
        INFO_HEIGHT_PLACEMENT[color],
        INFO_WIDTH,
        HEIGHT // 2,
    )


def calculate_coords(cell):
    return (
        SQUARE_SIZE * (cell[0] + 0.5),
        HEIGHT - (SQUARE_SIZE * (int(cell[1]) + 0.5)),
    )


def cell_to_string(cell):
    if cell:
        return f"{COLUMN_COORDS_NUMBERS[cell[0]]}{cell[1]+1}"
    return None


def string_to_cell(cell_string):
    if cell_string:
        return COLUMN_COORDS_LETTERS[cell_string[0]], int(cell_string[1]) - 1
    return None
