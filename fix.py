
import anthropic
import sys
from pathlib import Path
import os
import re
import subprocess
import weave; weave.init("cw")
#@ 
# Set up the Anthropic client with the provided API key
# # Initialize the Anthropic client

import os
import anthropic

client = anthropic.Client(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Define the log file paths
log_dir = os.path.expanduser("~/.cw")
log_file_path = os.path.join(log_dir, "output.log")
error_log_path = os.path.join(log_dir, "error_output.log")
monitor_log = Path("~/.cw/python_file_changes.log").expanduser()
solution_file_path = Path("~/.cw/solution.py").expanduser()  # Path to the solution file

def get_last_n_lines(file_path, n=40):
    """Read the last n lines of a file."""
    try:
        with open(file_path, 'r') as f:
            return ''.join(f.readlines()[-n:])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def get_unique_files_from_log(n):
    """Extract the last n unique modified Python files from the monitor log."""
    if not monitor_log.exists():
        print(f"Log file not found: {monitor_log}")
        sys.exit(1)

    unique_files = []
    seen_files = set()

    with open(monitor_log, 'r') as f:
        lines = f.readlines()

    # Iterate over the log lines in reverse to get the most recent first
    for line in reversed(lines):
        parts = line.split()
        if len(parts) > 1 and parts[0] in ["Modified:", "Created:", "Executed:"]:
            
            file_path = parts[1]
        
                
            if file_path not in seen_files and 'fix.py' not in file_path and 'file_monitor.py' not in file_path:
                seen_files.add(file_path)
                unique_files.append(file_path)

            if len(unique_files) >= n:
                break

    return unique_files

def read_file_contents(file_paths):
    """Read and return the contents of the specified files."""
    contents = ""
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                contents += f"\n--- {file_path} ---\n{f.read()}"
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return contents

@weave.op

def generate_fix_with_anthropic(error_log: str, recent_output: str, file_contents: str, instruction: str = "") -> str:
    """Query the Anthropic API with the error log, recent files content, and optional instruction."""

    # Prepare the user content for the message
    user_content = [
        {"type": "text", "text": f"I encountered the following error:\n\n{error_log}"},
        {"type": "text", "text": f"Here is the most recent console output:\n\n{recent_output}"},
        {"type": "text", "text": f"Here are the contents of some recent Python files:\n\n{file_contents}"}
    ]

    if instruction:
        user_content.append({"type": "text", "text": f"Additional instruction: {instruction}"})

    # Create the message using the Messages API
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022", 
        max_tokens=1024,
        temperature=0,
        system="You are an expert Python programmer. Help resolve code errors efficiently.",
        messages=[
            {
                "role": "user",
                "content": user_content
            }
        ]
    )

    return message.content[0].text  # Correct access to the response content



def parse_claude_output(output: str) -> str:
    """Parse Claude's output into Python code and comments."""
    code_lines = []
    comment_lines = []

    code_block_start = re.compile(r"```python")
    code_block_end = re.compile(r"```")

    inside_code_block = False

    for line in output.splitlines():
        if code_block_start.match(line.strip()):
            inside_code_block = True
            continue  # Skip the start marker
        elif code_block_end.match(line.strip()):
            inside_code_block = False
            continue  # Skip the end marker

        if inside_code_block:
            code_lines.append(line)
        else:
            if line.strip():  # Avoid adding empty comment lines
                comment_lines.append(f"# {line}")

    if code_lines:
        return "\n".join(comment_lines + ["\n"] + code_lines)
    else:
        return output

def save_to_solution_file(content: str, file_path: Path):
    """Save the generated content to the solution.py file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Saved solution to {file_path}")

def open_file_in_vscode(file_path: Path):
    """Open the specified file in VSCode."""
    try:
        subprocess.run(["code", str(file_path)], check=True)
        print(f"Opened {file_path} in VSCode")
    except subprocess.CalledProcessError as e:
        print(f"Failed to open {file_path} in VSCode: {e}")
    except FileNotFoundError:
        print("VSCode executable 'code' not found. Make sure VSCode command line tools are installed.")




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_last_modified.py <n> [<instruction>] [err|console]")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
    except ValueError:
        print("Error: <n> must be an integer.")
        sys.exit(1)

    # Optional instruction parameter
    instruction = ""
    log_type = ""

    # Determine if the second argument is instruction or log type
    if len(sys.argv) > 2:
        if sys.argv[2] in ["err", "console"]:
            log_type = sys.argv[2]
        else:
            instruction = sys.argv[2]

    # Check for log_type in the third argument if not already set
    if not log_type and len(sys.argv) > 3:
        log_type = sys.argv[3]

    # Get the last n unique modified files
    unique_files = get_unique_files_from_log(n)
    print(unique_files)
    file_contents = read_file_contents(unique_files) if unique_files else ""

    # Read the last 40 lines of output.log and error_output.log
    recent_output = get_last_n_lines(log_file_path, 40)
    error_log = get_last_n_lines(error_log_path, 40)

    if error_log.strip() or recent_output.strip():
        print("\n--- Generating Fix with Anthropic ---")
        if log_type == "err":
            fix = generate_fix_with_anthropic(error_log, "", file_contents, instruction)
        elif log_type == "console":
            fix = generate_fix_with_anthropic("", recent_output, file_contents, instruction)
        else:
            fix = generate_fix_with_anthropic(error_log, recent_output, file_contents, instruction)

        print(f"\n--- Suggested Fix ---\n{fix}")

        # Parse the fix and check if it contains Python code
        parsed_content = parse_claude_output(fix)

        if "```python" in fix:
            save_to_solution_file(parsed_content, solution_file_path)
            open_file_in_vscode(solution_file_path)
        else:
            print("\n--- Solution ---")
            print(parsed_content)
    else:
        print("\nNo recent output or errors found.")
