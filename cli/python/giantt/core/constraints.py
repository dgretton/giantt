import re
from typing import Optional
from enum import Enum
from dataclasses import dataclass
from .duration import Duration, DurationPart

class TimeConstraintType(Enum):
    WINDOW = "window"
    DEADLINE = "deadline"
    RECURRING = "recurring"

class ConsequenceType(Enum):
    SEVERE = "severe"
    WARNING = "warn"
    ESCALATING = "escalating"

class EscalationRate(Enum):
    LOWEST = ",,,"
    LOW = "..."
    NEUTRAL = ""
    UNSURE = "?"
    MEDIUM = "!"
    HIGH = "!!"
    CRITICAL = "!!!"


@dataclass
class TimeWindow:
    """Represents a time window with an optional grace period."""
    window: DurationPart
    grace_period: Optional[DurationPart] = None

    @classmethod
    def parse(cls, window_str: str) -> 'TimeWindow':
        """Parse a time window string.
        
        Args:
            window_str: String like '5d' or '5d:2d' (with grace period)
            
        Returns:
            TimeWindow object
        """
        parts = window_str.split(':')
        window = DurationPart.parse(parts[0])
        grace_period = DurationPart.parse(parts[1]) if len(parts) > 1 else None
        return cls(window, grace_period)

    def __str__(self) -> str:
        """String representation of time window."""
        base = str(self.window)
        if self.grace_period:
            base += f":{self.grace_period}"
        return base


@dataclass
class TimeConstraint:
    type: TimeConstraintType
    duration: Duration
    grace_period: Optional[Duration] = None
    consequence_type: ConsequenceType = ConsequenceType.WARNING
    escalation_rate: EscalationRate = EscalationRate.NEUTRAL
    due_date: Optional[str] = None
    interval: Optional[Duration] = None
    stack: bool = False

    @classmethod
    def from_string(cls, constraint_str: str) -> Optional['TimeConstraint']:
        if not constraint_str:
            return None
            
        # Parse window constraints
        window_match = re.match(r'window\((\d+[smhdwy])(:\d+[smhdwy])?,([^)]+)\)', constraint_str)
        if window_match:
            window = Duration.parse(window_match.group(1))
            grace = Duration.parse(window_match.group(2)[1:]) if window_match.group(2) else None
            consequence = cls._parse_consequence(window_match.group(3))
            
            return cls(
                type=TimeConstraintType.WINDOW,
                duration=window,
                grace_period=grace,
                consequence_type=consequence['type'],
                escalation_rate=consequence['rate']
            )
            
        # Parse deadline constraints
        deadline_match = re.match(r'due\((\d{4}-\d{2}-\d{2})(:\d+[smhdwy])?,([^)]+)\)', constraint_str)
        if deadline_match:
            due_date = deadline_match.group(1)
            grace = Duration.parse(deadline_match.group(2)[1:]) if deadline_match.group(2) else None
            consequence = cls._parse_consequence(deadline_match.group(3))
            
            return cls(
                type=TimeConstraintType.DEADLINE,
                duration=Duration.parse('1d'), # Default to 1 day for deadline
                grace_period=grace,
                consequence_type=consequence['type'],
                escalation_rate=consequence['rate'],
                due_date=due_date
            )
            
        # Parse recurring constraints
        recurring_match = re.match(r'every\((\d+[smhdwy])(:\d+[smhdwy])?,([^)]+)\)', constraint_str)
        if recurring_match:
            interval = Duration.parse(recurring_match.group(1))
            grace = Duration.parse(recurring_match.group(2)[1:]) if recurring_match.group(2) else None
            consequence_str = recurring_match.group(3)
            
            stack = 'stack' in consequence_str
            consequence_str = consequence_str.replace(',stack', '')
            consequence = cls._parse_consequence(consequence_str)
            
            return cls(
                type=TimeConstraintType.RECURRING,
                duration=interval,
                grace_period=grace,
                consequence_type=consequence['type'],
                escalation_rate=consequence['rate'],
                interval=interval,
                stack=stack
            )
            
        raise ValueError(f"Invalid time constraint format: {constraint_str}")
    
    def __str__(self):
        base_str = {
            TimeConstraintType.WINDOW: f"window({self.duration}",
            TimeConstraintType.DEADLINE: f"due({self.due_date}",
            TimeConstraintType.RECURRING: f"every({self.interval}",
        }[self.type]
        
        if self.grace_period:
            base_str += f":{self.grace_period}"
        
        base_str += f",{self.consequence_type.value}"
        if self.escalation_rate != EscalationRate.NEUTRAL:
            base_str += f",escalate:{self.escalation_rate.value}"
        
        if self.type == TimeConstraintType.RECURRING and self.stack:
            base_str += ",stack"
            
        return base_str + ")"

    @staticmethod
    def _parse_consequence(consequence_str: str) -> dict:
        parts = consequence_str.split(',')
        base_consequence = parts[0].strip()
        
        if len(parts) > 1 and parts[1].startswith('escalate:'):
            rate_str = parts[1][9:]  # Remove 'escalate:'
            return {
                'type': ConsequenceType.ESCALATING,
                'rate': EscalationRate(rate_str) if rate_str else EscalationRate.NEUTRAL
            }
        
        return {
            'type': ConsequenceType(base_consequence),
            'rate': EscalationRate.NEUTRAL
        }
