from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Set

class IssueType(Enum):
    DANGLING_REFERENCE = "dangling_reference"
    ORPHANED_ITEM = "orphaned_item"
    INCOMPLETE_CHAIN = "incomplete_chain"
    CHART_INCONSISTENCY = "chart_inconsistency"
    TAG_INCONSISTENCY = "tag_inconsistency"

@dataclass
class Issue:
    type: IssueType
    item_id: str
    message: str
    related_ids: List[str]
    suggested_fix: Optional[str] = None

class GianttDoctor:
    def __init__(self, graph: 'GianttGraph'):
        self.graph = graph
        self.issues: List[Issue] = []
    
    def quick_check(self) -> int:
        """Run a quick check and return number of issues found."""
        self.issues = []
        self._check_relations()
        return len(self.issues)
    
    def full_diagnosis(self) -> List[Issue]:
        """Run all checks and return detailed issues."""
        self.issues = []
        self._check_relations()
        self._check_orphans()
        self._check_chains()
        self._check_charts()
        self._check_tags()
        return self.issues

    def _check_relations(self):
        """Check for dangling references in relations."""
        for item_id, item in self.graph.items.items():
            for rel_type, targets in item.relations.items():
                for target in targets:
                    if target not in self.graph.items:
                        self.issues.append(Issue(
                            type=IssueType.DANGLING_REFERENCE,
                            item_id=item_id,
                            message=f"References non-existent item '{target}' in {rel_type.lower()} relation",
                            related_ids=[target],
                            suggested_fix=f"giantt modify {item_id} {rel_type.lower()} {','.join(t for t in targets if t in self.graph.items)}"
                        ))

    def _check_orphans(self):
        """Find items with no incoming or outgoing relations."""
        for item_id, item in self.graph.items.items():
            has_incoming = any(
                target == item_id
                for other in self.graph.items.values()
                for targets in other.relations.values()
                for target in targets
            )
            has_outgoing = bool(item.relations)
            
            if not has_incoming and not has_outgoing:
                self.issues.append(Issue(
                    type=IssueType.ORPHANED_ITEM,
                    item_id=item_id,
                    message="Item has no relations to other items",
                    related_ids=[],
                    suggested_fix="Consider connecting this item to related tasks"
                ))

    def _check_chains(self):
        """Check for incomplete dependency chains."""
        unlocks_map = {
            item_id: set(targets)
            for item_id, item in self.graph.items.items()
            for targets in [item.relations.get('UNLOCKS', [])]
        }
        requires_map = {
            item_id: set(targets)
            for item_id, item in self.graph.items.items()
            for targets in [item.relations.get('REQUIRES', [])]
        }
        
        # Check for items that unlock something but aren't required by it
        for item_id, unlocked_items in unlocks_map.items():
            for unlocked in unlocked_items:
                if unlocked in self.graph.items:
                    if item_id not in requires_map.get(unlocked, set()):
                        self.issues.append(Issue(
                            type=IssueType.INCOMPLETE_CHAIN,
                            item_id=item_id,
                            message=f"Item unlocks '{unlocked}' but isn't required by it",
                            related_ids=[unlocked],
                            suggested_fix=f"giantt modify {unlocked} requires {item_id}"
                        ))

    def _check_charts(self):
        """Check for chart consistency issues."""
        # Find all unique charts
        all_charts = set()
        chart_items: Dict[str, Set[str]] = {}
        
        for item_id, item in self.graph.items.items():
            for chart in item.charts:
                all_charts.add(chart)
                if chart not in chart_items:
                    chart_items[chart] = set()
                chart_items[chart].add(item_id)
        
        # Check for items that should probably be in certain charts
        for chart in all_charts:
            chart_set = chart_items[chart]
            for item_id in chart_set:
                item = self.graph.items[item_id]
                # Check if any required items or unlocked items in this chart
                # aren't also in this chart
                related_items = set(item.relations.get('REQUIRES', []) + 
                                 item.relations.get('UNLOCKS', []))
                for related_id in related_items:
                    if (related_id in self.graph.items and 
                        related_id not in chart_set and
                        any(c == chart for c in self.graph.items[related_id].charts)):
                        self.issues.append(Issue(
                            type=IssueType.CHART_INCONSISTENCY,
                            item_id=related_id,
                            message=f"Item is related to items in chart '{chart}' but isn't in it",
                            related_ids=[item_id],
                            suggested_fix=f"giantt modify {related_id} charts {','.join(self.graph.items[related_id].charts + [chart])}"
                        ))

    def _check_tags(self):
        """Check for tag consistency issues."""
        # Find all unique tags
        all_tags = set()
        tag_items: Dict[str, Set[str]] = {}
        
        for item_id, item in self.graph.items.items():
            for tag in item.tags:
                all_tags.add(tag)
                if tag not in tag_items:
                    tag_items[tag] = set()
                tag_items[tag].add(item_id)
        
        # Check for items that should probably have certain tags
        for tag in all_tags:
            tag_set = tag_items[tag]
            for item_id in tag_set:
                item = self.graph.items[item_id]
                # Check if any required items with this tag aren't also tagged
                related_items = set(item.relations.get('REQUIRES', []) + 
                                 item.relations.get('UNLOCKS', []))
                for related_id in related_items:
                    if (related_id in self.graph.items and 
                        related_id not in tag_set and
                        any(t == tag for t in self.graph.items[related_id].tags)):
                        self.issues.append(Issue(
                            type=IssueType.TAG_INCONSISTENCY,
                            item_id=related_id,
                            message=f"Item is related to items with tag '{tag}' but doesn't have it",
                            related_ids=[item_id],
                            suggested_fix=f"giantt modify {related_id} tags {','.join(self.graph.items[related_id].tags + [tag])}"
                        ))
