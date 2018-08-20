import subprocess
import os
import time

returncode = None
while returncode != 0:
	pkill = subprocess.run(['pkill', '-f', 'suitsBot.py'])
	if returncode is None:
		completed = subprocess.run(['python3.6', 'PythonScripts/suitsBot.py'])
	else:
		completed = subprocess.run(['python3.6', 'PythonScripts/suitsBot.py', str(returncode)])
	returncode = completed.returncode
	time.sleep(1)
print("Exiting...")