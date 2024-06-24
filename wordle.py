import os
import json
import openai
import enchant
import random
from dotenv import load_dotenv
load_dotenv()
from llms.llms import llm_call_gpt_json, llm_call_claude_json, llm_call_groq
from utils.retry import retry_except

openai.api_key = os.getenv("OPENAI_API_KEY")
with open('info.json', 'r') as file:
    data = json.load(file)

instructions = data.get('instructions_w')
objective = data.get('objective_w')
GPT = data.get('GPT_4')
CLAUDE = data.get('CLAUDE')
OLLAMA = data.get('OLLAMA')

def get_llm_response(input_str, llm_type='openai'):
    if llm_type == 'openai':
        return llm_call_gpt_json(input_str, GPT)
    elif llm_type == 'claude':
        return llm_call_claude_json(input_str, CLAUDE)
    elif llm_type == 'groq':
        return llm_call_groq(input_str)

def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip().lower() for line in file if len(line.strip()) == 5]
    return words

def colorize_guess(guess, target):
    """
    Generate a formatted feedback message for each operation.

    Parameters:
    - position: The position being analyzed or modified.
    - status: The status code or symbol (e.g., 'G' for correct, 'Y' for incorrect but close, etc.).
    - description: A descriptive message explaining the status.

    Returns:
    A formatted string with the feedback.
    """    
    GYs = []
    result = ['_'] * 5  # Placeholder for coloring: '_' = not guessed, 'G' = green, 'Y' = yellow
    target_tmp = list(target)  # Temp copy to mark letters as used
    feedback = []  # This will now hold dictionaries with position, letter, and feedback

    # First pass for correct positions
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = 'G'
            target_tmp[i] = None  # Mark as used
            feedback.append({'position': i, 'letter': guess[i], 'color': 'G'})  # Record the 'G' feedback with position
        else:
            feedback.append({'position': i, 'letter': guess[i], 'color': '_'})  # Placeholder
    
    # Second pass for correct letters in wrong positions
    for i in range(5):
        if guess[i] != target[i] and guess[i] in target_tmp:
            result[i] = 'Y'
            target_tmp[target_tmp.index(guess[i])] = None  # Mark as used
            feedback[i]['color'] = 'Y'  # Update the placeholder to 'Y'
    
    # Convert result to colored string or another representation for CLI
    GYs = ''.join(result)
    detailed_feedback = "\n".join([f"Position {item['position']+1}: {item['letter']} - {item['color']}" for item in feedback])
    # target_tmp = list(target)  # Temporary copy to mark letters as used
    
    # # First pass for correct positions
    # for i in range(5):
    #     if guess[i] == target[i]:
    #         feedback.append({'position': i+1, 'letter': guess[i], 'feedback': 'Correct position and letter (G)'})
    #         target_tmp[i] = None  # Mark as used
    #     else:
    #         feedback.append({'position': i+1, 'letter': guess[i], 'feedback': None})  # Placeholder

    # # Second pass for correct letters in wrong positions
    # for i in range(5):
    #     if feedback[i]['feedback'] is None:  # Only check letters not already marked as correct
    #         if guess[i] in target_tmp:
    #             feedback[i]['feedback'] = 'Correct letter, wrong position (Y)'
    #             target_tmp[target_tmp.index(guess[i])] = None  # Mark as used
    #         else:
    #             feedback[i]['feedback'] = 'Letter not in the word (_)'

    # # Format the feedback for display or further processing
    # feedback_details = "\n".join([f"Position {item['position']}: {item['letter']} - {item['feedback']}" for item in feedback])
    return GYs, detailed_feedback

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

def play_wordle(file_path, run_id, llm_type, results):
    words = load_words(file_path)
    target = random.choice(words)
    attempts = 0
    max_attempts = 5
    guess_history = []  # Initialize empty list to store history of guesses and feedback

    while attempts <= max_attempts:
        print(f"\n This is attempt number: {attempts}. \n")
        history_str = " ".join(guess_history)
        input_str = f"{instructions}. {objective}. Based on previous attempts: {history_str}. Only return the word."

        guess_response = get_llm_response(input_str, llm_type=llm_type)
        guess = extract_word(guess_response).strip().lower()
        
        words_validity = check_word_validity(guess)
        print(f"The validity of the word is: {words_validity}")
        if len(guess) != 5 or not guess.isalpha() or guess not in words:
            print("Invalid input or word not in list. Try again.")
            attempts += 1  # Increment the attempt counter to reflect the attempt
            if attempts >= max_attempts:  # Check if the maximum attempts have been reached
                print(f"Maximum attempts reached without guessing the word. The correct word was '{target}'.")
                break  # Exit the loop if the maximum attempts are reached break
            continue  # Continue to the next iteration of the loop

        attempts += 1
        GYs, feedback_details = colorize_guess(guess, target)
        print("Feedback on your guess: ", feedback_details)

        guess_history.append(f"Attempt {attempts}: {guess} - {feedback_details}")

        results.append({
            "Global attempt #": run_id,
            "Run #": attempts,
            "LLM type": llm_type,
            "Target word": target,
            "Guessed word": guess,
            "Number of 'G' in colorised results": GYs.count('G'),
            "Number of 'Y' in colorised results": GYs.count('Y'),
            "Feedback": feedback_details
        })

def main():
    runs = int(input("Enter the number of runs: "))
    results = []
    llm_types = ['claude', 'openai', 'groq']

    for run_id in range(1, runs + 1):
        for llm_type in llm_types:
            print(f"\n\n Starting run #{run_id}")
            play_wordle('puzzles/wordle.txt', run_id, llm_type, results)

    # Ensure the results directory exists
    os.makedirs('results', exist_ok=True)

    # Write results to file
    with open('results/results_wordle.json', 'w') as f:
        json.dump(results, f, indent=4)

    print("All runs completed. Results stored in 'results/results_wordle.json'.")

if __name__ == '__main__':
    main()
