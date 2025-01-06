# AI Git Commit Message Generator 🤖 ✨

This repository contains two scripts that automatically generate meaningful Git commit messages using AI. Both scripts analyze your code changes and create descriptive commit messages, with optional emoji support.

## Scripts Overview 📜

### 1. Generate.py (Ollama Version) 🐳
Uses Ollama's local AI model to generate commit messages.

**Features:**
- 🔄 Local AI processing with Ollama
- 🔍 Analyzes both staged and unstaged changes
- 👀 Watch mode for automatic commits
- 😊 Optional emoji in commit messages
- 📝 Detailed change summaries
- 🎯 Support for staged-only commits

**Requirements:**
- Python 3.x
- Ollama installed and running
- qwen2.5-coder:3b model in Ollama

### 2. Generate_Hyperbolic.py (Cloud Version) ☁️
Uses Hyperbolic's cloud API for commit message generation.

**Features:**
- 🌐 Cloud-based AI processing
- 🔍 Analyzes both staged and unstaged changes
- 👀 Watch mode for automatic commits
- 😊 Optional emoji in commit messages
- 📝 Detailed change summaries
- 🎯 Support for staged-only commits

**Requirements:**
- Python 3.x
- Hyperbolic API key
- Internet connection

## Installation 🛠️

1. Install required packages:   

```bash
pip install gitpython watchdog
```

2. For generate.py
```bash
pip install ollama-python
```

3. For generate_hyperbolic.py
```bash
pip install requests
```



## Usage 🚀

### Basic Usage:

```bash
python generate.py
```


## Using Ollama version
```bash
python generate.py
```


##Using Hyperbolic version
```bash
 python generate_hyperbolic.py
```


### Command Line Options 🎮

Both scripts support the following options:

| Option | Short | Description |
|--------|-------|-------------|
| `--path` | `-p` | Path to Git repository (default: current directory) |
| `--emoji` | `-e` | Enable emoji in commit messages |
| `--staged` | `-s` | Only process staged files |
| `--watch` | `-w` | Enable watch mode for automatic commits |
| `--delay` | `-d` | Delay in seconds before auto-commit (default: 5) |
| `--debug` | | Enable debug logging |

### Examples 📋

```bash
python generate.py -p /path/to/repo -e -s -w -d 10
```



## Watch mode with emojis
```bash
python generate.py -w -e
```

## Process only staged changes
```bash
python generate.py -s
```

## Watch staged changes with custom delay
```bash
python generate.py -w -s -d 10
```

## Use specific repository path
```bash
python generate.py -p /path/to/repo
```

## Features in Detail 🔍

### Watch Mode 👀
- Monitors repository for changes
- Automatically generates commit messages
- Configurable delay before commit
- Can be limited to staged changes only

### Emoji Support 😊
- Adds relevant emojis based on change type
- Follows conventional commit message format
- Makes commits more expressive and readable

### Logging 📊
- Detailed debug logs available
- UTF-8 support for emoji logging
- Tracks all operations and errors

## Error Handling 🛡️
- Graceful handling of Git errors
- API connection error management
- Unicode/encoding error protection
- Duplicate processing prevention

## Contributing 🤝
Feel free to submit issues and enhancement requests!

## License 📄
MIT License

## Note ℹ️
- The Ollama version (generate.py) requires a local Ollama installation
- The Hyperbolic version (generate_hyperbolic.py) requires an API key and internet connection
- Both scripts provide similar functionality with different AI backends


```
python .\generate_hyperbolic.py --watch --staged --emoji --delay 2 -p C:\Users\adel\KONSOL\Projects\KonsolERP\konsolAppCore
```
