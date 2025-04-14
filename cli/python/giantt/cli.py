from typing import List, Dict
import click
import shutil

from giantt_core import (
    GianttGraph, GianttItem, 
    Status, Priority, Duration,
    Issue, IssueType, GianttDoctor,
    CycleDetectedException
)

def run_quick_check(graph: GianttGraph) -> None:
    """Run a quick health check after operations."""
    doctor = GianttDoctor(graph)
    issues = doctor.quick_check()
    if issues > 0:
        click.echo(
            click.style(
                f"\n{issues} or more warnings. Run 'giantt doctor' for details.",
                fg='yellow'
            )
        )

def load_file(filename: str) -> GianttGraph:
    # create a backup of the file first
    shutil.copyfile(filename, filename + '.backup')
    graph = GianttGraph()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    item = GianttItem.from_string(line)
                    graph.add_item(item)
                except ValueError as e:
                    click.echo(f"Warning: Skipping invalid line: {e}", err=True)
    return graph

def create_banner(title: str, padding_h: int = 5, padding_v: int = 1):
    """Create a banner of hash characters in a box with the title centered inside."""
    title = f" {title} "
    title_len = len(title)
    banner_len = padding_h * 2 + title_len
    banner = "#" * banner_len + "\n"
    for _ in range(padding_v):
        banner += "#" + " " * (banner_len - 2) + "#\n"
    pad_length_left = (banner_len - title_len) // 2
    if title_len % 2 == 0:
        pad_length_left -= 1
    if pad_length_left < 0:
        pad_length_left = 0
    pad_length_right = banner_len - title_len - pad_length_left - 2
    if pad_length_right < 0:
        pad_length_right = 0
    banner += "#" + " " * pad_length_left + title + " " * pad_length_right + "#\n"
    for _ in range(padding_v):
        banner += "#" + " " * (banner_len - 2) + "#\n"
    banner += "#" * banner_len
    return banner
    
def save_file(filename: str, graph):
    """
    Safely saves the file by first performing a sort in memory
    and a health check.
    
    Args:
        filename: Path to the file to save
        graph: GianttGraph object containing items to save
        
    Raises:
        CycleDetectedException: If dependencies contain a cycle
        ValueError: If dependencies reference non-existent items
    """
    try:
        # First perform the sort in memory to check for issues
        sorted_items = graph.safe_topological_sort()
        
        # If we get here, the sort was successful, so write to file
        with open(filename, "w") as f:
            f.write(create_banner("Giantt Items"))
            f.write("\n\n")
            for item in sorted_items:
                f.write(item.to_string() + "\n")
        
        # Run a quick health check
        run_quick_check(graph)

    except CycleDetectedException as e:
        raise click.ClickException(f"Error: {str(e)}")
    except ValueError as e:
        raise click.ClickException(f"Error: {str(e)}")

@click.group()
def cli():
    """Giantt command line utility for managing task dependencies."""
    pass

