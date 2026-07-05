"""
Alias Tracker — records which variables are aliases of one another.

When ``x = y`` is encountered the tracker records that *x* aliases *y*,
so any taint on *y* also applies to *x*.
"""

from __future__ import annotations

from typing import Dict, Set, Optional


class AliasTracker:
    """Tracks variable aliasing within a single scope/module."""

    def __init__(self):
        # alias_map: variable_name -> set of names it is aliased to
        self._alias_map: Dict[str, Set[str]] = {}

    def record_alias(self, new_name: str, original_name: str) -> None:
        """Record that *new_name* is an alias for *original_name*."""
        if new_name not in self._alias_map:
            self._alias_map[new_name] = set()
        self._alias_map[new_name].add(original_name)

        # transitive: if original already has aliases, propagate
        if original_name in self._alias_map:
            self._alias_map[new_name].update(self._alias_map[original_name])

    def get_aliases(self, name: str) -> Set[str]:
        """Return all names that *name* is aliased to (direct + transitive)."""
        visited: Set[str] = set()
        queue = [name]
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            for alias_target in self._alias_map.get(current, set()):
                if alias_target not in visited:
                    queue.append(alias_target)
            # reverse lookup: anything that aliases current
            for src, targets in self._alias_map.items():
                if current in targets and src not in visited:
                    queue.append(src)
        visited.discard(name)
        return visited

    def are_aliases(self, name_a: str, name_b: str) -> bool:
        return name_b in self.get_aliases(name_a)

    def all_tracked(self) -> Dict[str, Set[str]]:
        return dict(self._alias_map)
