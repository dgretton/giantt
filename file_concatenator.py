#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from pathlib import Path

def create_file_header(filepath: str, line_width: int = 80) -> str:
    """Create a boxed header with file metadata."""
    header = f"File: {filepath}\n"
    header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create box
    top_bottom = "+" + "=" * (line_width - 2) + "+"
    empty_line = "|" + " " * (line_width - 2) + "|"
    
    # Center the header text
    header_lines = []
    for line in header.split('\n'):
        padding = (line_width - 2 - len(line)) // 2
        header_lines.append("|" + " " * padding + line + " " * (line_width - 2 - len(line) - padding) + "|")
    
    return "\n".join([
        top_bottom,
        empty_line,
        *header_lines,
        empty_line,
        top_bottom,
        ""  # Extra newline for spacing
    ])

def concatenate_files(root_dir: str, output_file: str):
    """Concatenate all source files in the directory structure with metadata headers."""
    extensions = {'.py', '.dart', '.ts', '.sql', '.md', '.toml', '.yaml', '.sh', '.txt'}
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, _, filenames in os.walk(root_dir):
            # Skip hidden directories and their contents
            if any(part.startswith('.') for part in Path(dirpath).parts):
                continue
                
            for filename in filenames:
                # Skip hidden files and files without recognized extensions
                if filename.startswith('.') or not any(filename.endswith(ext) for ext in extensions):
                    continue
                    
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_dir)

                # Skip the output file itself
                if os.path.abspath(filepath) == os.path.abspath(output_file):
                    print(f"Skipping {rel_path}: Output file", file=sys.stderr)
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    # Write header and content
                    outfile.write(create_file_header(rel_path))
                    outfile.write(content)
                    outfile.write("\n\n")  # Add spacing between files
                except Exception as e:
                    print(f"Error processing {rel_path}: {str(e)}", file=sys.stderr)

def main():
    if len(sys.argv) != 3:
        print("Usage: python concatenate_files.py <root_directory> <output_file>")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        concatenate_files(root_dir, output_file)
        print(f"Successfully concatenated files to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
