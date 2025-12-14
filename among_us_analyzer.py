import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import re

# --- 1. HELPER FUNCTIONS ---

def parse_time_string(time_str):
    """
    Converts time strings like '07m 04s', '12s', or '1m' into total seconds (integer).
    Returns 0 if the format is invalid or missing.
    """
    if not isinstance(time_str, str) or time_str.strip() in ['-', 'N/A']:
        return 0
    
    minutes = 0
    seconds = 0
    
    # Extract minutes (look for digits before 'm')
    match_m = re.search(r'(\d+)m', time_str)
    if match_m:
        minutes = int(match_m.group(1))
        
    # Extract seconds (look for digits before 's')
    match_s = re.search(r'(\d+)s', time_str)
    if match_s:
        seconds = int(match_s.group(1))
        
    return (minutes * 60) + seconds

# --- 2. DATA LOADING & CLEANING ---

def load_and_clean_data(folder_path):
    print("--- Loading Data from 'data' folder ---")
    
    # Find all CSV files that start with "User" inside the data folder
    all_files = glob.glob(os.path.join(folder_path, "User*.csv"))
    
    if not all_files:
        print("ERROR: No CSV files found! Make sure they are in a folder named 'data'.")
        return None
        
    print(f"Found {len(all_files)} files. Reading...")

    df_list = []
    for filename in all_files:
        try:
            # Read each CSV file
            df = pd.read_csv(filename)
            df_list.append(df)
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")

    if not df_list:
        return None

    # Combine all individual user files into one large dataset
    full_data = pd.concat(df_list, ignore_index=True)
    
    print(f"Raw data loaded: {len(full_data)} rows.")
    
    # --- DATA CLEANING STEPS ---
    
    # 1. Remove "junk" header rows that might be repeated inside the data
    if 'Team' in full_data.columns:
        full_data = full_data[full_data['Team'] != 'Team']
    
    # 2. Convert 'Game Length' text to Seconds (Numeric)
    if 'Game Length' in full_data.columns:
        full_data['Duration_Seconds'] = full_data['Game Length'].apply(parse_time_string)
    
    # 3. Clean 'Task Completed' (Replace '-' with 0 and convert to number)
    if 'Task Completed' in full_data.columns:
        full_data['Task Completed'] = full_data['Task Completed'].astype(str).replace('-', '0')
        full_data['Task_Count'] = pd.to_numeric(full_data['Task Completed'], errors='coerce').fillna(0)
    
    # 4. Clean 'Imposter Kills' (Replace '-' with 0 and convert to number)
    if 'Imposter Kills' in full_data.columns:
        full_data['Imposter Kills'] = full_data['Imposter Kills'].astype(str).replace('-', '0')
        full_data['Kill_Count'] = pd.to_numeric(full_data['Imposter Kills'], errors='coerce').fillna(0)

    # 5. Clean 'Sabotages Fixed' (Replace 'N/A' or '-' with 0)
    if 'Sabotages Fixed' in full_data.columns:
        full_data['Sabotages Fixed'] = full_data['Sabotages Fixed'].astype(str).replace(['-', 'N/A', 'nan'], '0')
        full_data['Sabotage_Count'] = pd.to_numeric(full_data['Sabotages Fixed'], errors='coerce').fillna(0)

    # 6. Remove any rows with 0 seconds duration (invalid games)
    if 'Duration_Seconds' in full_data.columns:
        full_data = full_data[full_data['Duration_Seconds'] > 0]

    print(f"Cleaned data: {len(full_data)} valid matches ready for analysis.")
    return full_data

# --- 3. ANALYSIS ---

