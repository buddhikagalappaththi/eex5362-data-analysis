==================================================
EEX5362 Performance Modelling 2024/25
Mini Project: System Performance Evaluation
==================================================
• Name:            B. Galappaththi
• Registration No: 722510047
• SNumber:         s22101386
• System:          "An Among Us Match"
• Due Date:        12/Dec/2025

==================================================
PROJECT OVERVIEW
==================================================
This project focuses on the performance modeling and evaluation of a complex,
session-based system: a match in the multiplayer game Among Us.

Instead of a theoretical simulation, this project utilizes a Performance Profiling approach. I developed a custom Python tool (app.py) to ingest, clean, and analyze
real-world telemetry data from 29 users (over 2,200 matches).

The goal is to evaluate:

System Throughput (Task Completion Rate)

Resource Allocation & Balance (Win Rates)

System Reliability (Survival Rate)

Bottleneck Identification (Sabotage Impact)

==================================================
DATASET
==================================================
The analysis uses the "Among Us Complete Dataset" sourced from Kaggle.

Location: data/ folder

Format:   29 individual CSV files (User1.csv to User29.csv)

Volume:   2,227 Valid Match Logs

==================================================
PREREQUISITES
==================================================
To run the profiling tool, you need Python installed along with the following libraries:

Python 3.x

pandas

matplotlib

tkinter (included with standard Python installations)

To install the required libraries, run:
$ pip install pandas matplotlib

==================================================
FILE STRUCTURE
==================================================
app.py
-> The main Graphical User Interface (GUI) tool. Run this to see the dashboard.

among_us_analyzer.py
-> A standalone script version of the analysis logic.

data/
-> Folder containing the 29 raw CSV data files.

AmongUs_Performance_Proposal.docx
-> The initial project proposal document.

==================================================
HOW to RUN THE TOOL
==================================================
Clone this repository or download the files.

Open your terminal/command prompt in the project folder.

Run the application:

$ python app.py

When the window opens:

Click "📂 1. Load CSV Data" and select the data folder provided in this repo.

Click "⚙️ 2. Run Analysis" to generate the metrics and graphs.

==================================================
KEY FINDINGS
==================================================
The analysis revealed that the system is statistically balanced and efficient:

Throughput: Crewmates complete ~0.56 tasks per minute.

Balance: Win rates are nearly identical (Impostor: 55.9% vs Crewmate: 55.7%).

Bottlenecks: Sabotages show a very low correlation (0.12) with game duration,
indicating they are NOT a significant bottleneck.
