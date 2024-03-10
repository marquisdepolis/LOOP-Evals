import enchant
import random

def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip().lower() for line in file if len(line.strip()) == 5]
    return words

def colorize_guess(guess, target):
    result = ['_'] * 5  # Placeholder for coloring: '_' = not guessed, 'G' = green, 'Y' = yellow
    target_tmp = list(target)  # Temp copy to mark letters as used
    print(f"Placeholder for coloring: '_' = not guessed, 'G' = green, 'Y' = yellow: {target_tmp}")
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

def play_wordle(file_path):
    words = load_words(file_path)
    target = random.choice(words)
    attempts = 1

    print("Welcome to WORDLE (Python Edition). Guess the 5-letter word!")
    print("Type 'exit' to quit the game.")

    while attempts < 5:
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

if __name__ == '__main__':
    play_wordle('puzzles/wordle.txt')
