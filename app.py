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
    if not isinstance(time_str, str) or time_str.strip() in ['-', 'N/A']: return 0
    m = re.search(r'(\d+)m', time_str)
    s = re.search(r'(\d+)s', time_str)
    minutes = int(m.group(1)) if m else 0
    seconds = int(s.group(1)) if s else 0
    return (minutes * 60) + seconds

class AmongUsProfilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Among Us Performance Profiler Tool (Advanced)")
        self.root.geometry("1300x850") # Wider window for 3 graphs
        
        # Data storage
        self.df = None
        self.data_folder = "data"

        # --- UI LAYOUT ---
        
        # 1. Header
        header_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="System Performance Model: Among Us Match", 
                 font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white").pack()

        # 2. Control Panel
        control_frame = tk.Frame(root, pady=10, bg="#ecf0f1")
        control_frame.pack(fill="x")
        
        tk.Button(control_frame, text="📂 1. Load CSV Data", command=self.load_data, 
                  bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"), width=20).grid(row=0, column=0, padx=20, pady=10)
        
        self.btn_analyze = tk.Button(control_frame, text="⚙️ 2. Run Analysis", command=self.run_analysis, 
                                     bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), width=25, state="disabled")
        self.btn_analyze.grid(row=0, column=1, padx=20, pady=10)

        # 3. Stats Display Area
        stats_frame = tk.LabelFrame(root, text=" Performance Metrics ", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        stats_frame.pack(padx=20, pady=5, fill="x")
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=8, width=100, font=("Consolas", 10), bg="#f8f9fa", relief="flat")
        self.stats_text.pack(fill="both", expand=True)
        self.stats_text.insert(tk.END, "Ready. Please load data to begin...\n")

        # 4. Graphs Area
        self.graph_frame = tk.Frame(root, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_data(self):
        folder = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Folder containing User CSVs")
        if not folder: return

        self.data_folder = folder
        all_files = glob.glob(os.path.join(folder, "User*.csv"))
        
        if not all_files:
            messagebox.showerror("Error", "No 'User*.csv' files found!")
            return

        try:
            df_list = []
            for f in all_files:
                try:
                    df_list.append(pd.read_csv(f))
                except: pass
            
            if not df_list: return

            full_data = pd.concat(df_list, ignore_index=True)
            
            # Cleaning Logic
            if 'Team' in full_data.columns: full_data = full_data[full_data['Team'] != 'Team']
            if 'Game Length' in full_data.columns: full_data['Duration_Seconds'] = full_data['Game Length'].apply(parse_time_string)
            
            # Clean numeric columns
            for col, new_col in [('Task Completed', 'Task_Count'), ('Imposter Kills', 'Kill_Count'), ('Sabotages Fixed', 'Sabotage_Count')]:
                if col in full_data.columns:
                    full_data[new_col] = pd.to_numeric(full_data[col].astype(str).replace(['-', 'N/A', 'nan'], '0'), errors='coerce').fillna(0)
            
            if 'Duration_Seconds' in full_data.columns:
                full_data = full_data[full_data['Duration_Seconds'] > 0]
            
            self.df = full_data
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, f"SUCCESS: Loaded {len(all_files)} files.\nValid Matches: {len(self.df)}\n")
            self.btn_analyze.config(state="normal")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def run_analysis(self):
        if self.df is None: return
        
        # --- CALCULATIONS ---
        
        # 1. Crewmate Stats
        crew_games = self.df[self.df['Team'] == 'Crewmate'].copy()
        avg_throughput = 0
        survival_rate = 0
        if not crew_games.empty:
            crew_games['Throughput'] = crew_games['Task_Count'] / (crew_games['Duration_Seconds'] / 60)
            avg_throughput = crew_games['Throughput'].mean()
            # Calculate Survival Rate (assuming 'Murdered' column exists)
            if 'Murdered' in crew_games.columns:
                survivors = crew_games[crew_games['Murdered'] == 'No'].shape[0]
                survival_rate = (survivors / len(crew_games)) * 100

        # 2. Impostor Stats
        imp_games = self.df[self.df['Team'] == 'Imposter']
        avg_kills = 0
        if not imp_games.empty:
            avg_kills = imp_games['Kill_Count'].mean()

        # 3. Win Rates
        win_stats = self.df.groupby(['Team', 'Outcome']).size().unstack(fill_value=0)
        imp_win_rate = 0
        crew_win_rate = 0
        
        if 'Win' in win_stats.columns:
            if 'Imposter' in win_stats.index:
                imp_win_rate = (win_stats.loc['Imposter', 'Win'] / len(imp_games) * 100)
            if 'Crewmate' in win_stats.index:
                crew_win_rate = (win_stats.loc['Crewmate', 'Win'] / len(crew_games) * 100)

        # 4. Bottleneck
        corr = 0
        if 'Sabotage_Count' in self.df.columns:
            corr = self.df['Sabotage_Count'].corr(self.df['Duration_Seconds'])

        # --- DISPLAY TEXT ---
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "=== COMPREHENSIVE PERFORMANCE REPORT ===\n")
        self.stats_text.insert(tk.END, f"1. System Efficiency:\n")
        self.stats_text.insert(tk.END, f"   - Crewmate Task Throughput: {avg_throughput:.2f} tasks/min\n")
        self.stats_text.insert(tk.END, f"   - Crewmate Reliability (Survival Rate): {survival_rate:.1f}%\n")
        self.stats_text.insert(tk.END, f"   - Impostor Service Rate (Avg Kills): {avg_kills:.2f} kills/game\n\n")
        self.stats_text.insert(tk.END, f"2. Resource Balance:\n")
        self.stats_text.insert(tk.END, f"   - Impostor Win Rate: {imp_win_rate:.1f}% | Crewmate Win Rate: {crew_win_rate:.1f}%\n")
        self.stats_text.insert(tk.END, f"   - Bottleneck Correlation (Sabotage vs Time): {corr:.2f}\n")

        self.show_graphs()

    def show_graphs(self):
        for widget in self.graph_frame.winfo_children(): widget.destroy()

        # Create 3 Subplots
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4), dpi=100)
        plt.subplots_adjust(wspace=0.3)
        
        # Graph 1: Latency (Histogram)
        duration_mins = self.df['Duration_Seconds'] / 60
        ax1.hist(duration_mins, bins=20, color='#3498db', edgecolor='white', alpha=0.7)
        ax1.set_title("1. Latency (Match Duration)")
        ax1.set_xlabel("Minutes")
        ax1.set_ylabel("Frequency")
        
        # Graph 2: Win Balance (Bar)
        win_counts = self.df.groupby(['Team', 'Outcome']).size().unstack()
        if win_counts is not None and not win_counts.empty:
            win_pct = win_counts.div(win_counts.sum(axis=1), axis=0) * 100
            win_pct.plot(kind='bar', stacked=True, color=['#e74c3c', '#2ecc71'], ax=ax2)
            ax2.set_title("2. Resource Balance (Win %)")
            ax2.set_ylabel("Win %")
            ax2.tick_params(axis='x', rotation=0)
            ax2.get_legend().remove() # Remove legend to save space

        # Graph 3: Workload vs Latency (Scatter)
        # We plot Tasks Completed vs Game Duration for Crewmates
        crew_data = self.df[self.df['Team'] == 'Crewmate']
        ax3.scatter(crew_data['Duration_Seconds']/60, crew_data['Task_Count'], alpha=0.5, c='purple', edgecolors='w')
        ax3.set_title("3. Workload vs. Latency")
        ax3.set_xlabel("Duration (Minutes)")
        ax3.set_ylabel("Tasks Completed")
        ax3.grid(True, linestyle='--', alpha=0.5)

        # Embed
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = AmongUsProfilerApp(root)
    root.mainloop()