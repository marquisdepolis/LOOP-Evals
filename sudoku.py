import os
import re
import json
import openai
import enchant
from dotenv import load_dotenv
load_dotenv()
from llms.llms import llm_call
from utils.retry import retry_except
from puzzles.sudokugen import generate_sudoku, is_valid_move, find_empty_location
from sudokusolve import encode_sudoku, decode_solution, transpose, solve_sudoku_with_explanation
from pysat.formula import CNF
from pysat.solvers import Glucose3

openai.api_key = os.getenv("OPENAI_API_KEY")
with open('info.json', 'r') as file:
    data = json.load(file)

instructions = data.get('instructions_wg')
objective = data.get('objective_s')
small_change = data.get('small_change_wg')
GPT = data.get('GPT_MODEL')
ATTEMPTS = 10
THRESHOLD = 10

def create_sudoku(sudoku, objective):
    """
    Generate a sudoku matrix.
    """
    response = llm_call(f"""
                        {instructions}. Objective is: {objective}. Given the following sudoku matrix, please analyse and reply with the number that would satisfy the answer. Sudoku is here: {sudoku}. Answer in the following format.
                        ```
                        Number, Number, etc
                        ```
    """, GPT)
    return response

def create_sudoku_row(sudoku, objective):
    """
    Generate a sudoku matrix.
    """
    response = []
    for row in sudoku:
        response_row = llm_call(f"""{instructions}. Objective is: {objective}. Given the following sudoku matrix, please analyse and reply with the number that would satisfy the answer. Sudoku is here: {sudoku}. Solve this row: {row}. Answer in the following format.
            ```
            Number, Number, etc
            ```
        """, GPT)
        response.append(response_row)
    return response

def solve_sudoku(board, replacements):
    replacement_queue = list(replacements)  # Queue of numbers to insert.
    print(replacement_queue)
    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] == 0:  # Found a blank space.
                if replacement_queue:
                    board[i][j] = replacement_queue.pop(0)  # Replace with the first number in the queue.
                else:
                    return "Not enough replacement numbers provided."
    if replacement_queue:
        return "Too many replacement numbers provided."
    return board

def parse_response_to_int_list(response):
    # Use regular expression to find all number sequences in the response.
    numbers = re.findall(r'\d+', response.strip("` \n"))
    # Convert found number strings to integers.
    return [int(num) for num in numbers]

def check_solution(sudoku):
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

def solve_row_by_row(sudoku, objective):
    final_solution = []
    for row_index, row in enumerate(sudoku):
        # Modify this prompt to ask for the solution of a single row, providing necessary context.
        response = create_sudoku(row, objective)  # Adjust this call as needed.
        row_solution = parse_response_to_int_list(response)
        if len(row_solution) != len(row):
            print(f"Error solving row {row_index + 1}: Response does not match row length.")
            return None
        final_solution.append(row_solution)
    return final_solution

def main():
    for puzzle_number in range(10, ATTEMPTS + 1):
        sudoku = generate_sudoku(puzzle_number)
        if puzzle_number <= THRESHOLD:
            pass
        else:
            # For puzzle numbers greater than 10, solve row by row.
            print(f"\n--- Puzzle {puzzle_number} (Row by Row) ---\n")
            response = create_sudoku_row(sudoku,objective)
            solved_board = solve_sudoku(sudoku, parse_response_to_int_list(response))
            for row in solved_board:
                print(row)
            check_solution(sudoku)

if __name__ == "__main__":
    main()
