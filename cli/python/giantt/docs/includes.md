# Giantt Include System

The Giantt include system allows you to organize your tasks across multiple files and include them in a main file. This is useful for:

- Organizing tasks by project, team, or category
- Sharing common dependencies across multiple projects
- Creating reusable task templates

## Using Includes

To include another Giantt items file, add an `#include` directive at the top of your file:

```
#include path/to/file.txt
#include another/file.txt

○ task1 1d "My Task" {"chart1"}
...
```

Include directives must be at the top of the file, before any task definitions.

## Include Resolution

- Relative paths are resolved relative to the including file
- Circular includes are detected and handled gracefully
- Missing include files generate a warning but don't cause failure

## Commands

### Show Include Structure

```bash
giantt includes -f my_file.txt
```

Show the include structure recursively:

```bash
giantt includes -f my_file.txt -r
```

### Add an Include

```bash
giantt add-include -f my_file.txt path/to/include.txt
```

## Best Practices

1. **Organize by Purpose**: Create separate files for different projects, teams, or categories
2. **Dependency Management**: Put common dependencies in separate files
3. **Avoid Deep Nesting**: Keep the include hierarchy shallow for better maintainability
4. **Use Meaningful Names**: Name your files descriptively
5. **Document Relationships**: Add comments to explain why files are included

## Example

**main.txt**:
```
#include dependencies.txt
#include project_a.txt
#include project_b.txt

○ milestone1 1d "Project Milestone 1" {"milestones"} >>> ⊢[proj_a_task3,proj_b_task2]
```

**dependencies.txt**:
```
○ setup_env 2d "Setup Environment" {"setup"}
○ install_deps 1d "Install Dependencies" {"setup"} >>> ⊢[setup_env]
```

**project_a.txt**:
```
#include dependencies.txt

○ proj_a_task1 3d "Project A Task 1" {"project_a"} >>> ⊢[install_deps]
○ proj_a_task2 2d "Project A Task 2" {"project_a"} >>> ⊢[proj_a_task1]
○ proj_a_task3 1d "Project A Task 3" {"project_a"} >>> ⊢[proj_a_task2]
```
