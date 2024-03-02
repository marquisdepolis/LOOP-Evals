# %%
import os
import re
import json
import openai
import enchant
from dotenv import load_dotenv
load_dotenv()
from llms.gpt import llm_call
from utils.retry import retry_except

openai.api_key = os.getenv("OPENAI_API_KEY")
with open('info.json', 'r') as file:
    data = json.load(file)

instructions = data.get('instructions')
small_change = data.get('small_change')
GPT = data.get('GPT_4')
ATTEMPTS = 50
TURNS = 10

def create_word_matrix(objective):
    """Generate a matrix of words, starting with 'C' and ending with 'N'."""
    response = llm_call(f"""
                        {instructions}. Objective is: {objective}. The words have to be valid English words when read across the rows and also when read down the columns. This is very important, think quietly first. Reply with only the list of words, as follows
                        ```
                        Word, Word, Word etc
                        ```
    """, GPT)
    return response

def check_word_validity(word):
    """
    Check if a word is a valid English word using pyenchant.
    """
    d = enchant.Dict("en_US")  # or "en_GB" for British English
    return d.check(word)

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError, ValueError), tries=3, delay=2)
def extract_words_from_matrix(response):
    """
    Parses the response to extract and create a list of words,
    """
    print(f"\nRaw response: {response}")  # Add this line to debug
    cleaned_response = response.replace('```', '').replace('\n', '').replace("'''", '').strip()
    
    print(f"\nCleaned response: {cleaned_response}")  # Debugging line to check the cleaned response
    words_list = [word.strip() for word in cleaned_response.split(",")]
    try:
        # Ensure all words have the same length
        word_lengths = [len(word) for word in words_list]
        if len(set(word_lengths)) > 1:
            print("Words have varying lengths, which is not allowed for a valid matrix.")

        matrix = [list(word) for word in words_list]
        row_words = words_list
        num_rows = len(matrix)
        num_cols = len(matrix[0]) if num_rows > 0 else 0

        # Generate column words based on the actual size of the matrix
        column_words = [''.join(matrix[row][col] for row in range(num_rows)) for col in range(num_cols)]
    
    except IndexError:
        # Handle the error or skip
        print("An IndexError occurred. Skipping problematic operation.")
        column_words = []  # Set to an empty list or another default value

    all_words = row_words + column_words
    print(f"\n\n All words are {all_words}")
    # print(f"Total number of words are {sum(all_words)}")
    return all_words

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def check_words_validity(words):
    """
    Checks the validity of each word in the list of words.
    Returns a dictionary with words as keys and their validity as boolean values.
    """
    words_validity = {word: check_word_validity(word.lower()) for word in words}
    # Check if the first word starts with 'C'
    if words and not words[0].startswith('C'):
        words_validity[words[0]] = False  # Mark as invalid
    
    # Check if the last word ends with 'N'
    if words and not words[-1].endswith('N'):
        words_validity[words[-1]] = False  # Mark as invalid
    
    # Check if all words have the same length
    word_lengths = [len(word) for word in words]
    if len(set(word_lengths)) > 1:
        # If there are varying lengths, mark all as invalid for simplicity
        for word in words:
            words_validity[word] = False
    invalid_words_count = sum(not validity for validity in words_validity.values())
    print(f"Validity measurement is {words_validity}")
    print(f"Number of invalid words: {invalid_words_count}\n\n")
    return words_validity

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def regenerate_invalid_words(invalid_words, original_matrix, objective):
    # Construct a prompt to regenerate only the invalid words, using the original matrix as context
    regeneration_prompt = f"""
    {small_change}. You had generated an original matrix of words:
    {original_matrix}. But this contained invalid words {invalid_words} when read across rows and columns. Let's fix this.
    Objective is: {objective}. The words have to be valid English words when read across the rows and also when read down the columns. This is very important, think quietly first. Ensure to maintain the matrix's integrity. Reply with only the list of words, as follows
    ```
    Word, Word, Word etc.
    ```
    """
    response = llm_call(regeneration_prompt, GPT)
    return response

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def main(attempt_number, objective):
    results = {
        'attempt_number': attempt_number,  # Log the attempt number
        'runs': [],  # Changed to 'runs' to store results of each run
        'success': False
    }
    attempt_count = 0
    max_attempts = TURNS
    
    for attempt_count in range(1, max_attempts + 1):
        attempt_data = {
            'index': attempt_count,
            'matrix': None,
            'word_responses': None,
            'false_count': None,
            'error': None
        }

        try:
            response = create_word_matrix(objective) if attempt_count == 1 else regenerate_invalid_words(invalid_words_list, original_matrix, objective)

            words = extract_words_from_matrix(response)
            all_words_validity = check_words_validity(words)

            invalid_words_count = sum(not validity for validity in all_words_validity.values())

            attempt_data['matrix'] = words
            attempt_data['word_responses'] = list(all_words_validity.keys())
            attempt_data['false_count'] = invalid_words_count

            invalid_words_list = [word for word, isValid in all_words_validity.items() if not isValid]

            if not invalid_words_list:
                results['success'] = True
                # Break the loop if successful
            else:
                original_matrix = response  # Save for regeneration context
        except ValueError as ve:
            print(f"A ValueError occurred: {ve}. Continuing with the next attempt...")
            words = extract_words_from_matrix(response)
            all_words_validity = check_words_validity(words)
            invalid_words_list = [word for word, isValid in all_words_validity.items() if not isValid]
            
            attempt_data['error'] = str(ve)  # Log the specific error that occurred
            attempt_data['matrix'] = words if 'words' in locals() else "Error occurred before matrix formation"
            attempt_data['word_responses'] = list(all_words_validity.keys()) if 'all_words_validity' in locals() else "Error occurred before validity checking"
            attempt_data['false_count'] = invalid_words_count if 'invalid_words_count' in locals() else "Error occurred before false count calculation"

        results['runs'].append(attempt_data)  # Add attempt data to results regardless of success/failure

        if results['success']:
            break  # Exit the loop if successful

    if not results['success']:
        print("Failed to generate a fully valid matrix within the maximum attempt limit.")

    return results
 
def repeatedly_run_main():
    objective_keys = ['objective_3', 'objective_4', 'objective_5']  # Directly use the keys
    for objective_key in objective_keys:
        objective_description = data.get(objective_key)
        all_results = []
        successful = False
        for attempt in range(1, ATTEMPTS + 1):
            print(f"Global Attempt {attempt} of {ATTEMPTS} for {objective_key}...")
            # Now passing both the key and description to main
            results = main(attempt, objective_description)
            
            successful = results.get('success', False)
            all_results.append(results)
            
            if successful:
                print(f"Successfully generated a valid matrix for {objective_key}. Exiting...")
                break
            else:
                print("Attempt unsuccessful.")
        
        # Write results after all attempts for an objective are completed
        with open(f'results_{objective_key}.json', 'w') as file:
            json.dump(all_results, file, indent=4)
        
        if not successful:
            print(f"Reached maximum attempt limit without success for {objective_key}. Exiting...")

if __name__ == "__main__":
    repeatedly_run_main()
