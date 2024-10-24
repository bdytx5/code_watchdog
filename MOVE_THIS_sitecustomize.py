# monitors errors, console output, and python file execution 
import sys
import os
from pathlib import Path

# Define log directories and files
log_dir = os.path.expanduser("~/.cw")
all_output_log = os.path.join(log_dir, "output.log")  # Logs all console I/O (appends)
error_log_path = os.path.join(log_dir, "error_output.log")  # Logs only errors (appends)
monitor_log = Path("~/.cw/python_file_changes.log").expanduser()

# Create the directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Determine the Desktop path
desktop_path = Path(os.path.expanduser("~/Desktop"))

class Tee:
    """A class to log stdout and stderr to both the console and a log file."""
    def __init__(self, filename, mode='a'):
        self.filename = filename
        self.file = open(filename, mode)  # Open log file in specified mode
        self.stdout = sys.stdout  # Original stdout
        self.stderr = sys.stderr  # Original stderr
        self.closed = False  # Track if the file has been closed

    def write(self, message):
        """Write to both the console and the log file."""
        if not self.closed:
            self.file.write(message)
            self.file.flush()  # Ensure log is updated immediately
        self.stdout.write(message)  # Print to the console

    def flush(self):
        """Ensure both the console and log file are properly flushed."""
        if not self.closed:
            self.file.flush()
        self.stdout.flush()

    def close(self):
        """Close the log file if it is still open."""
        if not self.closed:
            self.file.close()
            self.closed = True

class ErrorLogger:
    """A class to log stderr messages to both output.log and error_output.log."""
    def __init__(self, error_filename, all_output_filename):
        # Open error log in 'w' mode to overwrite each time
        self.error_filename = error_filename
        self.error_file = open(error_filename, 'w')  # Write mode (overwrites)
        self.all_output_file = open(all_output_filename, 'a')  # Append mode
        self.stderr = sys.__stderr__  # Original stderr
        self.error_logged = False  # Track if an error was logged
        self.closed = False  # Track if the files have been closed

    def write(self, message):
        """Write errors to both error_output.log (overwrite) and output.log (append)."""
        if not self.closed:
            self.error_file.write(message)
            self.error_file.flush()  # Ensure log is updated immediately

            self.all_output_file.write(message)
            self.all_output_file.flush()

            self.error_logged = True  # Track that an error was logged

        self.stderr.write(message)  # Print to the console

    def flush(self):
        """Ensure all files are properly flushed."""
        if not self.closed:
            self.error_file.flush()
            self.all_output_file.flush()
        self.stderr.flush()

    def close(self):
        """Close the log files if they are still open."""
        if not self.closed:
            self.error_file.close()
            self.all_output_file.close()
            self.closed = True

# Ensure log files are properly closed on exit
def cleanup():
    """Clean up resources by closing log files."""
    output_logger.close()
    error_logger.close()

def log_recent_script():
    """Log the path of the most recently run Python script if it's within the Desktop directory."""
    script_path = Path(sys.argv[0]).resolve()  # Get the current script path

    # Check if the script is within the Desktop or any of its subdirectories
    if desktop_path in script_path.parents or script_path == desktop_path:
        try:
            with open(monitor_log, 'a') as log_file:  # Append mode
                log_file.write(f"Executed: {script_path}\n")
        except Exception as e:
            print(f"Error logging script path: {e}", file=sys.__stderr__)

# Log the current script execution (if applicable)
log_recent_script()

# Set up logging for stdout and stderr
output_logger = Tee(all_output_log, mode='a')  # Append to all_output.log
sys.stdout = output_logger  # Redirect stdout to the Tee instance

error_logger = ErrorLogger(error_log_path, all_output_log)  # Capture errors in both logs
sys.stderr = error_logger  # Redirect stderr to the ErrorLogger instance

# Ensure log files are properly closed on exit
def cleanup():
    """Clean up resources by closing log files."""
    output_logger.close()
    error_logger.close()

import atexit  # Ensure cleanup happens when the script exits
atexit.register(cleanup)
