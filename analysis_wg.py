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
combined_results_path = 'results/results_wg.json'  # Updated path to match the uploaded file

# Load the JSON data from the file
with open(combined_results_path, 'r') as file:
    data = json.load(file)

# Define a function to compute metrics
def compute_metrics(data):
    success_rate, avg_false_counts, all_false_counts = {}, {}, {}
    for matrix, attempts in data.items():
        matrix_successes = sum(1 for attempt in attempts if 'success' in attempt and attempt['success'])
        total_attempts = len(attempts)
        success_rate[matrix] = matrix_successes / total_attempts if total_attempts else 0
        total_false_counts = sum(run['false_count'] for attempt in attempts if 'runs' in attempt for run in attempt['runs'] if 'false_count' in run)
        total_runs = sum(len(attempt['runs']) for attempt in attempts if 'runs' in attempt)
        avg_false_counts[matrix] = total_false_counts / total_runs if total_runs else 0
        all_false_counts[matrix] = [run['false_count'] for attempt in attempts if 'runs' in attempt for run in attempt['runs'] if 'false_count' in run]
    return success_rate, avg_false_counts, all_false_counts

# Compute success rates, average false counts, and collect all false counts for histogram
success_rates, avg_false_counts, all_false_counts = compute_metrics(data)

# Plot Success Rate by Matrix Size
plt.figure(figsize=(10, 5))
plt.bar(success_rates.keys(), success_rates.values(), color='green', alpha=0.6, label='Success Rate')
plt.ylabel('Success Rate')
plt.legend()
plt.savefig(f'charts/wg_success_rates.png')

# Plot Success Rate and Average False Count by Matrix Size
plt.figure(figsize=(10, 5))
bar_positions = np.arange(len(success_rates))
plt.bar(bar_positions - 0.2, success_rates.values(), width=0.4, color='green', alpha=0.6, label='Success Rate')
plt.bar(bar_positions + 0.2, avg_false_counts.values(), width=0.4, color='red', alpha=0.6, label='Avg False Count')
plt.xticks(bar_positions, success_rates.keys())
plt.ylabel('Rate')
plt.title('Success Rate and Average False Count by Matrix Size')
plt.legend()
plt.savefig('charts/wg_success_and_avg_false_count.png')

# Plot Distribution of False Counts by Matrix Size
plt.figure(figsize=(10, 5))
for matrix, counts in all_false_counts.items():
    if counts:  # Ensure counts is not empty
        sns.histplot(counts, bins=max(counts)-min(counts)+1, kde=True, label=matrix, alpha=0.5)
plt.title('Distribution of False Counts by Matrix Size')
plt.xlabel('False Counts')
plt.ylabel('Frequency')
plt.legend()
plt.grid(axis='y', alpha=0.75)
plt.savefig('charts/wg_distribution_of_false_counts.png')

# Normalize for visualization
max_success_rate = max(success_rates.values()) if success_rates.values() else 1
max_avg_false_count = max(avg_false_counts.values()) if avg_false_counts.values() else 1

df = pd.DataFrame({
    'Matrix Size': list(avg_false_counts.keys()),
    'Normalized Success Rate': [rate / max_success_rate if max_success_rate > 0 else 0 for rate in success_rates.values()],
    'Normalized Avg False Count': [count / max_avg_false_count if max_avg_false_count > 0 else 0 for count in avg_false_counts.values()]
})

# Ensure all lists are the same length
assert len(df['Matrix Size']) == len(df['Normalized Success Rate']) == len(df['Normalized Avg False Count'])

# Visualization of Normalized Success Rate and Avg False Count
plt.figure(figsize=(12, 8))
sns.barplot(data=df, x='Matrix Size', y='Normalized Avg False Count', color='blue', label='Normalized Avg False Count')
sns.lineplot(data=df, x='Matrix Size', y='Normalized Success Rate', color='red', marker='o', label='Normalized Success Rate')
plt.title('Normalized Success Rate and Avg False Count')
plt.ylabel('Normalized Rate')
plt.legend()
plt.savefig('charts/wg_normalized_success_rate_and_avg_false_count.png')
