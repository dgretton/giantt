from typing import List, Optional, Tuple, Dict, Set
from dataclasses import dataclass, field
import re
from enum import Enum
import json
from .duration import Duration
from .constraints import TimeConstraint


class Status(Enum):
    NOT_STARTED = "○"
    IN_PROGRESS = "◑"
    BLOCKED = "⊘"
    COMPLETED = "●"

class Priority(Enum):
    LOWEST = ",,,"
    LOW = "..."
    NEUTRAL = ""
    UNSURE = "?"
    MEDIUM = "!"
    HIGH = "!!"
    CRITICAL = "!!!"

class RelationType(Enum):
    REQUIRES = "⊢"
    UNLOCKS = "►"
    SUPERCHARGES = "≫"
    INDICATES = "∴"
    BEFORE = "↶"
    WITH = "∪"
    CONFLICTS = "⊗"


@dataclass
class GianttItem:
    id: str
    title: str = ""
    description: str = ""
    status: Status = Status.NOT_STARTED
    priority: Priority = Priority.NEUTRAL
    duration: Duration = Duration()
    charts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    relations: dict = field(default_factory=dict)
    time_constraint: Optional[TimeConstraint] = None
    user_comment: Optional[str] = None
    auto_comment: Optional[str] = None

    # type-check everything
    def __init__(self, id: str, title: str, description: str, status: Status, priority: Priority, duration: Duration, charts: List[str], tags: List[str], relations: dict, time_constraint: Optional[TimeConstraint], user_comment: Optional[str], auto_comment: Optional[str]):
        if not isinstance(id, str):
            raise TypeError(f"id must be a string, not {type(id)}")
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, not {type(title)}")
        if not isinstance(description, str):
            raise TypeError(f"description must be a string, not {type(description)}")
        if not isinstance(status, Status):
            raise TypeError(f"status must be a Status, not {type(status)}")
        if not isinstance(priority, Priority):
            raise TypeError(f"priority must be a Priority, not {type(priority)}")
        if not isinstance(duration, Duration):
            raise TypeError(f"duration must be a Duration, not {type(duration)}")
        if not isinstance(charts, list):
            raise TypeError(f"charts must be a list, not {type(charts)}")
        if not all(isinstance(i, str) for i in charts):
            raise TypeError(f"all elements of charts must be a string")
        if not isinstance(tags, list):
            raise TypeError(f"tags must be a list, not {type(tags)}")
        if not all(isinstance(i, str) for i in tags):
            raise TypeError(f"all elements of tags must be a string")
        if not isinstance(relations, dict):
            raise TypeError(f"relations must be a dict, not {type(relations)}")
        if not all(isinstance(k, str) for k in relations.keys()):
            raise TypeError(f"all keys of relations must be a string")
        if not all(isinstance(v, list) for v in relations.values()):
            raise TypeError(f"all values of relations must be a list")
        if not all(all(isinstance(i, str) for i in v) for v in relations.values()):
            raise TypeError(f"all elements of all values of relations must be a string")
        if not isinstance(time_constraint, (TimeConstraint, type(None))):
            raise TypeError(f"time_constraint must be a TimeConstraint or None, not {type(time_constraint)}")
        if not isinstance(user_comment, (str, type(None))):
            raise TypeError(f"user_comment must be a string or None, not {type(user_comment)}")
        if not isinstance(auto_comment, (str, type(None))):
            raise TypeError(f"auto_comment must be a string or None, not {type(auto_comment)}")
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.duration = duration
        self.charts = charts
        self.tags = tags
        self.relations = relations
        self.time_constraint = time_constraint
        self.user_comment = user_comment
        self.auto_comment = auto_comment

    def copy(self):
        return GianttItem(
            self.id,
            self.title,
            self.description,
            self.status,
            self.priority,
            self.duration,
            self.charts.copy(),
            self.tags.copy(),
            self.relations.copy(),
            self.time_constraint,
            self.user_comment,
            self.auto_comment
        )


