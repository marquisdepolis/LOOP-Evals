import os
import json
import openai
import enchant
import random
from dotenv import load_dotenv
load_dotenv()
from llms.gpt import llm_call_json
from utils.retry import retry_except

openai.api_key = os.getenv("OPENAI_API_KEY")
with open('info.json', 'r') as file:
    data = json.load(file)

instructions = data.get('instructions_w')
objective = data.get('objective_w')
GPT = data.get('GPT_4')

def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip().lower() for line in file if len(line.strip()) == 5]
    return words

def colorize_guess(guess, target):
    result = ['_'] * 5  # Placeholder for coloring: '_' = not guessed, 'G' = green, 'Y' = yellow
    target_tmp = list(target)  # Temp copy to mark letters as used
    # First pass for correct positions
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = 'G'
            target_tmp[i] = None  # Mark as used
    
    # Second pass for correct letters in wrong positions
    for i in range(5):
        if guess[i] != target[i] and guess[i] in target_tmp:
            result[i] = 'Y'
            target_tmp[target_tmp.index(guess[i])] = None  # Mark as used
    
    # Convert result to colored string or another representation for CLI
    return ''.join(result)
    colored_result = ''
    for i in range(5):
        if result[i] == 'G':
            colored_result += f'\033[92m{guess[i]}\033[0m'  # Green
        elif result[i] == 'Y':
            colored_result += f'\033[93m{guess[i]}\033[0m'  # Yellow
        else:
            colored_result += guess[i]  # No color for incorrect letters
    return colored_result

def check_word_validity(word):
    """
    Check if a word is a valid English word using pyenchant.
    """
    d = enchant.Dict("en_US")  # or "en_GB" for British English
    return d.check(word)

def play_wordle_user(file_path):
    words = load_words(file_path)
    target = random.choice(words)
    attempts = 0
    max_attempts = 6

    print("Welcome to WORDLE (Python Edition). Guess the 5-letter word!")
    print("Type 'exit' to quit the game.")

    while attempts < max_attempts:
        guess = input(f"Enter your guess: Attempt number ({attempts}): ").strip().lower()
        if guess == 'exit':
            print("Game exited. Thanks for playing!")
            return
        if len(guess) != 5 or not guess.isalpha():
            print("Invalid input. Please enter a 5-letter word.")
            continue
        if guess not in words:
            print("Word not in list. Try again.")
            continue
        
        attempts += 1
        colored_guess = colorize_guess(guess, target)
        print("Feedback on your guess: ", colored_guess)
        
        if guess == target:
            print("Congratulations! You've guessed the word correctly.")
            return
        elif attempts == 0:
            print(f"Game over. The correct word was '{target}'.")
            return

def check_word_validity(word):
    """
    Check if a word is a valid English word using pyenchant.
    """
    d = enchant.Dict("en_US")  # or "en_GB" for British English
    return d.check(word)

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError, ValueError), tries=3, delay=2)
def extract_word(response):
    """
    Parses the response to extract the word.
    """
    print(f"\nRaw response: {response}")  # Add this line to debug
    cleaned_response = response.replace('```', '').replace('\n', '').replace("'''", '').strip()
    
    print(f"\nCleaned response: {cleaned_response}")  # Debugging line to check the cleaned response
    return cleaned_response

def play_wordle(file_path):
    words = load_words(file_path)
    target = random.choice(words)
    attempts = 0
    max_attempts = 6

    print("Welcome to WORDLE (Python Edition). Guessing the 5-letter word!")

    while attempts < max_attempts:
        guess = llm_call_json(f"""{instructions}. {objective}. Only return the word inside a docstring, like:   
                              '''WORD
                              '''
                              """,GPT).strip().lower()
        guess = extract_word(guess)
        words_validity = check_word_validity(guess.lower())
        print(f"The validity of the word is: {words_validity}")
        if len(guess) != 5 or not guess.isalpha():
            print("Invalid input. Please enter a 5-letter word.")
            continue
        if guess not in words:
            print("Word not in list. Try again.")
            continue

        attempts += 1
        colored_guess = colorize_guess(guess, target)
        print("Feedback on your guess: ", colored_guess)

        guess = llm_call_json(f"""{instructions}. {objective}. You are given feedback on the positions according to {colored_guess}. G means the position is correct and letter is correct. Y means letter is correct but position is wrong. Your input guess was {guess}. Now think and write what the correct answer should be as one word. Only return the word inside a docstring, like:
                              '''
                              WORD
                              '''
                              """,GPT).strip().lower()

        if guess == target:
            print("Congratulations! You've guessed the word correctly.")
            return
        elif attempts == 0:
            print(f"Game over. The correct word was '{target}'.")
            return
        
if __name__ == '__main__':
    play_wordle('puzzles/wordle.txt')