# init here

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.argument('substring')
def show(file: str, substring: str):
    """Show details of an item matching the substring."""
    graph = load_file(file)
    # If there is an exact match to an ID, select that item. Otherwise, find by title substring
    if substring in graph.items:
        item = graph.items[substring]
    else:
        item = graph.find_by_substring(substring)
    
    click.echo(f"Title: {item.title}")
    click.echo(f"ID: {item.id}")
    click.echo(f"Status: {item.status.name}")
    click.echo(f"Priority: {item.priority.name}")
    click.echo(f"Duration: {item.duration}")
    click.echo(f"Charts: {', '.join(item.charts)}")
    click.echo(f"Tags: {', '.join(item.tags)}")
    click.echo("Relations:")
    for rel_type, targets in item.relations.items():
        click.echo(f"{rel_type}: {', '.join(targets)}")
    click.echo(f"Time Constraint: {item.time_constraint}")
    click.echo(f"User Comment: {item.user_comment}")
    click.echo(f"Auto Comment: {item.auto_comment}")
    
    for rel_type, targets in item.relations.items():
        click.echo(f"{rel_type}: {', '.join(targets)}")
    
    if item.user_comment:
        click.echo(f"Comment: {item.user_comment}")
    if item.auto_comment:
        click.echo(f"Auto Comment: {item.auto_comment}")

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.argument('substring')
@click.argument('new_status', type=click.Choice([s.name for s in Status]))
def set_status(file: str, substring: str, new_status: str):
    """Set the status of an item."""
    graph = load_file(file)
    item = graph.find_by_substring(substring)
    item.status = Status[new_status]
    save_file(file, graph)

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.argument('id')
@click.argument('title')
@click.option('--duration', default='1d', help='Duration (e.g., 1d, 2w, 3mo)')
@click.option('--priority', type=click.Choice([p.name for p in Priority]), default='NEUTRAL')
@click.option('--charts', help='Comma-separated list of chart names')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--status', type=click.Choice([s.name for s in Status]), default='NOT_STARTED')
@click.option('--requires', help='Comma-separated list of item IDs that this item requires')
@click.option('--unlocks', help='Comma-separated list of item IDs that this item unlocks')
def add(file: str, id: str, title: str, duration: str, priority: str, 
        charts: str, tags: str, status: str, requires: str, unlocks: str):
    """Add a new item to the Giantt chart."""
    graph = load_file(file)
    
    # Validate ID is unique and string search for this ID or title won't conflict with other titles
    for item in graph.items.values():
        if item.id == id:
            raise click.ClickException(f"Item ID '{id}' already exists\n"
                                       f"Existing item: {item.id} - {item.title}")
        if id.lower() in item.title.lower():
            raise click.ClickException(f"Item ID '{id}' conflicts with title of another item\n"
                                       f"Conflicting item: {item.id} - {item.title}")
        if title.lower() in item.title.lower():
            raise click.ClickException(f"Title '{title}' conflicts with title of another item\n"
                                       f"Conflicting item: {item.id} - {item.title}")
    
    # Create relations dict
    relations = {}
    if requires:
        relations['REQUIRES'] = requires.split(',')

    if unlocks:
        relations['UNLOCKS'] = unlocks.split(',')
    
    # Create new item
    try:
        item = GianttItem(
            id=id,
            title=title,
            description="",  # Not currently supported
            status=Status[status],
            priority=Priority[priority],
            duration=Duration.parse(duration),
            charts=charts.split(',') if charts else [],
            tags=tags.split(',') if tags else [],
            relations=relations,
            time_constraint=None,
            user_comment=None,
            auto_comment=None
        )
    except ValueError as e:
        raise click.ClickException(f"Error: {str(e)}")
    
    # Add item
    graph.add_item(item)
    
    # Try to save, catching potential cycle issues
    try:
        save_file(file, graph)
        click.echo(f"Added item '{id}'")
    except CycleDetectedException as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nThe new item would create a dependency cycle. Please revise the relations.", err=True)
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nPlease fix invalid dependencies before adding the item.", err=True)

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.argument('substring')
@click.argument('property')
@click.argument('value')
def modify(file: str, substring: str, property: str, value: str):
    """Modify any property of a Giantt item.
    
    PROPERTY can be one of:
    - title: The item's display title
    - duration: Duration in format like '1d', '2w', '3mo'
    - priority: One of LOWEST, LOW, NEUTRAL, UNSURE, MEDIUM, HIGH, CRITICAL
    - status: One of NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED
    - charts: Comma-separated list of chart names
    - tags: Comma-separated list of tags
    - requires: Comma-separated list of item IDs this item requires
    - unlocks: Comma-separated list of item IDs this item unlocks
    """
    graph = load_file(file)
    item = graph.find_by_substring(substring)
    
    # Handle different property types
    if property == 'title':
        item.title = value
    elif property == 'duration':
        item.duration = Duration.parse(value)
    elif property == 'priority':
        try:
            item.priority = Priority[value.upper()]
        except KeyError:
            raise click.ClickException(f"Invalid priority. Must be one of: {', '.join(p.name for p in Priority)}")
    elif property == 'status':
        try:
            item.status = Status[value.upper()]
        except KeyError:
            raise click.ClickException(f"Invalid status. Must be one of: {', '.join(s.name for s in Status)}")
    elif property == 'charts':
        item.charts = [c.strip() for c in value.split(',') if c.strip()]
    elif property == 'tags':
        item.tags = [t.strip() for t in value.split(',') if t.strip()]
    elif property in ('requires', 'unlocks'):
        # Get existing relations of other types
        new_relations = {
            rel_type: targets 
            for rel_type, targets in item.relations.items() 
            if rel_type != property.upper()
        }
        
        # Add new relations of specified type
        if value:  # Only add if value is non-empty
            target_ids = [t.strip() for t in value.split(',') if t.strip()]

            new_relations[property.upper()] = target_ids

            # Check for cycles when modifying requirements
            if property == 'requires':
                # Create temporary copy of item with new relations
                temp_item = item.copy()
                temp_item.relations = new_relations
                temp_graph = graph.copy()
                temp_graph.items[item.id] = temp_item
                
                try:
                    temp_graph.safe_topological_sort()
                except CycleDetectedException as e:
                    raise click.ClickException(
                        f"Adding these requirements would create a cycle: {' -> '.join(e.cycle_items)}")
        
        item.relations = new_relations
    else:
        raise click.ClickException(
            f"Unknown property '{property}'. Must be one of: title, duration, priority, "
            "status, charts, tags, requires, unlocks")
    
    save_file(file, graph)
    click.echo(f"Modified {property} of item '{item.id}'")

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
def sort(file: str):
    """Sort items in topological order and save."""
    graph = load_file(file)
    try:
        save_file(file, graph)
        click.echo("Successfully sorted and saved items.")
    except CycleDetectedException as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nPlease resolve the cycle before sorting.", err=True)
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nPlease fix invalid dependencies before sorting.", err=True)