@dataclass
class GianttItem:
    id: str
    title: str = ""
    description: str = ""
    status: Status = Status.NOT_STARTED
    priority: Priority = Priority.NEUTRAL
    duration: Duration = Duration()
    charts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    relations: dict = field(default_factory=dict)
    time_constraint: Optional[TimeConstraint] = None
    user_comment: Optional[str] = None
    auto_comment: Optional[str] = None

    @classmethod
    def from_string(cls, line: str) -> 'GianttItem':
        """Parse a line into a GianttItem."""
        line = line.strip()
        
        # Parse the pre-title section
        pre_title = line[:line.find('"')].strip()
        status_str, id_priority_str, duration_str = parse_pre_title_section(pre_title)
        status = Status(status_str)
        
        # Parse the title
        title_start = line.find('"')
        title_end = line.find('"', title_start + 1)
        while title_end != -1 and line[title_end - 1] == '\\':
            title_end = line.find('"', title_end + 1)
        
        if title_end == -1:
            raise ValueError("No ending quote found for title")

        title = json.loads(line[title_start:title_end + 1])
        post_title = line[title_end + 1:].strip()

        # Extract ID and priority
        priority_symbols = ['!!!', '!!', '!', '?', '...', ',,,']
        id_str = id_priority_str
        priority = ''
        for symbol in priority_symbols:
            if id_priority_str.endswith(symbol):
                id_str = id_priority_str[:-len(symbol)]
                priority = symbol
                break
        # must be type Priority
        priority = Priority(priority)

        # Parse duration
        duration = Duration.parse(duration_str)

        # Parse post-title section
        charts_pattern = re.compile(r'^\s*(\{[^}]+\})\s*(.*)$')
        charts_match = charts_pattern.match(post_title)
        if not charts_match:
            raise ValueError("Invalid charts format")
        
        charts_str = charts_match.group(1)
        remainder = charts_match.group(2)

        # Split remainder into tags, relations, and constraints
        parts = remainder.split('>>>')
        tags_str = parts[0].strip()
        relations_str = parts[1].strip() if len(parts) > 1 else ""

        # Split relations section into relations and time constraints
        constraint_parts = relations_str.split('@@@')
        relations_str = constraint_parts[0].strip()
        time_constraint_str = constraint_parts[1].strip() if len(constraint_parts) > 1 else None

        # Parse charts
        charts = [c.strip().strip('"') for c in charts_str[1:-1].split(",") if c.strip()]
        
        # Parse tags
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        
        # Parse relations
        relations = {}
        rel_symbols = {'⊢': 'REQUIRES', '►': 'UNLOCKS', '≫': 'SUPERCHARGES',
                      '∴': 'INDICATES', '↶': 'BEFORE', '∪': 'WITH', '⊗': 'CONFLICTS'}
        
        for symbol, rel_type in rel_symbols.items():
            pattern = f"{symbol}\\[([^]]+)\\]"
            matches = re.findall(pattern, relations_str)
            if matches:
                relations[rel_type] = [t.strip() for t in matches[0].split(",")]

        return cls(
            id=id_str,
            title=title,
            description="",  # Not currently supported
            status=status,
            priority=priority,
            duration=duration,
            charts=charts,
            tags=tags,
            relations=relations,
            time_constraint=time_constraint_str,
            user_comment=None,
            auto_comment=None
        )


    def to_string(self) -> str:
        charts_str = '{"' + '","'.join(self.charts) + '"}'
        tags_str = ' ' + ','.join(self.tags) if self.tags else ""
        
        rel_parts = []
        for rel_type, targets in self.relations.items():
            if targets:
                symbol = RelationType[rel_type].value
                rel_parts.append(f"{symbol}[{','.join(targets)}]")
        relations_str = ' >>> ' + ' '.join(rel_parts) if rel_parts else ""

        # JSON encode the title to handle special characters properly
        title_str = json.dumps(self.title)

        user_comment_str = f" # {self.user_comment}" if self.user_comment else ""
        auto_comment_str = f" ### {self.auto_comment}" if self.auto_comment else ""

        return f"{self.status.value} {self.id}{self.priority.value} {self.duration} {title_str} {charts_str}{tags_str}{relations_str}{user_comment_str}{auto_comment_str}"

    def copy(self):
        return GianttItem(
            self.id,
            self.title,
            self.description,
            self.status,
            self.priority,
            self.duration,
            self.charts.copy(),
            self.tags.copy(),
            self.relations.copy(),
            self.time_constraint,
            self.user_comment,
            self.auto_comment
        )

