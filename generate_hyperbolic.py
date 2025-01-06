import requests
import git
import os
import argparse
from typing import Dict, List, Tuple
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from datetime import datetime

# Add Hyperbolic API configuration
HYPERBOLIC_API_URL = "https://api.hyperbolic.xyz/v1/chat/completions"
HYPERBOLIC_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZGVsNTBhbGk1MEBnbWFpbC5jb20iLCJpYXQiOjE3MzUzNTMxNTN9.k5lJTkPtxORZCa4xfKjk6Hw-bb71YrnUVvuYBT5nFOc"
HYPERBOLIC_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {HYPERBOLIC_API_KEY}"
}

def setup_logging(debug: bool = False) -> None:
    """
    Setup logging configuration with UTF-8 encoding.
    Only sets up logging if debug mode is enabled.
    """
    if not debug:
        # Disable all logging if not in debug mode
        logging.getLogger().setLevel(logging.CRITICAL)
        return
        
    log_level = logging.DEBUG
    log_filename = f"git_ai_commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure file handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    console_handler = logging.StreamHandler()
    
    # Set format for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:-2]:
        root_logger.removeHandler(handler)

def parse_arguments() -> tuple:
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Generate Git commit messages using AI')
    parser.add_argument('--path', '-p', 
                       help='Path to Git repository (optional, defaults to current directory)',
                       default=os.getcwd())
    parser.add_argument('--emoji', '-e',
                       help='Add emojis to commit message (optional)',
                       action='store_true',
                       default=False)
    parser.add_argument('--staged', '-s',
                       help='Only process staged files (optional)',
                       action='store_true',
                       default=False)
    parser.add_argument('--watch', '-w',
                       help='Watch for changes and auto-commit (optional)',
                       action='store_true',
                       default=False)
    parser.add_argument('--delay', '-d',
                       help='Delay in seconds before auto-commit (default: 5)',
                       type=int,
                       default=5)
    parser.add_argument('--debug', 
                       help='Enable debug logging',
                       action='store_true',
                       default=False)
    args = parser.parse_args()
    return os.path.abspath(args.path), args.emoji, args.staged, args.watch, args.delay, args.debug

def find_git_root(path: str) -> str:
    """
    Find the root directory of the Git repository
    """
    try:
        repo = git.Repo(path, search_parent_directories=True)
        return repo.git.rev_parse("--show-toplevel")
    except git.exc.InvalidGitRepositoryError:
        print(f"Warning: Not a Git repository at {path}. Using the specified path directly.")
        return path

