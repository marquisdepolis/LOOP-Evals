# %%
import os
import re
import json
import openai
import enchant
from dotenv import load_dotenv
load_dotenv()
from llms.llms import llm_call_gpt_json, llm_call_claude, llm_call_ollama_json
from utils.retry import retry_except

openai.api_key = os.getenv("OPENAI_API_KEY")
with open('info.json', 'r') as file:
    data = json.load(file)

instructions = data.get('instructions_wg')
small_change = data.get('small_change_wg')
GPT = data.get('GPT_MODEL')
ATTEMPTS = 50
TURNS = 10
CLAUDE = data.get('CLAUDE')
OLLAMA = data.get('OLLAMA')

def get_llm_response(input_str, llm_type='openai'):
    if llm_type == 'openai':
        return llm_call_gpt_json(input_str, GPT)
    elif llm_type == 'claude':
        return llm_call_claude(input_str, CLAUDE)
    elif llm_type == 'ollama':
        return llm_call_ollama_json(input_str, OLLAMA)
    
def create_word_matrix(objective):
    """Generate a matrix of words, starting with 'C' and ending with 'N'."""
    response = get_llm_response(f"""
                        {instructions}. Objective is: {objective}. The words have to be valid English words when read across the rows and also when read down the columns. This is very important, think quietly first. Reply with only the list of words, as follows. Ensure you reply with the correct number of words and in the correct order. For example:
                        '''
                        Word, Word, Word etc
                        '''
    """)
    return response

def check_word_validity(word):
    """
    Check if a word is a valid English word using pyenchant.
    """
    d = enchant.Dict("en_US")  # or "en_GB" for British English
    return d.check(word)

def preprocess_json_string(response):
    """
    Preprocesses the response string to fix common JSON formatting issues.
    This can include removing extra commas, fixing array formatting, etc.
    """
    # Example fix: Remove trailing commas before closing brackets or braces
    response = re.sub(r',(?=\s*[}\]])', '', response)
    return response

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError, ValueError), tries=3, delay=2)
def extract_words_from_matrix(response):
    """
    Enhanced parsing function to extract words from a JSON response that may contain
    various structures or formatting issues.
    """
    print(f"Raw response is: {response}")
    response = preprocess_json_string(response)  # Preprocess the response string
    
    try:
        response_json = json.loads(response)
        
        # Dynamically identify and extract the word list from the JSON, handling various cases
        word_list = None
        for value in response_json.values():
            if isinstance(value, list):
                word_list = value  # Direct list of words or lists
                break
            elif isinstance(value, str):
                word_list = value.split(", ")  # Single string of comma-separated words
                break
        
        if not word_list:
            print("No suitable word list found in the response.")
            return []

        # If the word list is a list of lists (nested), flatten it
        if any(isinstance(i, list) for i in word_list):
            words = [word for sublist in word_list for word in sublist]
        else:
            words = word_list

        # Clean and validate the words
        words = [word.strip().replace('"', '').replace("'", "") for word in words]  # Strip and remove quotes
        return words

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from response: {e}. Check the response format.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
    
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
    Objective is: {objective}. The words have to be valid English words when read across the rows and also when read down the columns. This is very important. Think quietly first. Ensure to maintain the matrix's integrity. Ensure you reply with the correct number of words and in the correct order. Reply with only the final list of words, as follows:
    '''
    Word, Word, Word etc.
    '''
    """
    response = get_llm_response(regeneration_prompt)
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

    cleanup()

def cleanup():
    archive_folder_path = '#Archive/'
    os.makedirs(archive_folder_path, exist_ok=True)
    os.makedirs('results', exist_ok=True)
    file_paths = [
        'results_objective_3.json',
        'results_objective_4.json',
        'results_objective_5.json'
    ]

    # Initialize a dictionary to hold all results
    combined_results = {}

    # Loop through each file, load its content, and add it to the combined results
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            data = json.load(file)
            objective_number = file_path.split('_')[-1].split('.')[0]
            combined_results[f'matrix_{objective_number}'] = data
        os.rename(file_path, archive_folder_path + os.path.basename(file_path))

    # Write the combined results to a new file
    combined_results_path = 'results/results_wg.json'
    with open(combined_results_path, 'w') as file:
        json.dump(combined_results, file, indent=4)

if __name__ == "__main__":
    repeatedly_run_main()
