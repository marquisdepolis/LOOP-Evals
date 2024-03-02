import json
import numpy as np
import matplotlib.pyplot as plt
import os

# Check if the folder exists, and if not, create it
os.makedirs('charts', exist_ok=True)
archive_folder_path = '#Archive/'
os.makedirs(archive_folder_path, exist_ok=True)

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
        # Extract objective number from the file name
        objective_number = file_path.split('_')[-1].split('.')[0]
        # Add this data to the combined results under a new key
        combined_results[f'matrix_{objective_number}'] = data
    
    # Move the file to the archive folder
    os.rename(file_path, archive_folder_path + os.path.basename(file_path))

# Write the combined results to a new file
combined_results_path = 'results_all.json'
with open(combined_results_path, 'w') as file:
    json.dump(combined_results, file, indent=4)

combined_results_path
with open(combined_results_path, 'r') as file:
    combined_data = json.load(file)

# Step 1: Load the JSON data
with open('results_all.json') as file:  # Ensure the correct path to 'results.json'
    data = json.load(file)

# Step 2: Analyze the data
# Compute success rate, average false counts, and collect all false counts for histogram
def compute_metrics(data):
    success_rate, avg_false_counts, all_false_counts = {}, {}, {'matrix_3': [], 'matrix_4': [], 'matrix_5': []}
    for matrix, details in data.items():
        successes = sum(1 for attempt in details if attempt['success'])
        total_attempts = len(details)
        success_rate[matrix] = successes / total_attempts if total_attempts else 0
        total_false_counts = sum(run['false_count'] for attempt in details for run in attempt['runs'])
        total_runs = sum(len(attempt['runs']) for attempt in details)
        avg_false_counts[matrix] = total_false_counts / total_runs if total_runs else 0
        all_false_counts[matrix].extend([run['false_count'] for attempt in details for run in attempt['runs']])
    return success_rate, avg_false_counts, all_false_counts

success_rates, avg_false_counts, all_false_counts = compute_metrics(combined_data)

# Success Rate and Average False Count by Matrix Size
plt.figure(figsize=(10, 5))
bar_positions = range(len(success_rates))
plt.bar(bar_positions, success_rates.values(), color='green', alpha=0.6, label='Success Rate')
plt.xticks(bar_positions, success_rates.keys())
plt.ylabel('Success Rate')
plt.twinx()
plt.plot(bar_positions, avg_false_counts.values(), color='red', marker='o', label='Avg False Count')
plt.ylabel('Average False Count')
plt.title('Success Rate and Average False Count by Matrix Size')
plt.legend()
plt.savefig(f'charts/successrates.png')

# Average False Counts per Attempt
plt.figure(figsize=(10, 5))
plt.plot(list(avg_false_counts.keys()), list(avg_false_counts.values()), marker='o')
plt.title('Average False Counts per Attempt')
plt.xlabel('Matrix Size')
plt.ylabel('Average False Count')
plt.grid(True)
plt.savefig(f'charts/avgfalsecounts.png')

# Distribution of False Counts by Matrix Size
plt.figure(figsize=(10, 5))
bins = range(int(max(max(all_false_counts.values(), key=max))) + 2)
for matrix, counts in all_false_counts.items():
    plt.hist(counts, bins=bins, alpha=0.5, label=f'{matrix}')
plt.title('Distribution of False Counts by Matrix Size')
plt.xlabel('False Counts')
plt.ylabel('Frequency')
plt.legend()
plt.grid(axis='y', alpha=0.75)
plt.savefig(f'charts/falsecounts.png')