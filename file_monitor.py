import time
import os
import psutil
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback

class PythonFileHandler(FileSystemEventHandler):
    def __init__(self, log_file, base_dir):
        super().__init__()
        self.log_file = log_file
        self.base_dir = Path(base_dir).resolve()

    def is_under_desktop(self, path):
        return self.base_dir in Path(path).resolve().parents

    def log(self, message):
        try:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
        except Exception as e:
            print(f"Failed to log message: {message}")
            print(f"Error: {e}")

    def on_modified(self, event):
        try:
            if event.src_path.endswith(".py") and self.is_under_desktop(event.src_path):
                self.log(f"Modified: {event.src_path} at {time.ctime()}")
        except Exception as e:
            self.log(f"Error on modified event: {traceback.format_exc()}")

    def on_created(self, event):
        try:
            if event.src_path.endswith(".py") and self.is_under_desktop(event.src_path):
                self.log(f"Created: {event.src_path} at {time.ctime()}")
        except Exception as e:
            self.log(f"Error on created event: {traceback.format_exc()}")

def start_monitoring(log_file):
    desktop_dir = Path.home() / "Desktop"
    observer = Observer()
    event_handler = PythonFileHandler(log_file, desktop_dir)

    try:
        observer.schedule(event_handler, str(desktop_dir), recursive=True)
        observer.start()
        print(f"Monitoring Python files in {desktop_dir}...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping the monitor...")
        observer.stop()
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Error starting monitor: {traceback.format_exc()}\n")
    observer.join()

if __name__ == "__main__":
    log_file = str(Path("~/.cw/python_file_changes.log").expanduser())
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    start_monitoring(log_file)
