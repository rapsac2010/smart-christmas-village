import subprocess
command = r"venv\Scripts\activate && python christmas_motion_runner.py"
command2 = r"venv\Scripts\activate && python christmas_show_runner.py"

subprocess.Popen(command, shell=True)
subprocess.Popen(command2, shell=True)
