# Giantt Include System

The Giantt include system allows you to organize your tasks across multiple files and include them in a main file.

## Quick Start

1. Create a dependencies file:
   ```
   ○ dep1 1d "Dependency 1" {"dependencies"}
   ○ dep2 2d "Dependency 2" {"dependencies"} >>> ⊢[dep1]
   ```

2. Create a main file with an include directive:
   ```
   #include dependencies.txt
   
   ○ main_task 3d "Main Task" {"main"} >>> ⊢[dep2]
   ```

3. View the include structure:
   ```bash
   giantt includes -f main.txt
   ```

4. Load the file normally - all included items will be loaded:
   ```bash
   giantt show -f main.txt --chart main
   ```

## Commands

- `giantt includes -f FILE [-r]`: Show include structure (use -r for recursive)
- `giantt add-include -f FILE INCLUDE_PATH`: Add an include directive to a file

## Features

- Circular include detection
- Graceful handling of missing files
- Relative path resolution
- Nested includes (files can include other files)

For more details, see the full documentation in `docs/includes.md`.
