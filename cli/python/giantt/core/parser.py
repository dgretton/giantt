from typing import Tuple, List, Dict, Optional
import re
import json
from dataclasses import dataclass
from enum import Enum

from .models import (
    GianttItem, GianttGraph,
    Status, Priority, RelationType,
)
from .duration import Duration, DurationPart
from .constraints import (
    TimeConstraint, TimeConstraintType,
    ConsequenceType, EscalationRate
)

class ParseError(Exception):
    """Raised when parsing fails"""
    def __init__(self, message: str, line: str, position: Optional[int] = None):
        self.message = message
        self.line = line
        self.position = position
        super().__init__(f"{message}\nLine: {line}" + 
                        (f"\nPosition: {position}" if position else ""))

@dataclass
class ParsedComponents:
    """Container for parsed components before creating a GianttItem"""
    status: Status
    id: str
    priority: Priority
    duration: Duration
    title: str
    charts: List[str]
    tags: List[str]
    relations: Dict[str, List[str]]
    time_constraint: Optional[TimeConstraint] = None
    user_comment: Optional[str] = None
    auto_comment: Optional[str] = None

class GianttParser:
    """
    Handles parsing and formatting of Giantt text format.
    
    Usage:
        parser = GianttParser()
        
        # Parse a file
        with open('GIANTT_ITEMS.txt', 'r') as f:
            graph = parser.parse_file(f)
            
        # Format a graph
        with open('GIANTT_ITEMS.txt', 'w') as f:
            parser.write_file(graph, f)
            
        # Parse a single line
        item = parser.parse_line("○ task1 1d \"Task\" {\"Basic\"}")
        
        # Format a single item
        line = parser.format_item(item)
    """
    
    # Regex patterns
    _TITLE_PATTERN = re.compile(r'^([^"]*)"((?:[^"\\]|\\.)*)"(.*)$')
    _CHARTS_PATTERN = re.compile(r'^\s*(\{[^}]+\})\s*(.*)$')
    
    @classmethod
    def parse_file(cls, file) -> GianttGraph:
        """Parse a complete Giantt file into a graph"""
        parser = cls()
        graph = GianttGraph()
        
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                item = parser.parse_line(line)
                graph.add_item(item)
            except ParseError as e:
                raise ParseError(f"Error on line {line_num}: {e.message}", line)
                
        return graph
    
    @classmethod
    def write_file(cls, graph: GianttGraph, file) -> None:
        """Write a graph to a file in Giantt format"""
        parser = cls()
        
        # Write header
        file.write(cls._create_header())
        file.write("\n\n")
        
        # Write items in topological order
        sorted_items = graph.safe_topological_sort()
        for item in sorted_items:
            file.write(parser.format_item(item) + "\n")
    
    def parse_line(self, line: str) -> GianttItem:
        """Parse a single line into a GianttItem"""
        components = self._parse_components(line)
        return GianttItem(
            id=components.id,
            title=components.title,
            status=components.status,
            priority=components.priority,
            duration=components.duration,
            charts=components.charts,
            tags=components.tags,
            relations=components.relations,
            time_constraint=components.time_constraint,
            user_comment=components.user_comment,
            auto_comment=components.auto_comment
        )
    
    def format_item(self, item: GianttItem) -> str:
        """Format a GianttItem into a line of text"""
        # Format the pre-title section
        pre_title = f"{item.status.value} {item.id}{item.priority.value} {item.duration}"
        
        # Format the title (JSON-escaped)
        title = json.dumps(item.title)
        
        # Format charts
        charts = f'{{"{ ","".join(json.dumps(c) for c in item.charts) }"}}'
        
        # Format tags
        tags = f" {','.join(item.tags)}" if item.tags else ""
        
        # Format relations
        rel_parts = []
        rel_symbols = {
            'REQUIRES': '⊢', 'UNLOCKS': '►', 'SUPERCHARGES': '≫',
            'INDICATES': '∴', 'BEFORE': '↶', 'WITH': '∪', 'CONFLICTS': '⊗'
        }
        for rel_type, targets in item.relations.items():
            if targets:
                symbol = rel_symbols[rel_type]
                rel_parts.append(f"{symbol}[{','.join(targets)}]")
        relations = f" >>> {' '.join(rel_parts)}" if rel_parts else ""
        
        # Format comments
        user_comment = f" # {item.user_comment}" if item.user_comment else ""
        auto_comment = f" ### {item.auto_comment}" if item.auto_comment else ""
        
        # Combine all parts
        return f"{pre_title} {title} {charts}{tags}{relations}{user_comment}{auto_comment}"

    def _parse_components(self, line: str) -> ParsedComponents:
        """Parse a line into its components"""
        # Parse pre-title, title, and post-title sections
        pre_title, title, post_title = self._split_line(line)
        
        # Parse pre-title section
        status, id_priority, duration_str = self._parse_pre_title(pre_title)
        id_str, priority = self._parse_id_priority(id_priority)
        duration = Duration.parse(duration_str)
        
        # Parse post-title section
        charts, remainder = self._parse_charts(post_title)
        tags, relations_str = self._parse_tags_relations(remainder)
        relations, time_constraint = self._parse_relations(relations_str)
        
        return ParsedComponents(
            status=status,
            id=id_str,
            priority=priority,
            duration=duration,
            title=title,
            charts=charts,
            tags=tags,
            relations=relations,
            time_constraint=time_constraint
        )

    def _split_line(self, line: str) -> Tuple[str, str, str]:
        """Split a line into pre-title, title, and post-title sections"""
        match = self._TITLE_PATTERN.match(line)
        if not match:
            raise ParseError("Could not find valid JSON-encoded title", line)
            
        pre_title = match.group(1).strip()
        title_escaped = match.group(2)
        post_title = match.group(3).strip()
        
        try:
            title = json.loads(f'"{title_escaped}"')
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid title encoding: {str(e)}", title_escaped)
            
        return pre_title, title, post_title

    def _parse_pre_title(self, pre_title: str) -> Tuple[Status, str, str]:
        """Parse the pre-title section into status, id+priority, and duration"""
        parts = pre_title.split()
        if len(parts) < 3:
            raise ParseError("Missing required fields before title", pre_title)
            
        status_sym, id_priority, duration = parts
        try:
            status = Status(status_sym)
        except ValueError:
            raise ParseError(f"Invalid status symbol: {status_sym}", pre_title)
            
        return status, id_priority, duration

    def _parse_id_priority(self, id_priority: str) -> Tuple[str, Priority]:
        """Parse an ID+priority string into separate components"""
        # Order by length to match longest priority first
        priorities = sorted([
            (p.value, p) for p in Priority
        ], key=lambda x: len(x[0]), reverse=True)
        
        for symbol, priority in priorities:
            if id_priority.endswith(symbol):
                return id_priority[:-len(symbol)], priority
                
        return id_priority, Priority.NEUTRAL

    def _parse_charts(self, post_title: str) -> Tuple[List[str], str]:
        """Parse the charts section"""
        match = self._CHARTS_PATTERN.match(post_title)
        if not match:
            raise ParseError("Missing or malformed charts block", post_title)
            
        charts_str = match.group(1)
        remainder = match.group(2)
        
        # Parse chart names
        charts = []
        try:
            chart_contents = charts_str[1:-1].strip()  # Remove outer {}
            if chart_contents:
                charts = [
                    json.loads(c)
                    for c in chart_contents.split(',')
                    if c.strip()
                ]
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid chart name format: {str(e)}", charts_str)
            
        return charts, remainder

    def _parse_tags_relations(self, text: str) -> Tuple[List[str], str]:
        """Split tags and relations sections"""
        parts = text.split('>>>')
        tags_str = parts[0].strip()
        relations_str = parts[1].strip() if len(parts) > 1 else ""
        
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        return tags, relations_str

    def _parse_relations(self, text: str) -> Tuple[Dict[str, List[str]], Optional[TimeConstraint]]:
        """Parse relations and time constraints"""
        constraint_parts = text.split('@@@')
        relations_str = constraint_parts[0].strip()
        constraint_str = constraint_parts[1].strip() if len(constraint_parts) > 1 else None
        
        # Parse relations
        relations = {}
        rel_symbols = {
            '⊢': 'REQUIRES', '►': 'UNLOCKS', '≫': 'SUPERCHARGES',
            '∴': 'INDICATES', '↶': 'BEFORE', '∪': 'WITH', '⊗': 'CONFLICTS'
        }
        
        for symbol, rel_type in rel_symbols.items():
            pattern = f"{symbol}\\[([^]]+)\\]"
            matches = re.findall(pattern, relations_str)
            if matches:
                relations[rel_type] = [
                    t.strip() for t in matches[0].split(",")
                ]
        
        # Parse time constraint if present
        time_constraint = (
            TimeConstraint.from_string(constraint_str)
            if constraint_str else None
        )
        
        return relations, time_constraint

    @staticmethod
    def _create_header() -> str:
        """Create the file header banner"""
        return (
            "########################\n"
            "#                      #\n"
            "#     Giantt Items     #\n"
            "#                      #\n"
            "########################"
        )

