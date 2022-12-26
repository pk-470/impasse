import random
from impasse.constants.position_constants import *

MIN_SEARCH_DEPTH = 5
MILLISECONDS_PER_MOVE = 6000
MAX_MILLISECONDS_PER_MOVE = 10000


class ABTimeOut(Exception):
    pass


def milliseconds(time):
    return int(time * 1000)


# Dictionary of random ids for each combination of (square, piece)
random.seed(42)
rand_ids = {
    (cell, (color, i)): random.getrandbits(64)
    for cell in INITIAL_STATE
    for color in (WHITE, BLACK)
    for i in (1, 2)
} | {(cell, None): random.getrandbits(64) for cell in INITIAL_STATE}


def make_state_hash(state):
    state_hash = 0
    for cell in state:
        state_hash ^= rand_ids[(cell, state[cell])]
    return state_hash
