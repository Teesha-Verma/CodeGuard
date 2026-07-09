"""
Repository Intelligence Layer — Architecture Detector.

Detects common software architecture patterns and architectural
components from a collection of file paths.
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List, Set

from app.analysis.repository.constants import (
    Architecture,
    Layer,
    ARCHITECTURE_SIGNALS,
    DIRECTORY_PATTERNS,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
)
from app.analysis.repository.models import ArchitectureInfo


# ═══════════════════════════════════════════════════════════════════
# Component detection patterns
# ═══════════════════════════════════════════════════════════════════

_COMPONENT_PATTERNS: Dict[str, List[str]] = {
    "Controllers": [
        "controllers", "views", "handlers", "endpoints",
    ],
    "Services": [
        "services", "usecases", "use_cases", "interactors",
    ],
    "Models": [
        "models", "entities", "domain",
    ],
    "Utilities": [
        "utils", "utilities", "helpers", "common", "lib",
    ],
    "APIs": [
        "api", "routes", "routers", "endpoints", "graphql",
    ],
    "Infrastructure": [
        "infra", "infrastructure", "deploy", "docker", "k8s",
    ],
    "Domain": [
        "domain", "core", "business",
    ],
    "Repositories": [
        "repositories", "repos", "dao", "persistence",
    ],
    "Tests": [
        "tests", "test", "spec", "specs", "fixtures",
    ],
}


class ArchitectureDetector:
    """Detects architecture patterns and components from file paths.

    Uses directory-name signals defined in
    :data:`~app.analysis.repository.constants.ARCHITECTURE_SIGNALS`
    to score each known :class:`Architecture` variant and returns
    results sorted by descending confidence.
    """

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def detect(self, file_paths: List[str]) -> List[ArchitectureInfo]:
        """Detect architecture patterns present in *file_paths*.

        Parameters
        ----------
        file_paths:
            Iterable of file-path strings (relative or absolute).

        Returns
        -------
        list[ArchitectureInfo]
            One entry per detected architecture, sorted by descending
            confidence.  Architectures with zero confidence are omitted.
        """
        directories: Set[str] = self._extract_directories(file_paths)
        results: List[ArchitectureInfo] = []

        # --- Signal-based architectures ---
        for arch, signals in ARCHITECTURE_SIGNALS.items():
            if not signals:
                # Handled by special-case logic (e.g. PACKAGE_BY_FEATURE).
                continue

            matched: List[str] = [s for s in signals if s in directories]
            if not matched:
                continue

            confidence = self._compute_confidence(
                matched_count=len(matched),
                total_signals=len(signals),
            )
            detected_layers = self._signals_to_layers(matched)

            results.append(
                ArchitectureInfo(
                    architecture=arch,
                    confidence=confidence,
                    detected_layers=detected_layers,
                    detected_directories=matched,
                    signals=signals,
                ),
            )

        # --- Monolith heuristic ---
        monolith_info = self._detect_monolith(file_paths, directories, results)
        if monolith_info is not None:
            results.append(monolith_info)

        # --- Package-by-feature heuristic ---
        pbf_info = self._detect_package_by_feature(file_paths, directories)
        if pbf_info is not None:
            results.append(pbf_info)

        # Sort descending by confidence.
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def detect_components(
        self,
        file_paths: List[str],
    ) -> Dict[str, List[str]]:
        """Detect architectural components and map each to its files.

        Parameters
        ----------
        file_paths:
            Iterable of file-path strings (relative or absolute).

        Returns
        -------
        dict[str, list[str]]
            Mapping of component name (e.g. ``"Controllers"``) to the
            list of file paths that belong to that component.
        """
        components: Dict[str, List[str]] = defaultdict(list)

        for fp in file_paths:
            parts = self._path_parts(fp)
            for component_name, patterns in _COMPONENT_PATTERNS.items():
                if any(p in parts for p in patterns):
                    components[component_name].append(fp)
                    break  # A file belongs to its first-matched component.

        return dict(components)

    # ──────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_directories(file_paths: List[str]) -> Set[str]:
        """Return the set of **lowercased** directory names across all paths."""
        dirs: Set[str] = set()
        for fp in file_paths:
            normalised = fp.replace("\\", "/")
            parts = normalised.split("/")
            # All components except the last (file name).
            for part in parts[:-1]:
                if part:
                    dirs.add(part.lower())
        return dirs

    @staticmethod
    def _path_parts(file_path: str) -> Set[str]:
        """Return all lowercased path components (including file stem)."""
        normalised = file_path.replace("\\", "/")
        parts: Set[str] = set()
        for segment in normalised.split("/"):
            if segment:
                # Add the segment itself and, for the leaf, its stem.
                parts.add(segment.lower())
                stem = segment.rsplit(".", 1)[0].lower()
                if stem:
                    parts.add(stem)
        return parts

    @staticmethod
    def _compute_confidence(
        matched_count: int,
        total_signals: int,
    ) -> float:
        """Derive a confidence score from signal coverage.

        Rules
        -----
        * ratio ≥ 0.75 → :const:`CONFIDENCE_HIGH`
        * ratio ≥ 0.50 → :const:`CONFIDENCE_MEDIUM`
        * ratio ≥ 0.25 → :const:`CONFIDENCE_LOW`
        * otherwise    → ``ratio`` scaled into [0.0, CONFIDENCE_LOW)
        """
        if total_signals == 0:
            return 0.0

        ratio = matched_count / total_signals

        if ratio >= 0.75:
            return CONFIDENCE_HIGH
        if ratio >= 0.50:
            return CONFIDENCE_MEDIUM
        if ratio >= 0.25:
            return CONFIDENCE_LOW
        return round(ratio * CONFIDENCE_LOW, 4)

    @staticmethod
    def _signals_to_layers(signals: List[str]) -> List[Layer]:
        """Map directory signal names to :class:`Layer` values via
        :const:`DIRECTORY_PATTERNS`.
        """
        layers: List[Layer] = []
        seen: Set[Layer] = set()
        for sig in signals:
            category = DIRECTORY_PATTERNS.get(sig)
            if category is not None:
                # FileCategory values intentionally mirror Layer values.
                try:
                    layer = Layer(category.value)
                except ValueError:
                    layer = Layer.UNKNOWN
            else:
                layer = Layer.UNKNOWN

            if layer not in seen:
                seen.add(layer)
                layers.append(layer)
        return layers

    # ──────────────────────────── special-case detectors ──────────

    @staticmethod
    def _detect_monolith(
        file_paths: List[str],
        directories: Set[str],
        already_detected: List[ArchitectureInfo],
    ) -> ArchitectureInfo | None:
        """Heuristic: a monolith is a large codebase with no clear
        service boundaries and no strong signal for other architectures.
        """
        # If another architecture already has high confidence, skip.
        if any(r.confidence >= CONFIDENCE_HIGH for r in already_detected):
            return None

        # Need a meaningful number of files.
        if len(file_paths) < 20:
            return None

        # Absence of microservice markers.
        micro_markers = {"gateway", "discovery", "config-server"}
        if micro_markers & directories:
            return None

        # Count how many distinct "app-like" top-level dirs exist.
        app_dirs = {"app", "src", "application", "project"}
        found_app = app_dirs & directories
        if not found_app:
            return None

        confidence = CONFIDENCE_LOW
        if len(file_paths) >= 100:
            confidence = CONFIDENCE_MEDIUM

        return ArchitectureInfo(
            architecture=Architecture.MONOLITH,
            confidence=confidence,
            detected_layers=[],
            detected_directories=sorted(found_app),
            signals=["large_codebase", "single_app_directory"],
        )

    def _detect_package_by_feature(
        self,
        file_paths: List[str],
        directories: Set[str],
    ) -> ArchitectureInfo | None:
        """Heuristic: package-by-feature is detected when multiple
        top-level directories each contain their own models/services/etc.
        """
        # Gather second-level directories grouped by their parent.
        feature_dirs: Dict[str, Set[str]] = defaultdict(set)
        for fp in file_paths:
            normalised = fp.replace("\\", "/")
            parts = [p for p in normalised.split("/") if p]
            if len(parts) >= 3:
                parent = parts[-3].lower() if len(parts) >= 3 else ""
                child = parts[-2].lower()
                if parent:
                    feature_dirs[parent].add(child)

        # A feature package should have ≥2 of: models, services,
        # views/controllers, schemas, repositories.
        indicator_dirs = {"models", "services", "views", "controllers",
                          "schemas", "repositories", "templates"}
        qualifying_features = 0
        matched_features: List[str] = []

        for parent, children in feature_dirs.items():
            overlap = children & indicator_dirs
            if len(overlap) >= 2:
                qualifying_features += 1
                matched_features.append(parent)

        if qualifying_features < 2:
            return None

        confidence = CONFIDENCE_MEDIUM
        if qualifying_features >= 4:
            confidence = CONFIDENCE_HIGH

        return ArchitectureInfo(
            architecture=Architecture.PACKAGE_BY_FEATURE,
            confidence=confidence,
            detected_layers=[],
            detected_directories=sorted(matched_features),
            signals=["multiple_feature_packages"],
        )
