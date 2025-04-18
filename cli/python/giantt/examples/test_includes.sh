#!/bin/bash

# Create example files
mkdir -p test_includes
cd test_includes

# Create dependencies file
cat > dependencies.txt << EOF
○ dep1 1d "Dependency 1" {"dependencies"}
○ dep2 2d "Dependency 2" {"dependencies"} >>> ⊢[dep1]
○ dep3 3d "Dependency 3" {"dependencies"} >>> ⊢[dep2]
EOF

# Create projects file
cat > projects.txt << EOF
#include dependencies.txt
○ project1 5d "Project 1" {"projects"} >>> ⊢[dep3]
○ project2 4d "Project 2" {"projects"} >>> ⊢[project1]
EOF

# Create main file
cat > main.txt << EOF
#include projects.txt
○ main_task1 2d "Main Task 1" {"main"} >>> ⊢[project2]
○ main_task2 3d "Main Task 2" {"main"} >>> ⊢[main_task1]
EOF

# Show the include structure
echo "Include structure:"
giantt includes -f main.txt -r

# Show all items
echo -e "\nAll items:"
giantt show -f main.txt --chart main

# Clean up
cd ..
rm -rf test_includes

echo -e "\nTest completed."
#!/bin/bash

# Create example files
mkdir -p test_includes
cd test_includes

# Create dependencies file
cat > dependencies.txt << EOF
○ dep1 1d "Dependency 1" {"dependencies"}
○ dep2 2d "Dependency 2" {"dependencies"} >>> ⊢[dep1]
○ dep3 3d "Dependency 3" {"dependencies"} >>> ⊢[dep2]
EOF

# Create projects file
cat > projects.txt << EOF
#include dependencies.txt
○ project1 5d "Project 1" {"projects"} >>> ⊢[dep3]
○ project2 4d "Project 2" {"projects"} >>> ⊢[project1]
EOF

# Create main file
cat > main.txt << EOF
#include projects.txt
○ main_task1 2d "Main Task 1" {"main"} >>> ⊢[project2]
○ main_task2 3d "Main Task 2" {"main"} >>> ⊢[main_task1]
EOF

# Show the include structure
echo "Include structure:"
giantt includes -f main.txt -r

# Show all items
echo -e "\nAll items:"
giantt show -f main.txt --chart main

# Clean up
cd ..
rm -rf test_includes

echo -e "\nTest completed."
