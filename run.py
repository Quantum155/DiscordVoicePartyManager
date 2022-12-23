from subprocess import run
from time import sleep

file_path = "test.py"

restart_timer = 2

def start_script():
    try:
        run("python "+file_path, check=True)
    except:
        handle_crash()

def handle_crash():
    sleep(restart_timer)
    start_script()

start_script()