def parse_pre_title_section(pre_title: str) -> Tuple[str, str, str]:
    """Parse the pre-title section into status, id+priority, and duration."""
    # Updated pattern to be more flexible with whitespace
    pattern = r'^([○◑⊘●])\s+([^\s]+)\s+([^\s"]+)'
    match = re.match(pattern, pre_title)
    
    if not match:
        raise ValueError(f"Invalid pre-title format: {pre_title}")
        
    status = match.group(1)
    id_priority = match.group(2)
    duration = match.group(3).strip()
    
    return status, id_priority, duration

# Saving this for later, all good stuff but will need to be incorporated into the parser rather than the dataclasses
# @dataclass
# class LogEntry:
#     """A single log entry recording an event or thought."""
#     timestamp: datetime
#     message: str
#     tags: Set[str]
#     metadata: Dict[str, str] = field(default_factory=dict)
    
#     @classmethod
#     def create(cls, message: str, session_tag: str, additional_tags: Optional[List[str]] = None) -> 'LogEntry':
#         """Create a new log entry with current timestamp."""
#         tags = {session_tag}
#         if additional_tags:
#             tags.update(additional_tags)
            
#         return cls(
#             timestamp=datetime.now(timezone.utc),
#             message=message,
#             tags=tags
#         )
    
