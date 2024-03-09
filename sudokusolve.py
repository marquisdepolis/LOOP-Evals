from pysat.formula import CNF
from pysat.solvers import Glucose3
from puzzles.sudokugen import generate_sudoku, is_valid_move, find_empty_location

def transpose(grid):
    return [list(row) for row in zip(*grid)]

def encode_sudoku(sudoku):
    cnf = CNF()

    # Encode each cell contains at least one number [1-9]
    for r in range(1, 10):
        for c in range(1, 10):
            cnf.append([9 * (r - 1) + 9 * 9 * (c - 1) + n for n in range(1, 10)])

    # Rows, columns, and blocks contain no repeated numbers
    for n in range(1, 10):
        for r in range(1, 10):
            for c1 in range(1, 10):
                for c2 in range(c1 + 1, 10):
                    cnf.append([-1 * (9 * (r - 1) + 9 * 9 * (c1 - 1) + n), -1 * (9 * (r - 1) + 9 * 9 * (c2 - 1) + n)])
                    
        for c in range(1, 10):
            for r1 in range(1, 10):
                for r2 in range(r1 + 1, 10):
                    cnf.append([-1 * (9 * (r1 - 1) + 9 * 9 * (c - 1) + n), -1 * (9 * (r2 - 1) + 9 * 9 * (c - 1) + n)])
                    
        for block in range(9):
            cells = []
            start_row = 3 * (block // 3)
            start_col = 3 * (block % 3)
            for r in range(1, 4):
                for c in range(1, 4):
                    cells.append((start_row + r, start_col + c))
            for i in range(9):
                for j in range(i + 1, 9):
                    r1, c1 = cells[i]
                    r2, c2 = cells[j]
                    cnf.append([-1 * (9 * (r1 - 1) + 9 * 9 * (c1 - 1) + n), -1 * (9 * (r2 - 1) + 9 * 9 * (c2 - 1) + n)])

    # Encode known values from the puzzle
    for r in range(9):
        for c in range(9):
            n = sudoku[r][c]
            if n:
                cnf.append([9 * r + 9 * 9 * c + n])

    return cnf

def decode_solution(model):
    solution = [[0 for _ in range(9)] for _ in range(9)]
    for var in model:
        if var > 0:
            var -= 1  # Adjusting 1-based indexing
            n = 1 + var % 9
            var //= 9
            c = var % 9
            var //= 9
            r = var
            solution[r][c] = n
    return solution

def detailed_reasoning_before_placement(board, row, col, num, depth):
    """
    Simulates reasoning for why a specific number is chosen for a cell before actually placing it.
    This function mimics a thought process considering Sudoku rules.
    """
    valid_move = True  # Assume the move is valid until proven otherwise

    # Check if placing 'num' in (row, col) violates Sudoku rules
    reasons = []
    # Row and column check
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            valid_move = False
            reasons.append(f"{'    ' * (depth + 1)}Invalid: {num} already in row {row+1} or column {col+1}.")
            break

    # Subgrid check
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                valid_move = False
                reasons.append(f"{'    ' * (depth + 1)}Invalid: {num} already in the 3x3 subgrid.")
                break

    if valid_move:
        print(f"{'    ' * (depth + 1)}Valid choice: No conflicts detected for {num}.")
    else:
        for reason in reasons:
            print(reason)
    
    return valid_move

def solve_sudoku_with_explanation(board, depth=0):
    '''
    Backtracking type constraint solution to figure out how to solve a sudoku.Ca
    '''
    empty_cell = find_empty_location(board)
    if not empty_cell:
        print(f"{'    ' * depth}Puzzle solved successfully.")
        return True  # Puzzle solved
    
    row, col = empty_cell
    print(f"{'    ' * depth}Looking for a number to place in cell ({row+1}, {col+1}):")
    
    for num in range(1, 10):
        if is_valid_move(board, row, col, num):
            print(f"{'    ' * depth}=> Trying {num} at ({row+1}, {col+1}):")
            
            # Explain why this number can be placed here (before actually placing it)
            if not detailed_reasoning_before_placement(board, row, col, num, depth):
                continue  # Skip to the next number if the current one doesn't fit logically
            
            board[row][col] = num
            print(f"{'    ' * (depth + 1)}Placed {num} at ({row+1}, {col+1}).")
            
            if solve_sudoku_with_explanation(board, depth + 1):
                return True
            
            # Backtrack
            print(f"{'    ' * (depth + 1)}Backtracking: Removing {num} from ({row+1}, {col+1}).")
            board[row][col] = 0
    
    if depth == 0:
        print("No valid number found for any cell, backtracking...")
    return False

# Generate a Sudoku puzzle with cells randomly removed -- highest poss is 64 currently
if __name__ == "__main__":
    sudoku = generate_sudoku(45)
    print("Generated Sudoku Puzzle:")
    for row in sudoku:
        print(row)
    print("\n")

    # Backtracking Solver with Explanations (Interactive Mode)
    print("\nStarting to solve with detailed explanations...")
    solved = solve_sudoku_with_explanation(sudoku)

    if solved:
        print("\nSudoku Puzzle Solved Successfully:")
        for row in sudoku:
            print(row)
    else:
        print("\nFailed to solve the Sudoku puzzle.")

    print("\nSolving with SAT Solver:")
    cnf = encode_sudoku(sudoku)
    solver = Glucose3()
    solver.append_formula(cnf)
    if solver.solve():
        model = solver.get_model()
        solution = decode_solution(model)
        solution = transpose(solution) # Because somehow I swtiched row and columns around
        print("\nSAT Solver Solution")
        for row in solution:
            print(row)
    else:
        print("No solution found, sorry!")
