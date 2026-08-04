"""Model routing (PRD FR-041, section 15, ARCHITECTURE.md section 13 gap 6).

Every role names a configured profile rather than a hard-coded model, so
changing which model answers is a settings change and never a code change.

Sequential loading is honoured here as well as declared. `config/defaults.yaml`
sets ``load_strategy: sequential`` because 12 GB of VRAM will not hold two heavy
models with large contexts at once (PRD FR-039). Phase 0 recorded that as
configuration nothing enforced; this router is where it starts being enforced,
by refusing to hand out a second heavy role while one is held. It is not
meaningfully exercised until Phase 4 adds the vision model, which is why the
lease is deliberately simple.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from jarvis.config.schema import AppConfig
from jarvis.llm.ports import ModelRole

__all__ = ["ModelRouter", "RoutedModel", "ModelBusyError"]

_LOG = logging.getLogger(__name__)

#: Roles that load a large model into memory. Embeddings are small enough to
#: coexist with anything.
_HEAVY_ROLES = frozenset({ModelRole.CONVERSATION, ModelRole.VISION})


class ModelBusyError(RuntimeError):
    """A heavy model is loaded and sequential loading is configured."""


@dataclass(frozen=True)
class RoutedModel:
    role: ModelRole
    name: str
    provider: str
    context_length: int

    def describe(self) -> str:
        return f"{self.role.value} -> {self.name} ({self.provider}, ctx {self.context_length})"


class ModelRouter:
    """Resolves a role to a configured profile, and gates heavy loads."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._held: ModelRole | None = None

    def update(self, config: AppConfig) -> None:
        """Adopt changed configuration without rebuilding the router."""
        with self._lock:
            self._config = config

    def resolve(self, role: ModelRole) -> RoutedModel:
        with self._lock:
            models = self._config.models
            profile = {
                ModelRole.CONVERSATION: models.planner,
                ModelRole.VISION: models.vision,
                ModelRole.EMBEDDING: models.embeddings,
            }[role]
        return RoutedModel(
            role=role,
            name=profile.name,
            provider=profile.provider,
            context_length=profile.context_length,
        )

    def describe_all(self) -> tuple[RoutedModel, ...]:
        return tuple(self.resolve(role) for role in ModelRole)

    @property
    def sequential(self) -> bool:
        with self._lock:
            return self._config.model_runtime.load_strategy == "sequential"

    @property
    def held_role(self) -> ModelRole | None:
        with self._lock:
            return self._held

    @contextmanager
    def hold(self, role: ModelRole) -> Iterator[RoutedModel]:
        """Reserve a role's model for the duration of a call.

        Under sequential loading, holding one heavy role refuses another. The
        caller gets a named error rather than the machine paging itself to a
        standstill trying to hold two large models at once.
        """
        routed = self.resolve(role)
        heavy = role in _HEAVY_ROLES
        with self._lock:
            if heavy and self.sequential and self._held is not None and self._held is not role:
                raise ModelBusyError(
                    f"'{self._held.value}' is loaded and model_runtime.load_strategy "
                    f"is 'sequential', so '{role.value}' cannot load at the same "
                    "time. Wait for the current model to finish, or change the "
                    "strategy if this machine has the memory for both."
                )
            previous = self._held
            if heavy:
                self._held = role
        try:
            yield routed
        finally:
            with self._lock:
                if heavy:
                    self._held = previous
