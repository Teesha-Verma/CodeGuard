"""
Repository Intelligence Layer — Layer Violation Detector.

Detects violations of architectural layering rules by inspecting the
dependency graph against configurable forbidden-import policies.
"""

from __future__ import annotations

import logging
from typing import Dict, FrozenSet, List, Optional

from app.analysis.repository.constants import (
    LAYER_RULES,
    Layer,
    Severity,
)
from app.analysis.repository.models import FileClassification, LayerViolation

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Severity mapping for specific layer→layer violations
# ═══════════════════════════════════════════════════════════════════

_SEVERITY_OVERRIDES: Dict[tuple[Layer, Layer], Severity] = {
    # Controller → Infrastructure
    (Layer.CONTROLLER, Layer.INFRASTRUCTURE): Severity.MEDIUM,
    # Model → API / Controller
    (Layer.MODEL, Layer.API): Severity.HIGH,
    (Layer.MODEL, Layer.CONTROLLER): Severity.HIGH,
    (Layer.MODEL, Layer.SERVICE): Severity.HIGH,
    (Layer.MODEL, Layer.INFRASTRUCTURE): Severity.HIGH,
    # Tests imported by production code (handled via INFRASTRUCTURE→TEST etc.)
    (Layer.INFRASTRUCTURE, Layer.CONTROLLER): Severity.MEDIUM,
    (Layer.INFRASTRUCTURE, Layer.API): Severity.MEDIUM,
    # Utility → Controller / Service
    (Layer.UTILITY, Layer.CONTROLLER): Severity.MEDIUM,
    (Layer.UTILITY, Layer.SERVICE): Severity.LOW,
    (Layer.UTILITY, Layer.API): Severity.MEDIUM,
    # Domain → Infrastructure / API / Controller
    (Layer.DOMAIN, Layer.INFRASTRUCTURE): Severity.HIGH,
    (Layer.DOMAIN, Layer.API): Severity.HIGH,
    (Layer.DOMAIN, Layer.CONTROLLER): Severity.HIGH,
    (Layer.DOMAIN, Layer.DATABASE): Severity.HIGH,
    # Service → Controller / API
    (Layer.SERVICE, Layer.CONTROLLER): Severity.MEDIUM,
    (Layer.SERVICE, Layer.API): Severity.MEDIUM,
    # Repository → Controller / API
    (Layer.REPOSITORY, Layer.CONTROLLER): Severity.MEDIUM,
    (Layer.REPOSITORY, Layer.API): Severity.MEDIUM,
    # Schema → Controller / API / Infrastructure
    (Layer.SCHEMA, Layer.CONTROLLER): Severity.MEDIUM,
    (Layer.SCHEMA, Layer.API): Severity.MEDIUM,
    (Layer.SCHEMA, Layer.INFRASTRUCTURE): Severity.MEDIUM,
    # Controller → Database / Migration
    (Layer.CONTROLLER, Layer.DATABASE): Severity.MEDIUM,
    (Layer.CONTROLLER, Layer.MIGRATION): Severity.MEDIUM,
}


def _build_classification_lookup(
    file_classifications: List[FileClassification],
) -> Dict[str, FileClassification]:
    """Map file paths to their :class:`FileClassification`."""
    return {fc.file_path: fc for fc in file_classifications}


def _severity_for(source_layer: Layer, target_layer: Layer) -> Severity:
    """Determine severity for a specific layer-pair violation."""
    return _SEVERITY_OVERRIDES.get(
        (source_layer, target_layer),
        Severity.MEDIUM,
    )


def _violation_reason(
    source_file: str,
    target_file: str,
    source_layer: Layer,
    target_layer: Layer,
) -> str:
    """Build a human-readable reason string."""
    return (
        f"{source_layer.value!s} layer file '{source_file}' "
        f"imports from forbidden {target_layer.value!s} layer "
        f"file '{target_file}'"
    )


