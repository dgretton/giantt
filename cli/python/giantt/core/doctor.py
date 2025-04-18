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
        self.fixed_issues: List[Issue] = []
    
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
        
    def get_issues_by_type(self, issue_type: IssueType) -> List[Issue]:
        """Get all issues of a specific type."""
        return [issue for issue in self.issues if issue.type == issue_type]
    
    def fix_issues(self, issue_type: Optional[IssueType] = None, item_id: Optional[str] = None) -> List[Issue]:
        """Fix issues of a specific type or for a specific item."""
        # Filter issues to fix
        issues_to_fix = self.issues
        if issue_type:
            issues_to_fix = [issue for issue in issues_to_fix if issue.type == issue_type]
        if item_id:
            issues_to_fix = [issue for issue in issues_to_fix if issue.item_id == item_id]
            
        fixed = []
        for issue in issues_to_fix:
            if self._fix_issue(issue):
                fixed.append(issue)
                
        # Remove fixed issues from the issues list
        for issue in fixed:
            if issue in self.issues:
                self.issues.remove(issue)
                
        self.fixed_issues.extend(fixed)
        return fixed
    
    def _fix_issue(self, issue: Issue) -> bool:
        """Fix a specific issue. Returns True if fixed, False otherwise."""
        if issue.type == IssueType.DANGLING_REFERENCE:
            return self._fix_dangling_reference(issue)
        elif issue.type == IssueType.INCOMPLETE_CHAIN:
            return self._fix_incomplete_chain(issue)
        elif issue.type == IssueType.CHART_INCONSISTENCY:
            return self._fix_chart_inconsistency(issue)
        elif issue.type == IssueType.TAG_INCONSISTENCY:
            return self._fix_tag_inconsistency(issue)
        return False

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
                            suggested_fix=f"giantt modify {item_id} --remove {rel_type.lower()} {target}"
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
                        
    def _fix_dangling_reference(self, issue: Issue) -> bool:
        """Fix a dangling reference issue by removing the reference."""
        item = self.graph.items.get(issue.item_id)
        if not item:
            return False
            
        # Find the relation type and target from the message
        rel_type = None
        target = None
        for rel_name in ['REQUIRES', 'ANYOF', 'SUPERCHARGES', 'INDICATES', 'TOGETHER', 'CONFLICTS', 'BLOCKS', 'SUFFICIENT']:
            if rel_name.lower() in issue.message.lower():
                rel_type = rel_name
                break
                
        if not rel_type:
            return False
            
        # Extract the target ID from the message
        import re
        match = re.search(r"non-existent item '([^']+)'", issue.message)
        if not match:
            return False
            
        target = match.group(1)
        
        # Remove the dangling reference
        if rel_type in item.relations and target in item.relations[rel_type]:
            item.relations[rel_type].remove(target)
            if not item.relations[rel_type]:
                del item.relations[rel_type]
            return True
            
        return False
        
    def _fix_incomplete_chain(self, issue: Issue) -> bool:
        """Fix an incomplete chain issue by adding the missing relation."""
        if not issue.related_ids or not issue.suggested_fix:
            return False
            
        item = self.graph.items.get(issue.item_id)
        related_item = self.graph.items.get(issue.related_ids[0])
        if not item or not related_item:
            return False
            
        # Parse the suggested fix to determine what to do
        parts = issue.suggested_fix.split()
        if len(parts) < 5:
            return False
            
        target_id = parts[2]
        action = parts[3]
        rel_type = parts[4].upper() if len(parts) > 4 else None
        
        if target_id != issue.item_id and target_id != issue.related_ids[0]:
            return False
            
        if "--add" in action.lower() and rel_type:
            target_item = self.graph.items.get(target_id)
            if not target_item:
                return False
                
            # Add the relation
            target_item.relations.setdefault(rel_type, [])
            if parts[5] not in target_item.relations[rel_type]:
                target_item.relations[rel_type].append(parts[5])
            return True
            
        return False
        
    def _fix_chart_inconsistency(self, issue: Issue) -> bool:
        """Fix a chart inconsistency by adding the item to the chart."""
        if not issue.related_ids or not issue.suggested_fix:
            return False
            
        item = self.graph.items.get(issue.item_id)
        if not item:
            return False
            
        # Extract chart name from message
        import re
        match = re.search(r"chart '([^']+)'", issue.message)
        if not match:
            return False
            
        chart_name = match.group(1)
        
        # Add the chart to the item
        if chart_name not in item.charts:
            item.charts.append(chart_name)
            return True
            
        return False
        
    def _fix_tag_inconsistency(self, issue: Issue) -> bool:
        """Fix a tag inconsistency by adding the tag to the item."""
        if not issue.related_ids or not issue.suggested_fix:
            return False
            
        item = self.graph.items.get(issue.item_id)
        if not item:
            return False
            
        # Extract tag name from message
        import re
        match = re.search(r"tag '([^']+)'", issue.message)
        if not match:
            return False
            
        tag_name = match.group(1)
        
        # Add the tag to the item
        if tag_name not in item.tags:
            item.tags.append(tag_name)
            return True
            
        return False
