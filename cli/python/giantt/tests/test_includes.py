import os
import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from giantt_cli import cli, load_graph_from_file, parse_include_directives

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_parse_include_directives(temp_dir):
    """Test parsing include directives from a file."""
    # Create a test file with include directives
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("#include file1.txt\n")
        f.write("#include file2.txt\n")
        f.write("○ item1 1d \"Test Item\" {\"chart1\"}\n")
    
    # Parse include directives
    includes = parse_include_directives(test_file)
    
    # Check that the includes were parsed correctly
    assert includes == ["file1.txt", "file2.txt"]

def test_load_graph_with_includes(temp_dir):
    """Test loading a graph with includes."""
    # Create test files
    main_file = os.path.join(temp_dir, "main.txt")
    include_file1 = os.path.join(temp_dir, "include1.txt")
    include_file2 = os.path.join(temp_dir, "include2.txt")
    
    # Create the include files
    with open(include_file1, "w") as f:
        f.write("○ item1 1d \"Item 1\" {\"chart1\"}\n")
    
    with open(include_file2, "w") as f:
        f.write("○ item2 2d \"Item 2\" {\"chart2\"}\n")
    
    # Create the main file with includes
    with open(main_file, "w") as f:
        f.write(f"#include {include_file1}\n")
        f.write(f"#include {include_file2}\n")
        f.write("○ item3 3d \"Item 3\" {\"chart3\"}\n")
    
    # Load the graph
    graph = load_graph_from_file(main_file)
    
    # Check that all items were loaded
    assert len(graph.items) == 3
    assert "item1" in graph.items
    assert "item2" in graph.items
    assert "item3" in graph.items

def test_circular_includes(temp_dir):
    """Test handling of circular includes."""
    # Create test files with circular includes
    file1 = os.path.join(temp_dir, "file1.txt")
    file2 = os.path.join(temp_dir, "file2.txt")
    
    with open(file1, "w") as f:
        f.write(f"#include {file2}\n")
        f.write("○ item1 1d \"Item 1\" {\"chart1\"}\n")
    
    with open(file2, "w") as f:
        f.write(f"#include {file1}\n")
        f.write("○ item2 2d \"Item 2\" {\"chart2\"}\n")
    
    # Load the graph - should handle circular includes gracefully
    graph = load_graph_from_file(file1)
    
    # Check that items were loaded despite circular includes
    assert len(graph.items) == 2
    assert "item1" in graph.items
    assert "item2" in graph.items

def test_missing_include_file(temp_dir):
    """Test handling of missing include files."""
    # Create a test file with a missing include
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("#include missing_file.txt\n")
        f.write("○ item1 1d \"Test Item\" {\"chart1\"}\n")
    
    # Load the graph - should handle missing includes gracefully
    graph = load_graph_from_file(test_file)
    
    # Check that the item in the main file was loaded
    assert len(graph.items) == 1
    assert "item1" in graph.items

def test_includes_command():
    """Test the includes command."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        with open("main.txt", "w") as f:
            f.write("#include include1.txt\n")
            f.write("#include include2.txt\n")
            f.write("○ item1 1d \"Item 1\" {\"chart1\"}\n")
        
        with open("include1.txt", "w") as f:
            f.write("○ item2 2d \"Item 2\" {\"chart2\"}\n")
        
        with open("include2.txt", "w") as f:
            f.write("#include include3.txt\n")
            f.write("○ item3 3d \"Item 3\" {\"chart3\"}\n")
        
        with open("include3.txt", "w") as f:
            f.write("○ item4 4d \"Item 4\" {\"chart4\"}\n")
        
        # Run the includes command
        result = runner.invoke(cli, ["includes", "-f", "main.txt"])
        assert result.exit_code == 0
        assert "main.txt" in result.output
        
        # Run with recursive flag
        result = runner.invoke(cli, ["includes", "-f", "main.txt", "-r"])
        assert result.exit_code == 0
        assert "main.txt" in result.output
        assert "include1.txt" in result.output
        assert "include2.txt" in result.output
        assert "include3.txt" in result.output

def test_add_include_command():
    """Test the add-include command."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("○ item1 1d \"Item 1\" {\"chart1\"}\n")
        
        # Run the add-include command
        result = runner.invoke(cli, ["add-include", "-f", "test.txt", "include.txt"])
        assert result.exit_code == 0
        
        # Check that the include directive was added
        with open("test.txt", "r") as f:
            content = f.read()
            assert "#include include.txt" in content