class LayerViolationDetector:
    """Detect architectural layer violations in a dependency graph.

    Uses the default :data:`LAYER_RULES` from constants, which can be
    augmented at runtime via :meth:`add_rule`.
    """

    def __init__(self) -> None:
        # Deep-copy the default rules so mutations are instance-local.
        self._rules: Dict[Layer, FrozenSet[Layer]] = dict(LAYER_RULES)

    # ── public API ──────────────────────────────────────────────────

    def detect(
        self,
        file_classifications: List[FileClassification],
        dependency_graph: Dict[str, List[str]],
        custom_rules: Optional[Dict[str, FrozenSet[str]]] = None,
    ) -> List[LayerViolation]:
        """Detect layer violations across the dependency graph.

        Parameters
        ----------
        file_classifications:
            Classification of every known file (includes its *layer*).
        dependency_graph:
            Mapping of ``source_file → [target_files]``.
        custom_rules:
            Optional rule overrides.  Keys and frozen-set values are
            plain strings that must match :class:`Layer` enum values.
            When provided these **replace** the default rules entirely.

        Returns
        -------
        List[LayerViolation]
            All detected violations, sorted by severity (high → low).
        """
        active_rules: Dict[Layer, FrozenSet[Layer]] = self._resolve_rules(
            custom_rules,
        )

        classification_map: Dict[str, FileClassification] = (
            _build_classification_lookup(file_classifications)
        )

        violations: List[LayerViolation] = []

        for source_file, targets in dependency_graph.items():
            source_cls = classification_map.get(source_file)
            if source_cls is None:
                continue
            source_layer: Layer = source_cls.layer

            forbidden: FrozenSet[Layer] = active_rules.get(
                source_layer, frozenset()
            )
            if not forbidden:
                continue

            for target_file in targets:
                target_cls = classification_map.get(target_file)
                if target_cls is None:
                    continue
                target_layer: Layer = target_cls.layer

                if target_layer in forbidden:
                    severity = _severity_for(source_layer, target_layer)
                    reason = _violation_reason(
                        source_file,
                        target_file,
                        source_layer,
                        target_layer,
                    )
                    violated_rule = (
                        f"{source_layer.value} -> {target_layer.value}"
                    )
                    violations.append(
                        LayerViolation(
                            violated_rule=violated_rule,
                            source_file=source_file,
                            target_file=target_file,
                            source_layer=source_layer,
                            target_layer=target_layer,
                            severity=severity,
                            reason=reason,
                        )
                    )

        # Sort by severity: CRITICAL > HIGH > MEDIUM > LOW > INFO
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        violations.sort(key=lambda v: severity_order.get(v.severity, 99))
        return violations

    def add_rule(
        self,
        source_layer: Layer,
        forbidden_target_layers: FrozenSet[Layer],
    ) -> None:
        """Add or replace a layering rule at runtime.

        Parameters
        ----------
        source_layer:
            The layer for which to set forbidden imports.
        forbidden_target_layers:
            Set of layers the *source_layer* must not import from.
        """
        self._rules[source_layer] = forbidden_target_layers

    def get_rules(self) -> Dict[Layer, FrozenSet[Layer]]:
        """Return a copy of the current rule-set."""
        return dict(self._rules)

    # ── internal helpers ────────────────────────────────────────────

    def _resolve_rules(
        self,
        custom_rules: Optional[Dict[str, FrozenSet[str]]],
    ) -> Dict[Layer, FrozenSet[Layer]]:
        """Resolve custom string-based rules into typed :class:`Layer` rules.

        If *custom_rules* is ``None``, the instance rules are returned
        unchanged.  Otherwise the custom rules **replace** the defaults.
        """
        if custom_rules is None:
            return self._rules

        resolved: Dict[Layer, FrozenSet[Layer]] = {}
        for source_str, forbidden_strs in custom_rules.items():
            try:
                source_layer = Layer(source_str)
            except ValueError:
                logger.warning(
                    "Unknown source layer %r in custom rules — skipping",
                    source_str,
                )
                continue

            forbidden_layers: set[Layer] = set()
            for target_str in forbidden_strs:
                try:
                    forbidden_layers.add(Layer(target_str))
                except ValueError:
                    logger.warning(
                        "Unknown target layer %r in custom rules — skipping",
                        target_str,
                    )
            resolved[source_layer] = frozenset(forbidden_layers)

        return resolved
