WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
OPPOSITE_COLOR = {WHITE: BLACK, BLACK: WHITE}

INITIAL_STATE = {
    (i, j): (WHITE, 1)
    if (i, j) in ((0, 0), (3, 1), (4, 0), (7, 1))
    else (WHITE, 2)
    if (i, j) in ((1, 7), (2, 6), (5, 7), (6, 6))
    else (BLACK, 1)
    if (i, j) in ((0, 6), (3, 7), (4, 6), (7, 7))
    else (BLACK, 2)
    if (i, j) in ((1, 1), (2, 0), (5, 1), (6, 0))
    else None
    for i in range(8)
    for j in range(8)
    if (i + j) % 2 == 0
}

HOME_ROW = {
    WHITE: ((0, 0), (2, 0), (4, 0), (6, 0)),
    BLACK: ((1, 7), (3, 7), (5, 7), (7, 7)),
}


MOVE_DIRECTIONS = {
    (WHITE, 1): ((1, 1), (-1, 1)),
    (WHITE, 2): ((1, -1), (-1, -1)),
    (BLACK, 1): ((1, -1), (-1, -1)),
    (BLACK, 2): ((1, 1), (-1, 1)),
}

DIAGONALS = {
    ((i, j), d): [
        (i + s * d[0], j + s * d[1])
        for s in range(1, 8)
        if 0 <= i + s * d[0] < 8 and 0 <= j + s * d[1] < 8
    ]
    for i, j in INITIAL_STATE
    for checker in MOVE_DIRECTIONS
    for d in MOVE_DIRECTIONS[checker]
}

# Parameters and weights for evaluation
DOUBLES_PATHS_MAX = 10
SINGLES_PATHS_MAX = 10

CHECKERS_COUNT_WEIGHT = 120
DOUBLES_PATHS_WEIGHT = 8
SINGLES_PATHS_WEIGHT = 2
DOUBLES_WEIGHT = 1
