from math import inf
import random
import time

from impasse.constants import *
from impasse.position import *


class AI:
    """
    A class to take care of the logic behind an AI player. Uses alpha-beta search
    with move-ordering, iterative deepening and a transposition table.
    """

    def __init__(self, color):
        self.color = color
        self.transposition_table = {}

    # Transposition table retrieval and storage

    def tt_retrieve(self, position: Position):
        try:
            return self.transposition_table[position.state_hash]
        except KeyError:
            return None, None, None, None

    def tt_store(self, position: Position, value, move, flag, depth):
        self.transposition_table[position.state_hash] = (value, move, flag, depth)

    # Finding moves

    def get_random_move(self, position: Position):
        """
        Returns a move randomly chosen amongst the available moves of the position.
        """
        origin = random.choice(list(position.all_legal_moves))
        target = random.choice(list(position.all_legal_moves[origin]))
        tag = position.all_legal_moves[origin][target]
        return origin, target, tag

    def ordered_moves(self, position: Position, most_promising_move=None):
        """
        Returns an ordered list of the available moves which hopefully generally increases
        the number of prunings during Alpha-Beta search. The moves are ordered as follows:
        - crowning moves (these are played necessarily)
        - bear offs
        - slides that block two enemy doubles
        - slides that block one enemy double
        - slides that block two enemy singles
        - slides that block one enemy single
        - moves that lead to a potential crowning
        - transpositions
        - the rest of the slides ordered from longest to shortest
        """
        check_first = []
        bear_offs = []
        crownings = []
        potential_crownings = []
        transposes = []
        slides_blocking_doubles_once = []
        slides_blocking_doubles_twice = []
        slides_blocking_singles_once = []
        slides_blocking_singles_twice = []
        other_slides = []
        for origin in position.all_legal_moves:
            moves = position.all_legal_moves[origin]
            for target in moves:
                tag = moves[target]
                move = (origin, target, tag)
                if move == most_promising_move:
                    check_first = [move]
                elif tag == "C":
                    crownings.append(move)
                elif tag in ("B", "SB", "TB"):
                    bear_offs.append(move)
                elif tag in ("SC", "TC"):
                    potential_crownings.append(move)
                elif tag == "T":
                    transposes.append(move)
                elif tag == "S":
                    blocks_double_once = False
                    blocks_double_twice = False
                    blocks_single_once = False
                    blocks_single_twice = False
                    color = position.turn
                    for direction in MOVE_DIRECTIONS[(color, 2)]:
                        for cell in DIAGONALS[(target, direction)]:
                            if not position.is_occupied(cell):
                                continue
                            if position.is_occupied_of_color(
                                cell, OPPOSITE_COLOR[color]
                            ) and not position.is_single(cell):
                                if blocks_double_once:
                                    blocks_double_twice = True
                                else:
                                    blocks_double_once = True
                                break
                            else:
                                break
                    if blocks_double_twice:
                        slides_blocking_doubles_twice.append(move)
                    elif blocks_double_once:
                        slides_blocking_doubles_once.append(move)
                    else:
                        for direction in MOVE_DIRECTIONS[(color, 1)]:
                            for cell in DIAGONALS[(target, direction)]:
                                if not position.is_occupied(cell):
                                    continue
                                if position.is_occupied_single_of_color(
                                    cell, OPPOSITE_COLOR[color]
                                ):
                                    if blocks_single_once:
                                        blocks_single_twice = True
                                    else:
                                        blocks_single_once = True
                                    break
                                else:
                                    break
                        if blocks_single_twice:
                            slides_blocking_singles_twice.append(move)
                        elif blocks_single_once:
                            slides_blocking_singles_once.append(move)
                        else:
                            other_slides.append(move)

        other_slides.sort(reverse=True, key=lambda x: abs(x[0][0] - x[1][0]))
        return (
            check_first
            + crownings
            + bear_offs
            + slides_blocking_doubles_twice
            + slides_blocking_doubles_once
            + slides_blocking_singles_twice
            + slides_blocking_singles_once
            + potential_crownings
            + transposes
            + other_slides
        )

    def minimax_parameters(self, color):
        """
        A helper function which returns the correct starting parameters to
        implement Alpha-Beta (MiniMax formulation) as a Max or a Min player.
        """
        if color == WHITE:
            return (
                -inf,
                lambda local_value, value: local_value > value,
                lambda alpha, beta, value: (max(alpha, value), beta),
            )
        else:
            return (
                inf,
                lambda local_value, value: local_value < value,
                lambda alpha, beta, value: (alpha, min(beta, value)),
            )

    def alpha_beta(
        self,
        position: Position,
        depth,
        alpha,
        beta,
    ):
        """
        Implements Alpha-Beta search (MiniMax formulation) enhanced by the use of a transposition table.
        Returns the Alpha-Beta evaluation of the position along with the best move found.
        """

        # Terminate if you run out of time
        move_time = milliseconds(time.time()) - self.search_start_time
        if (
            move_time > MILLISECONDS_PER_MOVE and self.min_search_depth_reached
        ) or move_time > MAX_MILLISECONDS_PER_MOVE:
            raise ABTimeOut

        old_alpha, old_beta = alpha, beta
        # Search for the position in the transposition table. If the search depth in
        # the TT is larger than the current search depth, then trust the TT entry.
        tt_value, tt_move, tt_flag, tt_depth = self.tt_retrieve(position)
        if tt_depth is not None and tt_depth >= depth:
            if tt_flag == "E":
                return tt_value, tt_move
            elif tt_flag == "L":
                alpha = max(alpha, tt_value)
            elif tt_flag == "U":
                beta = min(beta, tt_value)
            if alpha >= beta:
                return tt_value, tt_move

        # Regular Alpha-Beta
        if position.winner or not depth:
            return position.evaluate(), None

        start_value, value_test, alpha_beta_assignment = self.minimax_parameters(
            position.turn
        )
        value = start_value
        # Check TT move first
        for origin, target, tag in self.ordered_moves(position, tt_move):
            new_position = position.new_position_after_move(origin, target, tag)
            if new_position.turn == position.turn:
                local_value, _ = self.alpha_beta(new_position, depth, alpha, beta)
            else:
                local_value, _ = self.alpha_beta(new_position, depth - 1, alpha, beta)
            if value_test(local_value, value):
                value = local_value
                best_move = (origin, target, tag)
            alpha, beta = alpha_beta_assignment(alpha, beta, value)
            if alpha >= beta:
                break

        # Store the position in the TT
        if value <= old_alpha:
            flag = "U"
        elif value >= old_beta:
            flag = "L"
        else:
            flag = "E"
        self.tt_store(position, value, best_move, flag, depth)

        return value, best_move

    def iterative_deepening(self, position: Position):
        """
        This function implements iterative deepening. The AI searches at depth 1,2,...
        until it reaches MIN_SEARCH_DEPTH. At this point it keeps searching deeper until
        it runs out of time (as defined by MILLISECONDS_PER_MOVE). All search stops however
        (even if MIN_SEARCH_DEPTH has not been reached) if calculation time exceeds
        MAX_MILLISECONDS_PER_MOVE. The function returns the last value and move found, along
        with the depth at which they were found.
        """
        search_depth = 1
        self.min_search_depth_reached = False
        self.search_start_time = milliseconds(time.time())
        while True:
            if search_depth > MIN_SEARCH_DEPTH:
                self.min_search_depth_reached = True
            try:
                value, best_move = self.alpha_beta(
                    position,
                    search_depth,
                    -inf,
                    inf,
                )
            except ABTimeOut:
                break
            prev_search_depth, prev_value, prev_best_move = (
                search_depth,
                value,
                best_move,
            )
            search_depth += 1

        return prev_search_depth, prev_value, prev_best_move

    def suggested_move(self, position: Position):
        """
        A function that returns the best move found by Alpha-Beta and prints
        some relevant data, such as the current evaluation and the Alpha-Beta
        evaluation of the position.
        """
        # If there is only one legal move, return it without searching
        origin, targets = (
            next(iter(position.all_legal_moves.items()))
            if len(position.all_legal_moves) == 1
            else (None, None)
        )
        if targets and len(targets) == 1:
            target = next(iter(targets))
            tag = targets[target]
            depth = "0 (one legal move)"
            value = position.evaluate()
            unique_move = True
        else:
            depth, value, (origin, target, tag) = self.iterative_deepening(position)
            unique_move = False
        print(f"Alpha-Beta evaluation: {value} at depth {depth}")
        return origin, target, tag, unique_move
