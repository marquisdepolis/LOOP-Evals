import random

def is_valid_move(board, row, col, num):
    ''' 
    Check if the number is not repeated in the current row, column, and 3x3 subgrid.
    '''
    for x in range(9):
        if board[row][x] == num or board[x][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                return False
    return True

def solve_sudoku(board):
    empty_cell = find_empty_location(board)
    if not empty_cell:
        return True  # Puzzle solved
    row, col = empty_cell
    for num in range(1, 10):
        if is_valid_move(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            board[row][col] = 0  # Backtrack
    return False

def find_empty_location(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return i, j
    return None

def remove_numbers_from_board(board, num_remove):
    count = 0
    while count < num_remove:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        while board[row][col] == 0:  # Find a cell that is not already empty
            row = random.randint(0, 8)
            col = random.randint(0, 8)
        board[row][col] = 0
        count += 1

def generate_sudoku(num_remove):
    board = [[0 for _ in range(9)] for _ in range(9)]
    for i in range(1, 10):
        row, col = random.randint(0, 8), random.randint(0, 8)
        while not is_valid_move(board,row, col, i):
            row, col = random.randint(0, 8), random.randint(0, 8)
        board[row][col] = i
    solve_sudoku(board)
    remove_numbers_from_board(board, num_remove)
    return board

if __name__ == "__main__":
    sudoku = generate_sudoku(10)
    for row in sudoku:
        print(row)