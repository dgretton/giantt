import re
from dataclasses import dataclass
from typing import List

@dataclass
class DurationPart:
    """Represents a single part of a duration with an amount and unit."""
    amount: float
    unit: str
    
    _UNIT_SECONDS = {
        's': 1,
        'min': 60,
        'h': 3600,
        'hr': 3600,
        'd': 86400,
        'w': 604800,
        'mo': 2592000,  # 30 days
        'y': 31536000,  # 365 days
    }

    _UNIT_NORMALIZE = {
        'hr': 'h',
        'minute': 'min',
        'minutes': 'min',
        'hour': 'h',
        'hours': 'h',
        'day': 'd',
        'days': 'd',
        'week': 'w',
        'weeks': 'w',
        'month': 'mo',
        'months': 'mo',
        'year': 'y',
        'years': 'y'
    }

    def __post_init__(self):
        """Normalize the unit after initialization."""
        self.unit = self._UNIT_NORMALIZE.get(self.unit, self.unit)
        if self.unit not in self._UNIT_SECONDS:
            raise ValueError(f"Invalid duration unit: {self.unit}")

    @property
    def total_seconds(self) -> float:
        """Get total seconds."""
        return self.amount * self._UNIT_SECONDS[self.unit]

    def __str__(self):
        # For whole numbers, display as integers
        amount_str = str(int(self.amount)) if self.amount.is_integer() else f"{self.amount}"
        return f"{amount_str}{self.unit}"


class Duration:
    """Handles compound durations like '6mo8d3.5s'."""
    
    def __init__(self, parts: List[DurationPart] = None):
        self.parts = parts or []

    @classmethod
    def parse(cls, duration_str: str) -> 'Duration':
        """Parse a duration string into a Duration object."""
        if not duration_str:
            raise ValueError("Empty duration string")

        pattern = r'(\d+\.?\d*)([a-zA-Z]+)'
        matches = re.finditer(pattern, duration_str)
        parts = []

        for match in matches:
            amount = float(match.group(1))
            unit = match.group(2)
            parts.append(DurationPart(amount, unit))

        if not parts:
            raise ValueError(f"No valid duration parts found in: {duration_str}")

        return cls(parts)

    def total_seconds(self):
        """Get total duration in seconds."""
        return sum(part.total_seconds for part in self.parts)

    def __str__(self):
        """String representation of duration."""
        if not self.parts:
            return "0s"
        return "".join(str(part) for part in self.parts)

    def __add__(self, other):
        """Add two durations."""
        total_seconds = self.total_seconds() + other.total_seconds()
        
        # Convert back to largest sensible unit
        for unit, seconds in sorted(self._UNIT_SECONDS.items(), 
                                  key=lambda x: x[1], reverse=True):
            if total_seconds >= seconds:
                amount = total_seconds / seconds
                if amount.is_integer():
                    amount = int(amount)
                return Duration([DurationPart(amount, unit)])
                
        return Duration([DurationPart(total_seconds, 's')])

    def __eq__(self, other):
        """Compare two durations."""
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() == other.total_seconds()

    def __lt__(self, other):
        """Compare two durations."""
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() < other.total_seconds()

    def __gt__(self, other):
        """Compare two durations."""
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() > other.total_seconds()

    def __le__(self, other):
        """Compare two durations."""
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() <= other.total_seconds()

    def __ge__(self, other):
        """Compare two durations."""
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() >= other.total_seconds()
