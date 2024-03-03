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

# Load the JSON data from the file
with open('results_all.json', 'r') as file:
    data = json.load(file)

# Initialize variables for analysis
false_counts = {3: [], 4: [], 5: []}
successes = {3: 0, 4: 0, 5: 0}

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

success_rates, avg_false_counts, all_false_counts = compute_metrics(data)

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
plt.savefig(f'charts/falsecountdist.png')

# Process the data
for matrix_size, attempts in data.items():
    size = int(matrix_size.split('_')[1])  # Extract the matrix size (3, 4, 5)
    for attempt in attempts:
        if attempt['success']:
            successes[size] += 1
        for run in attempt['runs']:
            false_counts[size].append(run['false_count'])

# Calculate average false counts and total successes
average_false_counts = {size: sum(counts)/len(counts) if counts else 0 for size, counts in false_counts.items()}
total_successes = successes

# Prepare data for visualization
df_data = {
    "Matrix Size": [f"{size}x{size}" for size in sorted(average_false_counts)],
    "Average False Count": [average_false_counts[size] for size in sorted(average_false_counts)],
    "Total Successes": [total_successes[size] for size in sorted(total_successes)]
}

df = pd.DataFrame(df_data)

# Plotting
fig, ax1 = plt.subplots()

color = 'tab:red'
ax1.set_xlabel('Matrix Size')
ax1.set_ylabel('Average False Count', color=color)
ax1.plot(df['Matrix Size'], df['Average False Count'], color=color, marker='o')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Total Successes', color=color)  
ax2.plot(df['Matrix Size'], df['Total Successes'], color=color, marker='x', linestyle='--')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
plt.title('Error Trends and Successes Across Matrix Sizes')
plt.savefig(f'charts/errortrends.png')

# You can reuse the 'false_counts' dictionary from the previous code snippet
for size, counts in false_counts.items():
    plt.figure(figsize=(10, 6))
    sns.histplot(counts, bins=max(counts)-min(counts)+1, kde=True)
    plt.title(f'Error Distribution for Matrix Size {size}x{size}')
    plt.xlabel('False Count')
    plt.ylabel('Frequency')
    plt.savefig(f'charts/falsecounts.png')

# Assuming 'data' is the loaded JSON data and 'successes' is the total number of successes calculated previously

attempt_counts = {size: len(attempts) for size, attempts in data.items()}
success_rates = {size: successes[size] / attempt_counts[size] for size in successes}

# Visualize the success rates
plt.figure(figsize=(10, 6))
plt.bar(range(len(success_rates)), list(success_rates.values()), tick_label=[f"{size}x{size}" for size in success_rates])
plt.title('Success Rates Across Matrix Sizes')
plt.xlabel('Matrix Size')
plt.ylabel('Success Rate')
plt.savefig(f'charts/successrates.png')


# Prepare data
sizes = np.array(list(success_rates.keys()))
rates = np.array(list(success_rates.values()))
average_errors = np.array([average_false_counts[size] for size in sizes])

# Correlation between success rates and average errors
correlation_rate_error = np.corrcoef(rates, average_errors)[0, 1]

# Correlation between success rates and number of attempts
attempt_numbers = np.array([attempt_counts[size] for size in sizes])
correlation_rate_attempts = np.corrcoef(rates, attempt_numbers)[0, 1]

print(f"Correlation between success rates and average errors: {correlation_rate_error}")
print(f"Correlation between success rates and number of attempts: {correlation_rate_attempts}")


# Initialize data storage
false_counts = {}
successes = {}
for size in data.keys():
    false_counts[size] = []
    successes[size] = {'successes': 0, 'total': 0}

# Process data
for size, attempts in data.items():
    for attempt in attempts:
        successes[size]['total'] += 1
        if attempt['success']:
            successes[size]['successes'] += 1
        for run in attempt['runs']:
            false_counts[size].append(run['false_count'])

# Calculate average false count and success rate
avg_false_counts = {size: sum(counts)/len(counts) for size, counts in false_counts.items() if counts}
success_rates = {size: val['successes'] / val['total'] for size, val in successes.items()}

# Data for visualization
df = pd.DataFrame({
    'Matrix Size': list(avg_false_counts.keys()),
    'Average False Count': list(avg_false_counts.values()),
    'Success Rate': list(success_rates.values())
})

# Normalize for visualization
df['Normalized Success Rate'] = df['Success Rate'] / df['Success Rate'].max()
df['Normalized Avg False Count'] = df['Average False Count'] / df['Average False Count'].max()

# Visualization
plt.figure(figsize=(12, 8))
sns.barplot(data=df, x='Matrix Size', y='Normalized Avg False Count', color='blue', label='Normalized Avg False Count')
sns.lineplot(data=df, x='Matrix Size', y='Normalized Success Rate', color='red', marker='o', label='Normalized Success Rate')
plt.title('Error and Success Rate Analysis')
plt.ylabel('Normalized Rate')
plt.legend()
plt.savefig(f'charts/normalised_count.png')
