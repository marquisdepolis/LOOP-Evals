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
    if not word:  # Check if the word is empty
        return False
    d = enchant.Dict("en_US")  # or "en_GB" for British English
    return d.check(word)

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError, ValueError), tries=3, delay=2)
def extract_word(response):
    """
    Parses the response to extract the word.
    """
    # print(f"\nRaw response: {response}")  # To debug
    try:
        parsed_response = json.loads(response)
        # If parsed_response is a dictionary, get the value of the first key
        if isinstance(parsed_response, dict):
            for key, value in parsed_response.items():
                # Assuming the value you are interested in is a string
                if isinstance(value, str):
                    cleaned_response = value.replace('```', '').replace('\n', '').replace("'''", '').strip()
                    print(f"\nExtracted value: {cleaned_response}")  # Debugging: Print the extracted value
                    return cleaned_response
            raise ValueError("No suitable string value was found in the response.")
        else:
            raise ValueError("The JSON response did not contain a dictionary as expected.")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from response: {e}")
        return ''
    except ValueError as e:
        print(f"ValueError: {e}")
        return ''

    return ''  # Return an empty string if no word is extracted

def play_wordle(file_path, run_id, results):
    words = load_words(file_path)
    target = random.choice(words)
    attempts = 0
    max_attempts = 6
    guess_history = []  # Initialize empty list to store history of guesses and feedback

    while attempts < max_attempts:
        print(f"\n This is attempt number: {attempts}. \n")
        history_str = " ".join(guess_history)
        input_str = f"{instructions}. {objective}. Based on previous attempts: {history_str}. Only return the word. Respond in json format."

        guess_response = llm_call_json(input_str, GPT)
        guess = extract_word(guess_response).strip().lower()
        
        words_validity = check_word_validity(guess)
        print(f"The validity of the word is: {words_validity}")
        if len(guess) != 5 or not guess.isalpha() or guess not in words:
            print("Invalid input or word not in list. Try again.")
            attempts += 1  # Increment the attempt counter to reflect the attempt
            if attempts >= max_attempts:  # Check if the maximum attempts have been reached
                print(f"Maximum attempts reached without guessing the word. The correct word was '{target}'.")
                break  # Exit the loop if the maximum attempts are reached
            continue  # Continue to the next iteration of the loop

        attempts += 1
        colored_guess = colorize_guess(guess, target)
        print("Feedback on your guess: ", colored_guess)

        guess_history.append(f"Attempt {attempts}: {guess} - {colored_guess}")

        # if guess == target or attempts == max_attempts:
        #     global_attempts = attempts if guess == target else -1  # -1 indicates failure to guess within max_attempts
        results.append({
            "Global attempt #": run_id,
            "Run #": attempts,
            "Target word": target,
            "Guessed word": guess,
            "Number of 'G' in colorised results": colored_guess.count('G'),
            "Number of 'Y' in colorised results": colored_guess.count('Y')
        })
        print(f"Results is: {results}")
        break

def main():
    runs = int(input("Enter the number of runs: "))
    results = []

    for run_id in range(1, runs + 1):
        print(f"\n\n Starting run #{run_id}")
        play_wordle('puzzles/wordle.txt', run_id, results)

    # Ensure the results directory exists
    os.makedirs('results', exist_ok=True)

    # Write results to file
    with open('results/results_wordle.json', 'w') as f:
        json.dump(results, f, indent=4)

    print("All runs completed. Results stored in 'results/results_wordle.json'.")

if __name__ == '__main__':
    main()
