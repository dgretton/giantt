#!/bin/zsh

# Check if a directory argument is provided
if [[ -z "$1" ]]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

TARGET_DIR="$1"

# Ensure the target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: Directory '$TARGET_DIR' does not exist."
  exit 1
fi

# Generate the tree structure
tree_output=$(tree --noreport "$TARGET_DIR" | sed 's/^[0-9]* directories, [0-9]* files$//')

# Output the tree structure
echo "$tree_output"

# Optionally, save the output to a file
OUTPUT_FILE="actual-current-directory-tree.txt"
echo "$tree_output" > "$OUTPUT_FILE"

echo "Directory tree saved to $OUTPUT_FILE"