@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.argument('new_id')
@click.argument('before_id')
@click.argument('after_id')
@click.option('--charts', help='Comma-separated list of charts')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--duration', default='1d', help='Duration (e.g., 1d, 2w, 3mo2w5d3s)')
@click.option('--priority', type=click.Choice([p.name for p in Priority]), 
              default='NEUTRAL', help='Priority level')
def insert(file: str, new_id: str, before_id: str, after_id: str,
          charts: str, tags: str, duration: str, priority: str):
    """Insert a new item between two existing items."""
    graph = load_file(file)
    
    try:
        new_item = GianttItem(
            id=new_id,
            priority=Priority[priority],
            duration=duration,
            charts=charts.split(',') if charts else [],
            tags=tags.split(',') if tags else []
        )
    except ValueError as e:
        raise click.ClickException(f"Error: {str(e)}")
    
    graph.insert_between(new_item, before_id, after_id)
    save_file(file, graph)


@cli.command()
@click.option('--file', '-f', default='GIANTT_ITEMS.txt', help='Giantt items file to use')
@click.option('--fix/--no-fix', default=False, help='Attempt to automatically fix issues')
def doctor(file: str, fix: bool):
    """Check the health of the Giantt graph and optionally fix issues."""
    graph = load_file(file)
    doctor = GianttDoctor(graph)
    issues = doctor.full_diagnosis()
    
    if not issues:
        click.echo(click.style("✓ Graph is healthy!", fg='green'))
        return
    
    # Group issues by type
    issues_by_type: Dict[IssueType, List[Issue]] = {}
    for issue in issues:
        if issue.type not in issues_by_type:
            issues_by_type[issue.type] = []
        issues_by_type[issue.type].append(issue)
    
    # Print issues
    click.echo(click.style(f"\nFound {len(issues)} issue" + ("s" if len(issues) != 1 else "") + ":", fg='yellow'))
    for issue_type, type_issues in issues_by_type.items():
        click.echo(f"\n{issue_type.value} ({len(type_issues)} issues):")
        for issue in type_issues:
            click.echo(f"  • {issue.item_id}: {issue.message}")
            if issue.suggested_fix:
                click.echo(f"    Suggested fix: {issue.suggested_fix}")
    
    if fix:
        click.echo("\nAttempting to fix issues...")
        # TODO: Implement auto-fixing logic
        click.echo("Auto-fixing not yet implemented")

if __name__ == '__main__':
    cli()