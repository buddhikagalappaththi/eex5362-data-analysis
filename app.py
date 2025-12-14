import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import glob
import os
import re

# --- HELPER FUNCTIONS ---
def parse_time_string(time_str):
    """Parses '07m 04s' into total seconds."""
    if not isinstance(time_str, str) or time_str.strip() in ['-', 'N/A']: return 0
    m = re.search(r'(\d+)m', time_str)
    s = re.search(r'(\d+)s', time_str)
    minutes = int(m.group(1)) if m else 0
    seconds = int(s.group(1)) if s else 0
    return (minutes * 60) + seconds

class AmongUsProfilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Among Us Performance Profiler Tool (Final Version)")
        self.root.geometry("1350x850") # Wide window for 3 graphs
        
        # Data storage
        self.df = None
        self.data_folder = "data"

        # --- UI LAYOUT ---
        
        # 1. Header Section
        header_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="System Performance Model: Among Us Match", 
                 font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white").pack()
        tk.Label(header_frame, text="EEX5362 Mini Project Tool", 
                 font=("Segoe UI", 10), bg="#2c3e50", fg="#ecf0f1").pack()

        # 2. Control Panel
        control_frame = tk.Frame(root, pady=10, bg="#ecf0f1")
        control_frame.pack(fill="x")
        
        tk.Button(control_frame, text="📂 1. Load CSV Data", command=self.load_data, 
                  bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"), width=20, relief="flat", padx=10).grid(row=0, column=0, padx=20, pady=10)
        
        self.btn_analyze = tk.Button(control_frame, text="⚙️ 2. Run Analysis", command=self.run_analysis, 
                                     bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), width=25, relief="flat", padx=10, state="disabled")
        self.btn_analyze.grid(row=0, column=1, padx=20, pady=10)

        # 3. Text Stats Display Area
        stats_frame = tk.LabelFrame(root, text=" Performance Metrics ", font=("Segoe UI", 11, "bold"), padx=10, pady=5)
        stats_frame.pack(padx=20, pady=5, fill="x")
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10, width=100, font=("Consolas", 10), bg="#f8f9fa", relief="flat")
        self.stats_text.pack(fill="both", expand=True)
        self.stats_text.insert(tk.END, "Ready. Please load data to begin...\n")

        # 4. Graphs Area
        self.graph_frame = tk.Frame(root, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_data(self):
        """Loads all User*.csv files from the selected directory."""
        folder = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Folder containing User CSVs")
        if not folder: return

        self.data_folder = folder
        all_files = glob.glob(os.path.join(folder, "User*.csv"))
        
        if not all_files:
            messagebox.showerror("Error", "No 'User*.csv' files found in selected folder!")
            return

        try:
            df_list = []
            for f in all_files:
                try:
                    df_list.append(pd.read_csv(f))
                except: pass
            
            if not df_list: return

            full_data = pd.concat(df_list, ignore_index=True)
            
            # --- DATA CLEANING ---
            # Remove repeated headers
            if 'Team' in full_data.columns: full_data = full_data[full_data['Team'] != 'Team']
            # Convert Time to Seconds
            if 'Game Length' in full_data.columns: full_data['Duration_Seconds'] = full_data['Game Length'].apply(parse_time_string)
            
            # Clean numeric columns (handle '-', 'N/A')
            for col, new_col in [('Task Completed', 'Task_Count'), ('Imposter Kills', 'Kill_Count'), ('Sabotages Fixed', 'Sabotage_Count')]:
                if col in full_data.columns:
                    full_data[new_col] = pd.to_numeric(full_data[col].astype(str).replace(['-', 'N/A', 'nan'], '0'), errors='coerce').fillna(0)
            
            # Filter valid games
            if 'Duration_Seconds' in full_data.columns:
                full_data = full_data[full_data['Duration_Seconds'] > 0]
            
            self.df = full_data
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, f"SUCCESS: Loaded {len(all_files)} files.\n")
            self.stats_text.insert(tk.END, f"Valid Matches Processed: {len(self.df)}\n")
            self.stats_text.insert(tk.END, "-"*60 + "\nData ready. Click 'Run Analysis'.\n")
            
            self.btn_analyze.config(state="normal")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def run_analysis(self):
        """Calculates statistics and generates graphs."""
        if self.df is None: return
        
        # --- 1. Throughput ---
        crew_games = self.df[self.df['Team'] == 'Crewmate'].copy()
        avg_throughput = 0
        if not crew_games.empty:
            crew_games['Throughput'] = crew_games['Task_Count'] / (crew_games['Duration_Seconds'] / 60)
            avg_throughput = crew_games['Throughput'].mean()

        # --- 2. Resource Balance (Win Rates) ---
        imp_win_rate = 0
        crew_win_rate = 0
        win_stats = self.df.groupby(['Team', 'Outcome']).size().unstack(fill_value=0)
        
        if 'Win' in win_stats.columns:
            if 'Imposter' in win_stats.index:
                imp_total = self.df[self.df['Team'] == 'Imposter'].shape[0]
                imp_win_rate = (win_stats.loc['Imposter', 'Win'] / imp_total * 100) if imp_total > 0 else 0
            if 'Crewmate' in win_stats.index:
                crew_total = self.df[self.df['Team'] == 'Crewmate'].shape[0]
                crew_win_rate = (win_stats.loc['Crewmate', 'Win'] / crew_total * 100) if crew_total > 0 else 0

        # --- 3. Bottleneck (Correlation) ---
        sabotage_corr = 0
        if 'Sabotage_Count' in self.df.columns:
            sabotage_corr = self.df['Sabotage_Count'].corr(self.df['Duration_Seconds'])

        # --- 4. Reliability (Survival Rate) ---
        survival_rate = 0
        if not crew_games.empty and 'Murdered' in crew_games.columns:
            survivors = crew_games[crew_games['Murdered'] == 'No'].shape[0]
            survival_rate = (survivors / len(crew_games)) * 100

        # --- 5. Workload Correlation ---
        workload_corr = 0
        if not crew_games.empty:
            workload_corr = crew_games['Task_Count'].corr(crew_games['Duration_Seconds'])

        # --- DISPLAY RESULTS ---
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "=== DETAILED ANALYSIS FINDINGS ===\n\n")
        
        self.stats_text.insert(tk.END, f"4.1 System Throughput (Operational Efficiency):\n")
        self.stats_text.insert(tk.END, f"   - Crewmate Task Completion Rate: {avg_throughput:.2f} tasks/min\n\n")
        
        self.stats_text.insert(tk.END, f"4.2 Resource Allocation and Balance (Fairness):\n")
        self.stats_text.insert(tk.END, f"   - Impostor Win Rate: {imp_win_rate:.1f}%\n")
        self.stats_text.insert(tk.END, f"   - Crewmate Win Rate: {crew_win_rate:.1f}%\n")
        self.stats_text.insert(tk.END, f"   - Status: {'BALANCED' if abs(imp_win_rate - crew_win_rate) < 5 else 'IMBALANCED'}\n\n")
        
        self.stats_text.insert(tk.END, f"4.3 Bottleneck Identification (Latency Analysis):\n")
        self.stats_text.insert(tk.END, f"   - Sabotage vs Duration Correlation: {sabotage_corr:.2f}\n")
        self.stats_text.insert(tk.END, f"   - Conclusion: {'Sabotages are a bottleneck.' if sabotage_corr > 0.3 else 'Sabotages are NOT a significant bottleneck.'}\n\n")

        self.stats_text.insert(tk.END, f"4.4 System Reliability (Survival Rate):\n")
        self.stats_text.insert(tk.END, f"   - Crewmate Survival Rate: {survival_rate:.1f}%\n\n")

        self.stats_text.insert(tk.END, f"4.5 Workload vs. Latency Relationship:\n")
        self.stats_text.insert(tk.END, f"   - Task Count vs Duration Correlation: {workload_corr:.2f}\n")
        self.stats_text.insert(tk.END, f"   - Insight: {'Higher workload extends game duration.' if workload_corr > 0.3 else 'Game duration is loosely coupled to workload.'}\n")

        self.show_graphs()

    def show_graphs(self):
        # Clear previous graphs
        for widget in self.graph_frame.winfo_children(): widget.destroy()

        # Create 3 Subplots (Side by Side)
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.5), dpi=100)
        plt.subplots_adjust(wspace=0.35, bottom=0.25) # More space at bottom for legend
        
        # --- Graph 1: Latency Histogram ---
        duration_mins = self.df['Duration_Seconds'] / 60
        ax1.hist(duration_mins, bins=20, color='#3498db', edgecolor='white', alpha=0.8)
        ax1.set_title("1. Latency (Duration)", fontsize=10, fontweight='bold')
        ax1.set_xlabel("Minutes")
        ax1.set_ylabel("Frequency")
        
        # --- Graph 2: Win Balance (Stacked Bar) ---
        win_counts = self.df.groupby(['Team', 'Outcome']).size().unstack()
        if win_counts is not None and not win_counts.empty:
            win_pct = win_counts.div(win_counts.sum(axis=1), axis=0) * 100
            # Colors: Red=Loss, Green=Win
            win_pct.plot(kind='bar', stacked=True, color=['#e74c3c', '#2ecc71'], ax=ax2)
            ax2.set_title("2. Resource Balance", fontsize=10, fontweight='bold')
            ax2.set_ylabel("Percentage %")
            ax2.set_xlabel("")
            ax2.tick_params(axis='x', rotation=0)
            
            # --- LEGEND FIX ---
            # Place legend BELOW the chart so it doesn't cover the title
            ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize='8', frameon=False)

        # --- Graph 3: Workload Scatter ---
        crew_data = self.df[self.df['Team'] == 'Crewmate']
        ax3.scatter(crew_data['Duration_Seconds']/60, crew_data['Task_Count'], alpha=0.4, c='purple', edgecolors='none')
        ax3.set_title("3. Workload vs. Latency", fontsize=10, fontweight='bold')
        ax3.set_xlabel("Duration (Minutes)")
        ax3.set_ylabel("Tasks Completed")
        ax3.grid(True, linestyle=':', alpha=0.6)

        # Embed into Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = AmongUsProfilerApp(root)
    root.mainloop()
