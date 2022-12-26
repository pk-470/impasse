from impasse.constants import *


class Position:
    """
    A class to keep track of each position along with its available moves,
    and to calculate the effect of a move on a position.
    """

    def __init__(
        self,
        state=None,
        turn=None,
        checkers_total=None,
        all_legal_moves=None,
        winner=None,
        state_hash=None,
    ):
        self.make_position(
            state, turn, checkers_total, all_legal_moves, winner, state_hash
        )

    def make_position(
        self,
        state=None,
        turn=None,
        checkers_total=None,
        all_legal_moves=None,
        winner=(),
        state_hash=None,
    ):
        """
        Initialises the position based on the input data. If all data is given, then it is
        passed along to the relevant attributes. If only a state and whose turn it is are given,
        the rest of the data is calculated on the spot. If no data is given, a starting position
        is created.
        """
        self.state = INITIAL_STATE.copy() if state is None else state
        self.turn = WHITE if turn is None else turn
        self.all_legal_moves = (
            self.get_all_legal_moves() if all_legal_moves is None else all_legal_moves
        )
        self.checkers_total = (
            {WHITE: 12, BLACK: 12}
            if state is None
            else checkers_total
            if checkers_total
            else self.count_checkers()
        )
        self.winner = (
            None
            if state is None
            else winner
            if winner in (WHITE, BLACK, None)
            else WHITE
            if not self.checkers_total[WHITE]
            else BLACK
            if not self.checkers_total[BLACK]
            else None
        )
        self.state_hash = state_hash if state_hash else make_state_hash(self.state)

    def count_checkers(self):
        """
        Returns a dictionary containing the number of checkers for each
        player in the current position.
        """
        white, black = 0, 0
        for cell in self.state:
            cell_color, cell_type = self.state[cell]
            if cell_color == WHITE:
                white += cell_type
            else:
                black += cell_type

        return {WHITE: white, BLACK: black}

    def copy(self):
        """
        Returns a copy of the current position.
        """
        state = self.state.copy()
        checkers_total = self.checkers_total.copy()
        all_legal_moves = {
            cell: self.all_legal_moves.copy() for cell in self.all_legal_moves
        }
        return Position(
            state,
            self.turn,
            checkers_total,
            all_legal_moves,
            self.winner,
            self.state_hash,
        )

    # Some shortcuts for various checks

    def is_valid(self, cell):
        return cell in self.state

    def is_occupied(self, cell):
        return cell in self.state and self.state[cell] is not None

    def is_single(self, cell):
        return self.state[cell][1] == 1

    def is_of_color(self, cell, color):
        return self.state[cell][0] == color

    def is_occupied_of_color(self, cell, color):
        return (
            cell in self.state
            and self.state[cell] is not None
            and self.state[cell][0] == color
        )

    def is_occupied_single_of_color(self, cell, color):
        return cell in self.state and self.state[cell] == (color, 1)

    # Impasse game functions

    def get_slides(self, origin):
        """
        Input:
            - origin (tuple)

        Returns:
            - slides (dictionary)
                Each key in slides is a cell in which origin can move.
                The corresponding value is one of:
                    - "S" : indicates a regular slide;
                    - "SB" : indicates a slide which places a crown at its
                        home row, thus leading to a bear off;
                    - "SC" : indicates a slide which places a single at its
                        furthest row, thus making crowning possible.
        """
        slides = {}
        for direction in MOVE_DIRECTIONS[self.state[origin]]:
            for candidate in DIAGONALS[(origin, direction)]:
                if self.is_occupied(candidate):
                    break
                else:
                    # Slide leading to bear off
                    if candidate in HOME_ROW[self.turn]:
                        slides[candidate] = "SB"
                    # Slide leading to available crowning
                    elif candidate in HOME_ROW[
                        OPPOSITE_COLOR[self.turn]
                    ] and self.is_single(origin):
                        slides[candidate] = "SC"
                    # Regular slide
                    else:
                        slides[candidate] = "S"

        return slides

    def get_transposes(self, origin):
        """
        Input:
            - origin (tuple)

        Returns:
            - transposes (dictionary):
                Each key in transposes is a cell in which origin can transpose.
                The corresponding value is one of:
                    - "T" : indicates a regular transpose;
                    - "TB" : indicates a transpose which places a crown
                        at its home row, leading to a bear off;
                    - "TC" : indicates a transpose which leaves a single
                        at its furthest row, thus making crowning possible.

        """
        transposes = {}
        for direction in MOVE_DIRECTIONS[self.state[origin]]:
            candidate = (origin[0] + direction[0], origin[1] + direction[1])
            if self.is_occupied_single_of_color(candidate, self.turn):
                # Transpose leading to bear off
                if candidate in HOME_ROW[self.turn]:
                    transposes[candidate] = "TB"
                # Transpose leading to available crowning
                elif origin in HOME_ROW[OPPOSITE_COLOR[self.turn]]:
                    transposes[candidate] = "TC"
                # Regular transpose
                else:
                    transposes[candidate] = "T"

        return transposes

    def get_singles_except(self, target):
        """
        Input:
            - target (tuple)

        Returns:
            - a list of all cells other than target containing a single friendly checker.
        """
        return [
            cell
            for cell in self.state
            if cell != target and self.is_occupied_single_of_color(cell, self.turn)
        ]

    def get_crownings(self):
        """
        Returns all available crownings in a dictionary with entries of the form
        'origin: crownings', in which 'crownings' is a dictionary with entries of the
        form 'target: "C"', where 'target' is a cell with a checker that needs to be
        crowned and "C" denotes that the move is a crowning, while 'origin' is a cell
        containing a single checker that can be used for the crowning of 'target'.
        """
        crownings = {}
        for target in HOME_ROW[OPPOSITE_COLOR[self.turn]]:
            if self.is_occupied(target) and self.state[target] == (self.turn, 1):
                crownings.update(
                    {cell: {target: "C"} for cell in self.get_singles_except(target)}
                )

        return crownings

    def get_other_moves(self):
        """
        Gets all available moves other than crownings. Returns a dictionary with
        entries of the form 'origin: moves', where 'moves' is a dictionary with
        entries of the form 'target: tag', where 'target' is a cell at which
        'origin' can move ('target' is None for bear offs) and 'tag' is the
        corresponding move tag (one of "S", "SB", "SC", "T" "TB", "TC", "B").
        """
        other_moves = {}
        for cell in self.state:
            if self.is_occupied_of_color(cell, self.turn):
                if self.state[cell][1] == 1:
                    # Get slides for singles
                    moves = self.get_slides(cell)
                else:
                    # Get transposes and slides for crowns
                    moves = self.get_transposes(cell) | self.get_slides(cell)
                if moves:
                    other_moves[cell] = moves
        # Impasse
        if not other_moves:
            return {
                cell: {None: "B"}
                for cell in self.state
                if self.is_occupied_of_color(cell, self.turn)
            }
        return other_moves

    def get_all_legal_moves(self):
        """
        Returns all legal moves in the position. If there are available crownings then
        it only returns those, otherwise it returns all other legal moves.
        """
        if crownings := self.get_crownings():
            return crownings
        return self.get_other_moves()

    def apply_move(self, origin, target, tag):
        """
        Input:
            - origin (tuple)
            - target (tuple)
            - tag (string)

        Returns:
            - state_update (dictionary):
                The part of the state dictionary that needs to be changed if a move
                described by origin, target and tag is applied on the current state.
        """
        origin_type = self.state[origin][1]
        # Slide
        if tag in ("S", "SC"):
            state_update = {origin: None, target: (self.turn, origin_type)}
        # Slide + Bear off
        elif tag == "SB":
            state_update = {origin: None, target: (self.turn, 1)}
        # Transpose
        elif tag in ("T", "TC"):
            state_update = {origin: (self.turn, 1), target: (self.turn, 2)}
        # Transpose + Bear off
        elif tag == "TB":
            state_update = {origin: (self.turn, 1), target: (self.turn, 1)}
        # Crowning
        elif tag == "C":
            state_update = {origin: None, target: (self.turn, 2)}
        # Bear off
        elif tag == "B":
            if origin_type == 1:
                state_update = {origin: None}
            else:
                state_update = {origin: (self.turn, 1)}

        return state_update

    def change_turn(self):
        """
        Change turn and find the new legal moves.
        """
        self.turn = OPPOSITE_COLOR[self.turn]
        self.all_legal_moves = self.get_other_moves()

    def check_for_crownings_and_change_turn(self):
        """
        Check for available crownings. If any are found then
        update the legal moves, otherwise change turn.
        """
        if crownings := self.get_crownings():
            self.all_legal_moves = crownings
        else:
            self.change_turn()

    def update(self, state_update, tag):
        """
        Updates the position data according to the state_update
        and the tag of the move that led to it.
        """
        old_state = {cell: self.state[cell] for cell in state_update}
        self.state_hash ^= make_state_hash(old_state)
        self.state_hash ^= make_state_hash(state_update)
        self.state.update(state_update)
        # Bear off
        if tag == "B":
            self.checkers_total[self.turn] -= 1
            # Check for win
            if not self.checkers_total[self.turn]:
                self.winner = self.turn
            # Might make crowning possible
            else:
                self.check_for_crownings_and_change_turn()
        # Slide + Bear off
        elif tag == "SB":
            self.checkers_total[self.turn] -= 1
            # Might make crowning possible
            self.check_for_crownings_and_change_turn()
        # Transpose + Bear off
        elif tag == "TB":
            self.checkers_total[self.turn] -= 1
            self.change_turn()
        # Potential crowning
        elif tag in ("SC", "TC"):
            self.check_for_crownings_and_change_turn()
        # Change turn after crowning or regular slide or
        # regular transpose
        elif tag in ("C", "S", "T"):
            self.change_turn()

    def new_position_after_move(self, origin, target, tag):
        """
        Returns a new Position object derived from applying a move
        on the current state.
        """
        new_position = self.copy()
        state_update = new_position.apply_move(origin, target, tag)
        new_position.update(state_update, tag)
        return new_position

    def path_to_bear_off(
        self,
        color,
        start,
        anchor_cell,
        i,
        doubles_with_paths,
        steps,
        prev_empty,
        changed_dir,
    ):
        """
        A recursive function that finds the shortest path from start (a cell
        containing a double checker) to bear off, if such a path exists.
        """
        d = MOVE_DIRECTIONS[(color, 2)][i]
        for cell in DIAGONALS[(anchor_cell, d)]:
            if not self.is_occupied(cell):
                # A step is added if we move from a single
                # to an empty cell
                if not prev_empty:
                    steps += 1
                    prev_empty = True
                changed_dir = False
                # Add one step before changing direction
                new_steps = steps + 1
            elif self.is_occupied_single_of_color(cell, color):
                # A step is added if we encounter a single cell
                # unless it is after changing direction at an empty
                # cell (since then we have already added a step)
                if not (changed_dir and prev_empty):
                    steps += 1
                changed_dir = False
                prev_empty = False
                # Change direction without adding step
                new_steps = steps
            else:
                break

            # Add the shortest path to bear off found so far for
            # each double (converted into a score out of 10)
            if cell in HOME_ROW[color] and (
                start not in doubles_with_paths
                or (
                    start in doubles_with_paths
                    and DOUBLES_PATHS_MAX - steps > doubles_with_paths[start]
                )
            ):
                doubles_with_paths[start] = DOUBLES_PATHS_MAX - steps
                break

            # Change direction
            doubles_with_paths = self.path_to_bear_off(
                color,
                start,
                cell,
                1 - i,
                doubles_with_paths,
                new_steps,
                prev_empty,
                True,
            )

        return doubles_with_paths

    def path_to_crown(self, color, start, anchor_cell, i, singles_with_paths, steps):
        """
        A recursive function that finds the shortest path from start (a cell
        containing a single checker) to a crowning square, if such a path
        exists.
        """
        d = MOVE_DIRECTIONS[(color, 1)][i]
        for cell in DIAGONALS[(anchor_cell, d)]:
            if self.is_occupied(cell):
                break

            # Add the shortest path to bear off found so far for
            # each double (converted into a score out of 10)
            if cell in HOME_ROW[OPPOSITE_COLOR[color]] and (
                start not in singles_with_paths
                or (
                    start in singles_with_paths
                    and SINGLES_PATHS_MAX - steps > singles_with_paths[start]
                )
            ):
                singles_with_paths[start] = SINGLES_PATHS_MAX - steps

            # Change direction (add 1 to steps)
            singles_with_paths = self.path_to_crown(
                color,
                start,
                cell,
                1 - i,
                singles_with_paths,
                steps + 1,
            )

        return singles_with_paths

    def future_bear_offs_and_doubles(self, color):
        """
        Returns the score associated to all the possible future bear offs of a player,
        as well as the number of double checkers they have.
        """
        doubles = 0
        doubles_with_paths = {}
        for start in self.state:
            if self.is_occupied_of_color(start, color) and not self.is_single(start):
                doubles += 1
                for i in (0, 1):
                    doubles_with_paths = self.path_to_bear_off(
                        color, start, start, i, doubles_with_paths, 0, False, False
                    )

        return sum(doubles_with_paths.values()), doubles

    def future_crowns(self, color):
        """
        Returns the score associated to all the possible future crownings of a player.
        """
        singles_with_paths = {}
        for start in self.state:
            if self.is_occupied_single_of_color(start, color):
                for i in (0, 1):
                    singles_with_paths = self.path_to_crown(
                        color, start, start, i, singles_with_paths, 1
                    )

        return sum(singles_with_paths.values())

    def evaluate(self):
        """
        Returns an evaluation of the current state. The evaluation depends on
        the following features:
        - number of checkers of each player (if both players have the same
            number of pieces, the number of double pieces of each player is
            considered instead);
        - number and length of paths each player has towards bear-off;
        - number and length of paths each player has towards crowning.
        """
        if self.winner is not None:
            win_eval = 1000
            return win_eval if self.winner == WHITE else -win_eval
        dwpw, dw = self.future_bear_offs_and_doubles(WHITE)
        dwpb, db = self.future_bear_offs_and_doubles(BLACK)
        checkers_count = self.checkers_total[BLACK] - self.checkers_total[WHITE]
        if checkers_count:
            value = CHECKERS_COUNT_WEIGHT * checkers_count
        else:
            value = DOUBLES_WEIGHT * (dw - db)
        doubles_path_score = dwpw - dwpb
        singles_path_score = self.future_crowns(WHITE) - self.future_crowns(BLACK)
        value += (
            DOUBLES_PATHS_WEIGHT * doubles_path_score
            + SINGLES_PATHS_WEIGHT * singles_path_score
        )
        return value
