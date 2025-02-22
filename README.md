# Giantt

A command-line utility for managing task dependencies and life planning through a giant Gantt chart system.

**⚠️  DEVELOPMENT STATUS: Experimental/Alpha**

## Quick Setup

### Prerequisites

- Python 3.7 or later
- pip (Python package installer)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/dgretton/giantt.git
   cd giantt
   ```

2. (optional) Use a virtual environment
   ```bash
   virtualenv venv
   . ./venv/bin/activate
   ```
   Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a symlink to make the CLI accessible from anywhere:
   ```bash
   chmod +x cli/python/giantt_cli.py
   ln -s "$(pwd)/cli/python/giantt_cli.py" ~/bin/giantt
   ```

   Make sure `~/bin` is in your PATH. If not, add this to your `.bashrc` or `.zshrc`:
   ```bash
   export PATH="$HOME/bin:$PATH"
   ```

   Alternatively, you can create an alias in your shell configuration:
   ```bash
   echo 'alias giantt="python /path/to/giantt/cli/python/giantt_cli.py"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Initial Setup

Initialize Giantt with the development flag for a local setup:

```bash
giantt init --dev
```

This creates a `.giantt` directory in your current location rather than in your home directory. This is recommended during development.

For a standard setup (not recommended during active development):
```bash
giantt init
```

## Basic Usage

After initialization, you can start adding and managing items:

```bash
# Add a new item
giantt add learn_python "Learn Python basics" --duration 3mo --tags "programming,education"

# Show item details
giantt show learn_python

# Change item status
giantt set-status learn_python IN_PROGRESS
```

See `docs/samples/` for samples of commands, items and logs.

## Data Structure

When using `--dev` mode, Giantt creates:
- `./.giantt/include/items.txt` - Active tasks and projects
- `./.giantt/include/logs.jsonl` - Log entries
- `./.giantt/occlude/` - Items not intended to be included in LLM context when asking models to interpret the giantt items file directly