def get_file_changes(repo_path: str, staged_only: bool = False) -> List[Tuple[str, str, str]]:
    """
    Get the changes in the repository.
    Returns a list of tuples (file_path, old_content, new_content)
    """
    repo = git.Repo(repo_path)
    changed_files = []
    processed_files = set()  # Keep track of processed files to avoid duplicates
    
    if not staged_only:
        # Get untracked (new) files
        untracked_files = repo.untracked_files
        for file_path in untracked_files:
            if file_path not in processed_files:
                try:
                    with open(os.path.join(repo_path, file_path), 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    changed_files.append((file_path, "", new_content))  # Empty string for old content
                    processed_files.add(file_path)
                    print(f"Found new file: {file_path}")
                except Exception as e:
                    print(f"Warning: Could not read new file {file_path}: {str(e)}")
        
        # Get unstaged changes
        for item in repo.index.diff(None):
            file_path = item.a_path or item.b_path
            if file_path not in processed_files:
                try:
                    # Get current content (working directory)
                    try:
                        with open(os.path.join(repo_path, file_path), 'r', encoding='utf-8') as f:
                            new_content = f.read()
                    except Exception as e:
                        print(f"Warning: Could not read current content for {file_path}: {str(e)}")
                        new_content = ""
                    
                    # Get staged content
                    try:
                        old_content = repo.git.show(f':{file_path}')
                    except Exception as e:
                        # File might be new in index
                        old_content = ""
                    
                    changed_files.append((file_path, old_content, new_content))
                    processed_files.add(file_path)
                    print(f"Found unstaged changes: {file_path}")
                except Exception as e:
                    print(f"Warning: Error processing unstaged file {file_path}: {str(e)}")
    
    # Get staged changes
    for item in repo.index.diff('HEAD'):
        file_path = item.a_path or item.b_path
        if file_path not in processed_files:
            try:
                # Get staged content
                try:
                    staged_content = repo.git.show(f':{file_path}')
                except Exception as e:
                    # File might be new in index
                    staged_content = ""
                
                # Get original content from HEAD
                try:
                    if repo.head.is_valid() and not item.new_file:
                        old_content = repo.git.show(f'HEAD:{file_path}')
                    else:
                        old_content = ""  # New file or no commits yet
                except Exception as e:
                    # File is likely new
                    old_content = ""
                
                changed_files.append((file_path, old_content, staged_content))
                processed_files.add(file_path)
                print(f"Found staged changes: {file_path}")
            except Exception as e:
                print(f"Warning: Error processing staged file {file_path}: {str(e)}")
    
    return changed_files

def generate_file_summary(file_path: str, old_content: str, new_content: str) -> str:
    """
    Generate a summary for a single file change using Hyperbolic API
    """
    prompt = """Please analyze the following file change and provide a concise summary of the modifications:

File: {file_path}
""".format(file_path=file_path)

    if old_content:
        prompt += "Old content:\n```\n" + old_content + "\n```\n"
    else:
        prompt += "Status: New File\n"
    prompt += "New content:\n```\n" + new_content + "\n```\n"

    try:
        data = {
            "messages": [{
                "role": "user",
                "content": prompt + "\nPlease provide a focused summary of the changes in this file."
            }],
            "model": "deepseek-ai/DeepSeek-V3",
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        response = requests.post(HYPERBOLIC_API_URL, headers=HYPERBOLIC_HEADERS, json=data)
        response.raise_for_status()  # Raise exception for bad status codes
        
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        raise Exception(f"Failed to connect to Hyperbolic API while processing {file_path}: {str(e)}")

def generate_change_summary(file_changes: List[Tuple[str, str, str]]) -> Dict[str, str]:
    """
    Generate summaries for all changed files
    Returns a dictionary of file paths and their summaries
    """
    if not file_changes:
        return {}

    file_summaries = {}
    print("\nGenerating individual file summaries...")
    
    for file_path, old_content, new_content in file_changes:
        print(f"Processing summary for: {file_path}")
        summary = generate_file_summary(file_path, old_content, new_content)
        file_summaries[file_path] = summary
        print(f"Completed summary for: {file_path}")
    
    return file_summaries

def generate_combined_commit_message(file_summaries: Dict[str, str], use_emoji: bool = False) -> str:
    """
    Generate a combined commit message based on all file summaries using Hyperbolic API
    """
    if not file_summaries:
        return "No changes to commit"

    base_prompt = """Based on the following file change summaries, please generate a comprehensive git commit message that covers all changes."""
    
    emoji_prompt = """
Add 2-3 relevant emojis at the end of the commit message based on the type of changes (e.g. ✨ for new features, 🐛 for bug fixes, 
📝 for documentation, 🎨 for style/UI, ♻️ for refactor, 🔧 for configuration, 🚀 for performance, 🧪 for tests).

Examples of commit messages with emojis:
- feat: add user authentication system ✨ 🔒
- fix: resolve memory leak in data processing 🐛 🚀
- docs: update API documentation 📝 📚
- style: improve dashboard layout 🎨 ✨
"""

    prompt = base_prompt + (emoji_prompt if use_emoji else "") + "\n\nFile summaries to analyze:"
    
    for file_path, summary in file_summaries.items():
        prompt += f"\nFile: {file_path}\nSummary: {summary}\n"
        prompt += "-" * 40 + "\n"

    prompt += "\nPlease create a commit message that effectively summarizes all these changes together. "
    prompt += "Follow git commit message best practices"
    if use_emoji:
        prompt += " and include relevant emojis at the end."
    else:
        prompt += "."

    try:
        data = {
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "model": "deepseek-ai/DeepSeek-V3",
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        response = requests.post(HYPERBOLIC_API_URL, headers=HYPERBOLIC_HEADERS, json=data)
        response.raise_for_status()
        
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        raise Exception(f"Failed to connect to Hyperbolic API while generating combined commit message: {str(e)}")

class GitChangeHandler(FileSystemEventHandler):
    def __init__(self, repo_path: str, use_emoji: bool, staged_only: bool, delay: int):
        self.repo_path = repo_path
        self.use_emoji = use_emoji
        self.staged_only = staged_only
        self.delay = delay
        self.timer = None
        self.repo = git.Repo(repo_path)
        self.processing = False
        self.last_commit_hash = None
        self.pending_changes = False
        
    def on_any_event(self, event):
        if event.is_directory:
            return
            
        # Mark that we have pending changes
        self.pending_changes = True
            
        # Cancel previous timer if exists
        if self.timer:
            self.timer.cancel()
        
        # Start new timer
        self.timer = threading.Timer(self.delay, self.process_changes)
        self.timer.start()
        logging.debug(f"Scheduled processing in {self.delay} seconds for change in {event.src_path}")
    
    def process_changes(self):
        if self.processing:
            logging.debug("Already processing changes, scheduling retry...")
            # Schedule a retry if we're currently processing
            self.timer = threading.Timer(self.delay, self.process_changes)
            self.timer.start()
            return
            
        try:
            self.processing = True
            logging.info("Starting to process changes...")
            
            if self.staged_only:
                # Check if there are any staged changes
                staged_changes = list(self.repo.index.diff('HEAD'))
                if not staged_changes:
                    logging.info("No staged changes to commit.")
                    self.processing = False
                    self.pending_changes = False
                    return
            
            # Get current HEAD hash
            try:
                current_hash = self.repo.head.commit.hexsha
            except Exception:
                current_hash = None  # Handle case of no commits yet
            
            if not self.pending_changes and current_hash == self.last_commit_hash:
                logging.debug("No new changes since last commit, skipping...")
                self.processing = False
                return
                
            changes = get_file_changes(self.repo_path, self.staged_only)
            
            if not changes:
                logging.info("No changes detected.")
                self.processing = False
                self.pending_changes = False
                return
            
            # Generate summaries and commit message
            logging.info("Generating file summaries...")
            file_summaries = generate_change_summary(changes)
            
            logging.info("Generating commit message...")
            commit_message = generate_combined_commit_message(file_summaries, self.use_emoji)
            
            # Perform the commit
            if self.staged_only:
                # Commit staged changes
                self.repo.index.commit(commit_message)
                logging.info(f"Committed staged changes with message:\n{commit_message}")
            else:
                # Stage and commit all changes
                self.repo.git.add('.')
                self.repo.index.commit(commit_message)
                logging.info(f"Committed all changes with message:\n{commit_message}")
            
            self.last_commit_hash = self.repo.head.commit.hexsha
            self.pending_changes = False
                
        except Exception as e:
            logging.error(f"Error during auto-commit: {str(e)}", exc_info=True)
        finally:
            self.processing = False
            # Check if we received new changes while processing
            if self.pending_changes:
                logging.debug("New changes detected during processing, scheduling another run...")
                self.timer = threading.Timer(self.delay, self.process_changes)
                self.timer.start()

def watch_repository(repo_path: str, use_emoji: bool, staged_only: bool, delay: int):
    """
    Watch repository for changes and auto-commit
    """
    event_handler = GitChangeHandler(repo_path, use_emoji, staged_only, delay)
    observer = Observer()
    observer.schedule(event_handler, repo_path, recursive=True)
    observer.start()
    
    print(f"\nWatching repository at: {repo_path}")
    print(f"Mode: {'staged files only' if staged_only else 'all changes'}")
    print(f"Auto-commit delay: {delay} seconds")
    print("Press Ctrl+C to stop watching...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.timer:
            event_handler.timer.cancel()
        print("\nStopped watching repository.")
    observer.join()

def main():
    try:
        # Get command line arguments
        project_path, use_emoji, staged_only, watch_mode, delay, debug = parse_arguments()
        
        # Setup logging
        setup_logging(debug)
        
        if not os.path.exists(project_path):
            raise Exception(f"The specified path does not exist: {project_path}")
        
        # Find git root or use the specified path
        repo_path = find_git_root(project_path)
        
        if watch_mode:
            # Run in watch mode
            watch_repository(repo_path, use_emoji, staged_only, delay)
        else:
            # Run once
            print(f"Using repository at: {repo_path}")
            print(f"Emoji in commit message: {'enabled' if use_emoji else 'disabled'}")
            print(f"Mode: {'staged files only' if staged_only else 'all changes'}")
            
            changes = get_file_changes(repo_path, staged_only)
            
            if not changes:
                print("No changes detected in the repository.")
                return
            
            # Generate individual file summaries
            file_summaries = generate_change_summary(changes)
            
            # Print individual file summaries
            print("\nIndividual File Summaries:")
            for file_path, summary in file_summaries.items():
                print(f"\nFile: {file_path}")
                print("Summary:")
                print(summary)
                print("-" * 40)
            
            # Generate combined commit message
            print("\nGenerating combined commit message...")
            commit_message = generate_combined_commit_message(file_summaries, use_emoji)
            print("\nSuggested Commit Message:")
            print(commit_message)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