def analyze_performance(df):
    print("\n" + "="*30)
    print(" PERFORMANCE ANALYSIS RESULTS")
    print("="*30)
    
    # --- Objective 1: Throughput (Task Efficiency) ---
    # We filter for Crewmates only, as Impostors don't do tasks
    crew_games = df[df['Team'] == 'Crewmate'].copy()
    
    if not crew_games.empty:
        # Calculate Tasks per Minute for each game
        # Formula: Tasks / (Seconds / 60)
        crew_games['Throughput'] = crew_games['Task_Count'] / (crew_games['Duration_Seconds'] / 60)
        
        avg_throughput = crew_games['Throughput'].mean()
        print(f"\n1. SYSTEM THROUGHPUT (Crewmates):")
        print(f"   Average Task Completion Rate: {avg_throughput:.2f} tasks per minute")
        print(f"   Total Tasks Completed (All Games): {crew_games['Task_Count'].sum()}")

    # --- Objective 2: Resource Allocation (Win Rates) ---
    print(f"\n2. SYSTEM BALANCE (Win Rates):")
    
    # Calculate win percentage for each team
    # We group by Team and Outcome to get counts
    if 'Outcome' in df.columns and 'Team' in df.columns:
        win_stats = df.groupby(['Team', 'Outcome']).size().unstack(fill_value=0)
        
        # Calculate percentages
        if 'Win' in win_stats.columns:
            # Check if Imposter/Crewmate rows exist
            impostor_wins = win_stats.loc['Imposter', 'Win'] if 'Imposter' in win_stats.index else 0
            impostor_total = df[df['Team'] == 'Imposter'].shape[0]
            
            crew_wins = win_stats.loc['Crewmate', 'Win'] if 'Crewmate' in win_stats.index else 0
            crew_total = df[df['Team'] == 'Crewmate'].shape[0]
            
            imp_win_rate = (impostor_wins / impostor_total * 100) if impostor_total > 0 else 0
            crew_win_rate = (crew_wins / crew_total * 100) if crew_total > 0 else 0
            
            print(f"   Impostor Win Rate: {imp_win_rate:.1f}%")
            print(f"   Crewmate Win Rate: {crew_win_rate:.1f}%")
            
            if abs(imp_win_rate - crew_win_rate) < 10:
                print("   -> CONCLUSION: The system is balanced (Win rates are similar).")
            else:
                print("   -> CONCLUSION: The system is imbalanced.")

    # --- Objective 3: Bottlenecks (Sabotage Impact) ---
    print(f"\n3. BOTTLENECK ANALYSIS (Sabotages):")
    if 'Sabotage_Count' in df.columns:
        # Correlation returns a value between -1 and 1
        correlation = df['Sabotage_Count'].corr(df['Duration_Seconds'])
        
        print(f"   Correlation between Sabotages Fixed and Game Length: {correlation:.2f}")
        if correlation > 0.2:
            print("   -> INSIGHT: Sabotages act as a bottleneck, significantly extending game duration.")
        else:
            print("   -> INSIGHT: Sabotages have minimal impact on overall game latency.")

# --- 4. VISUALIZATION ---

def plot_visualizations(df):
    print("\nGenerating charts...")
    
    # Set a nice style for the plots
    plt.style.use('ggplot')

    # --- Chart 1: Game Duration Histogram (Latency) ---
    if 'Duration_Seconds' in df.columns:
        plt.figure(figsize=(10, 6))
        # Convert seconds to minutes for readability
        duration_minutes = df['Duration_Seconds'] / 60
        
        plt.hist(duration_minutes, bins=30, color='#3498db', edgecolor='black', alpha=0.7)
        plt.title('Distribution of Match Duration (System Latency)', fontsize=14)
        plt.xlabel('Match Duration (Minutes)', fontsize=12)
        plt.ylabel('Number of Matches', fontsize=12)
        plt.axvline(duration_minutes.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Avg: {duration_minutes.mean():.1f} min')
        plt.legend()
        plt.tight_layout()
        plt.savefig('chart_latency_histogram.png')
        print("   - Saved 'chart_latency_histogram.png'")

    # --- Chart 2: Win Balance Bar Chart ---
    if 'Outcome' in df.columns and 'Team' in df.columns:
        # Prepare data
        win_counts = df.groupby(['Team', 'Outcome']).size().unstack()
        if win_counts is not None and not win_counts.empty:
            # Convert to percentages for fair comparison
            win_pct = win_counts.div(win_counts.sum(axis=1), axis=0) * 100
            
            ax = win_pct.plot(kind='bar', stacked=True, color=['#e74c3c', '#2ecc71'], figsize=(8, 6))
            plt.title('Win Rate Balance (Imposter vs Crewmate)', fontsize=14)
            plt.ylabel('Percentage (%)', fontsize=12)
            plt.xlabel('Team Role', fontsize=12)
            plt.xticks(rotation=0)
            plt.legend(title='Outcome', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Add labels on the bars
            for c in ax.containers:
                ax.bar_label(c, fmt='%.1f%%', label_type='center', color='white', weight='bold')
                
            plt.tight_layout()
            plt.savefig('chart_win_balance.png')
            print("   - Saved 'chart_win_balance.png'")
        else:
            print("   - Could not generate Win Balance chart (insufficient data).")

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # 1. Define folder path (assuming 'data' folder is in same directory)
    data_folder = "data"
    
    # 2. Load and Clean
    df_matches = load_and_clean_data(data_folder)
    
    if df_matches is not None:
        # 3. Analyze
        analyze_performance(df_matches)
        
        # 4. Visualize
        plot_visualizations(df_matches)
        
        print("\nAnalysis Complete! Check the generated PNG images for your report.")