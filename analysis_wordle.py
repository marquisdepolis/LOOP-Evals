import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the JSON data
file_path = 'results/results_wordle.json'
with open(file_path, 'r') as file:
    data = json.load(file)

# Convert the JSON data to a Pandas DataFrame
df = pd.DataFrame(data)

# Success Analysis: Calculate the number of successful guesses
successes = df[df['Guessed word'] == df['Target word']].shape[0]

# Progression Analysis: Prepare data for analyzing trends of 'G' and 'Y' counts over attempts within each run
# We'll group by 'Run #' and then examine the 'G' and 'Y' trends within those groups
# g_y_trends = df.groupby('Run #').apply(lambda x: x[['Number of \'G\' in colorised results', 'Number of \'Y\' in colorised results']].values.tolist())
g_y_trends = df.groupby('Run #').apply(lambda x: x[['Number of \'G\' in colorised results', 'Number of \'Y\' in colorised results']].values.tolist(), include_groups=False)
# Displaying the total number of successes
successes, g_y_trends.head()
def plot_g_y_trends_for_all_runs(g_y_trends):
    runs_to_plot = g_y_trends.index.unique()  # Automatically determine all runs
    num_runs = len(runs_to_plot)
    fig, axes = plt.subplots(nrows=num_runs, ncols=1, figsize=(10, 5 * num_runs), sharex=True)

    if num_runs == 1:  # Adjust if there's only one run to plot
        axes = [axes]

    for run, ax in zip(runs_to_plot, axes):
        trends = g_y_trends.loc[run]
        attempts = range(1, len(trends) + 1)
        g_counts = [trend[0] for trend in trends]
        y_counts = [trend[1] for trend in trends]
        
        ax.plot(attempts, g_counts, marker='o', linestyle='-', color='green', label='Correct Position (G)')
        ax.plot(attempts, y_counts, marker='o', linestyle='-', color='orange', label='Correct Letter, Wrong Position (Y)')
        ax.set_title(f'Run #{run} Trends of G and Y Counts')
        ax.set_xlabel('Attempt Number')
        ax.set_ylabel('Count')
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    # Save the figure
    plt.savefig('charts/wordle_g_y_trends.png', format='png')

# Call the function to plot and save the figure for all runs
plot_g_y_trends_for_all_runs(g_y_trends)

# Preparing data for visualization
# We need to reset the index to work with 'Run #' as a regular column for easier plotting
df_reset = df.reset_index()
# Plotting
plt.figure(figsize=(14, 7))

# Plot for 'G' counts
sns.lineplot(data=df_reset, x="Run #", y="Number of 'G' in colorised results", marker='o', label="Correct Position ('G')", color="green")

# Plot for 'Y' counts
sns.lineplot(data=df_reset, x="Run #", y="Number of 'Y' in colorised results", marker='o', label="Correct Letter, Wrong Position ('Y')", color="orange")

plt.title("Average 'G' and 'Y' Counts per Attempt Across Runs")
plt.xlabel("Run Number")
plt.ylabel("Average Count")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.savefig('charts/wordle_avg_GY_trend.png')

# Heatmap of 'G+Y' counts across all attempts and runs
df['Total G+Y'] = df["Number of 'G' in colorised results"] + df["Number of 'Y' in colorised results"]
heatmap_data = df.pivot_table(index='Run #', columns='Global attempt #', values='Total G+Y', aggfunc='mean', fill_value=0)

plt.figure(figsize=(12, 7))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", linewidths=.5, cmap='YlGnBu')
plt.title("Heatmap of 'G+Y' Counts per Attempt Across All Runs")
plt.xlabel("Attempt Number")
plt.ylabel("Run Number")
plt.savefig('charts/wordle_heatmap avg.png')

# Box Plot of 'G' and 'Y' Counts
plt.figure(figsize=(14, 7))
sns.boxplot(data=df[['Number of \'G\' in colorised results', 'Number of \'Y\' in colorised results']])
plt.title("Box Plot of 'G' and 'Y' Counts Across All Attempts")
plt.ylabel("Count")
plt.savefig('charts/wordle_GY_count.png')