class CycleDetectedException(Exception):
    def __init__(self, cycle_items):
        self.cycle_items = cycle_items
        cycle_str = " -> ".join(cycle_items)
        super().__init__(f"Cycle detected in dependencies: {cycle_str}")


class GianttGraph:
    def __init__(self):
        self.items: dict[str, GianttItem] = {}
        
    def add_item(self, item: GianttItem):
        self.items[item.id] = item
        
    def find_by_substring(self, substring: str) -> GianttItem:
        matches = [item for item in self.items.values() if substring.lower() in item.title.lower() or substring == item.id]
        if not matches:
            raise ValueError(f"No items found matching '{substring}'")
        if len(matches) > 1:
            raise ValueError(f"Multiple matches found: {', '.join(item.id for item in matches)}")
        return matches[0]

    def safe_topological_sort(self, in_memory_copy=None):
        """
        Performs a safe topological sort that detects cycles and provides detailed error information.
        
        Args:
            items: Dictionary mapping item IDs to their GianttItem objects
            in_memory_copy: Optional dictionary to use for sorting attempt (to avoid modifying original)
            
        Returns:
            List of sorted GianttItem objects
            
        Raises:
            CycleDetectedException: If a dependency cycle is detected, with details about the cycle
        """
        # Build adjacency list for strict relations
        adj_list = {item.id: set() for item in self.items.values()}
        for item in self.items.values():
            for rel_type in ['REQUIRES']:
                if rel_type in item.relations:
                    for target in item.relations[rel_type]:
                        if target not in adj_list:
                            continue # Skip non-existent items
                        adj_list[item.id].add(target)

        # Calculate in-degrees
        in_degree = {node: 0 for node in adj_list}
        for node in adj_list:
            for neighbor in adj_list[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        # Find nodes with no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        sorted_items = []
        visited = set()

        while queue:
            node = queue.pop(0)
            sorted_items.append(self.items[node])
            visited.add(node)
            
            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we haven't visited all nodes, there must be a cycle
        if len(sorted_items) != len(self.items):
            # Find the cycle for better error reporting
            def find_cycle():
                unvisited = set(self.items.keys()) - visited
                stack = []
                path = []
                
                def dfs(current):
                    if current in stack:
                        cycle_start = stack.index(current)
                        return stack[cycle_start:]
                    if current in visited:
                        return None
                        
                    stack.append(current)
                    for neighbor in adj_list[current]:
                        cycle = dfs(neighbor)
                        if cycle:
                            return cycle
                    stack.pop()
                    return None

                # Start DFS from any unvisited node
                start_node = next(iter(unvisited))
                cycle = dfs(start_node)
                if cycle:
                    # Add one more occurrence of first node to show complete cycle
                    cycle.append(cycle[0])
                return cycle or []

            cycle = find_cycle()
            raise CycleDetectedException(cycle)

        sorted_items.reverse()
        return sorted_items

    def insert_between(self, new_item: GianttItem, before_id: str, after_id: str):
        if before_id not in self.items or after_id not in self.items:
            raise ValueError("Both before and after items must exist")

        before_item = self.items[before_id]
        after_item = self.items[after_id]

        # Update relations
        new_item.relations['REQUIRES'] = [before_id]
        new_item.relations['UNLOCKS'] = [after_id]

        # Update existing items
        if 'UNLOCKS' in before_item.relations:
            before_item.relations['UNLOCKS'].remove(after_id)
            before_item.relations['UNLOCKS'].append(new_item.id)

        if 'REQUIRES' in after_item.relations:
            after_item.relations['REQUIRES'].remove(before_id)
            after_item.relations['REQUIRES'].append(new_item.id)

        self.add_item(new_item)

    def copy(self):
        new_graph = GianttGraph()
        for item in self.items.values():
            new_graph.add_item(item.copy())
        return new_graph

