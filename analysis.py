import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

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
        objective_number = file_path.split('_')[-1].split('.')[0]
        combined_results[f'matrix_{objective_number}'] = data
    os.rename(file_path, archive_folder_path + os.path.basename(file_path))

# Write the combined results to a new file
combined_results_path = 'results_wg.json'
with open(combined_results_path, 'w') as file:
    json.dump(combined_results, file, indent=4)

# Load the JSON data from the file
with open(combined_results_path, 'r') as file:
    data = json.load(file)

# Define a function to compute metrics
def compute_metrics(data):
    success_rate, avg_false_counts, all_false_counts = {}, {}, {}
    for matrix, details in data.items():
        matrix_successes = sum(1 for attempt in details if attempt['success'])
        total_attempts = len(details)
        success_rate[matrix] = matrix_successes / total_attempts if total_attempts else 0
        total_false_counts = sum(run['false_count'] for attempt in details for run in attempt['runs'])
        total_runs = sum(len(attempt['runs']) for attempt in details)
        avg_false_counts[matrix] = total_false_counts / total_runs if total_runs else 0
        all_false_counts[matrix] = [run['false_count'] for attempt in details for run in attempt['runs']]
    return success_rate, avg_false_counts, all_false_counts

# Compute success rates, average false counts, and collect all false counts for histogram
success_rates, avg_false_counts, all_false_counts = compute_metrics(data)

# Further processing and plotting code goes here, ensuring that all dictionary keys are used consistently

# Example plotting code (Ensure to adjust according to your specific needs and correct keys usage)
plt.figure(figsize=(10, 5))
plt.bar(success_rates.keys(), success_rates.values(), color='green', alpha=0.6, label='Success Rate')
plt.ylabel('Success Rate')
plt.legend()
plt.savefig(f'charts/success_rates.png')

# After computing success rates, average false counts, all_false_counts as shown in the previous snippet

# Plot Success Rate and Average False Count by Matrix Size
plt.figure(figsize=(10, 5))
bar_positions = np.arange(len(success_rates))
plt.bar(bar_positions - 0.2, success_rates.values(), width=0.4, color='green', alpha=0.6, label='Success Rate')
plt.bar(bar_positions + 0.2, avg_false_counts.values(), width=0.4, color='red', alpha=0.6, label='Avg False Count')
plt.xticks(bar_positions, success_rates.keys())
plt.ylabel('Rate')
plt.title('Success Rate and Average False Count by Matrix Size')
plt.legend()
plt.savefig('charts/success_and_avg_false_count.png')

# Plot Distribution of False Counts by Matrix Size
plt.figure(figsize=(10, 5))
for matrix, counts in all_false_counts.items():
    sns.histplot(counts, bins=max(counts)-min(counts)+1, kde=True, label=matrix, alpha=0.5)
plt.title('Distribution of False Counts by Matrix Size')
plt.xlabel('False Counts')
plt.ylabel('Frequency')
plt.legend()
plt.grid(axis='y', alpha=0.75)
plt.savefig('charts/distribution_of_false_counts.png')

# Assuming you've correctly calculated 'success_rates' and 'avg_false_counts' and formatted them
# Normalize for visualization
df = pd.DataFrame({
    'Matrix Size': list(avg_false_counts.keys()),
    'Normalized Success Rate': [rate / max(success_rates.values()) for rate in success_rates.values()],
    'Normalized Avg False Count': [count / max(avg_false_counts.values()) for count in avg_false_counts.values()]
})

# Visualization of Normalized Success Rate and Avg False Count
plt.figure(figsize=(12, 8))
sns.barplot(data=df, x='Matrix Size', y='Normalized Avg False Count', color='blue', label='Normalized Avg False Count')
sns.lineplot(data=df, x='Matrix Size', y='Normalized Success Rate', color='red', marker='o', label='Normalized Success Rate')
plt.title('Normalized Success Rate and Avg False Count')
plt.ylabel('Normalized Rate')
plt.legend()
plt.savefig('charts/normalized_success_rate_and_avg_false_count.png')