#     def to_dict(self) -> dict:
#         """Convert to dictionary for serialization."""
#         return {
#             'timestamp': self.timestamp.isoformat(),
#             'message': self.message,
#             'tags': sorted(list(self.tags)),  # Convert set to sorted list for consistent serialization
#             'metadata': self.metadata
#         }
    
#     @classmethod
#     def from_dict(cls, data: dict) -> 'LogEntry':
#         """Create a LogEntry from a dictionary."""
#         return cls(
#             timestamp=datetime.fromisoformat(data['timestamp']),
#             message=data['message'],
#             tags=set(data['tags']),
#             metadata=data.get('metadata', {})
#         )
    
#     def has_tag(self, tag: str) -> bool:
#         """Check if entry has a specific tag."""
#         return tag in self.tags
    
#     def has_any_tags(self, tags: List[str]) -> bool:
#         """Check if entry has any of the specified tags."""
#         return bool(self.tags.intersection(tags))
    
#     def has_all_tags(self, tags: List[str]) -> bool:
#         """Check if entry has all of the specified tags."""
#         return self.tags.issuperset(tags)
    
#     def add_tag(self, tag: str) -> None:
#         """Add a tag to the entry."""
#         self.tags.add(tag)
    
#     def remove_tag(self, tag: str) -> None:
#         """Remove a tag from the entry."""
#         self.tags.discard(tag)


# class LogCollection:
#     """A collection of log entries with query capabilities."""
    
#     def __init__(self, entries: Optional[List[LogEntry]] = None):
#         self.entries = entries or []
    
#     def add_entry(self, entry: LogEntry) -> None:
#         """Add a new entry to the collection."""
#         self.entries.append(entry)
    
#     def create_entry(self, message: str, session_tag: str, additional_tags: Optional[List[str]] = None) -> LogEntry:
#         """Create and add a new entry."""
#         entry = LogEntry.create(message, session_tag, additional_tags)
#         self.add_entry(entry)
#         return entry
    
#     def get_by_session(self, session_tag: str) -> List[LogEntry]:
#         """Get all entries with a specific session tag."""
#         return [entry for entry in self.entries if entry.has_tag(session_tag)]
    
#     def get_by_tags(self, tags: List[str], require_all: bool = False) -> List[LogEntry]:
#         """Get entries with specified tags.
        
#         Args:
#             tags: List of tags to match
#             require_all: If True, entries must have all tags; if False, any tag matches
#         """
#         if require_all:
#             return [entry for entry in self.entries if entry.has_all_tags(tags)]
#         return [entry for entry in self.entries if entry.has_any_tags(tags)]
    
#     def get_by_date_range(self, start: datetime, end: Optional[datetime] = None) -> List[LogEntry]:
#         """Get entries within a date range."""
#         end = end or datetime.now(timezone.utc)
#         return [
#             entry for entry in self.entries 
#             if start <= entry.timestamp <= end
#         ]
    
#     def save_to_file(self, filepath: Path) -> None:
#         """Save all entries to a JSONL file."""
#         with open(filepath, 'w') as f:
#             for entry in self.entries:
#                 json.dump(entry.to_dict(), f)
#                 f.write('\n')
    
#     @classmethod
#     def load_from_file(cls, filepath: Path) -> 'LogCollection':
#         """Load entries from a JSONL file."""
#         entries = []
#         with open(filepath) as f:
#             for line in f:
#                 if line.strip():  # Skip empty lines
#                     try:
#                         data = json.loads(line)
#                         entries.append(LogEntry.from_dict(data))
#                     except json.JSONDecodeError as e:
#                         print(f"Warning: Skipping invalid log entry: {e}")
#         return cls(entries)
    
#     def append_to_file(self, filepath: Path, entry: LogEntry) -> None:
#         """Append a single entry to a JSONL file."""
#         with open(filepath, 'a') as f:
#             json.dump(entry.to_dict(), f)
#             f.write('\n')
    
#     def __len__(self) -> int:
#         return len(self.entries)
    
#     def __iter__(self):
#         return iter(self.entries)
    
#     def __getitem__(self, index):
#         return self.entries[index]