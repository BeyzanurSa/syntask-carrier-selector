"""Reads the Rule set from rules.yaml (ADR 0002) and checks every name against the engine's registries."""

from pathlib import Path

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

from app.engine.constraints import CONSTRAINTS
from app.engine.ranking import RANKING_CRITERIA


class RulesError(ValueError):
    """The Rule set refers to unknown names or has no enabled ranking criterion."""


class RankingEntry(BaseModel):
    name: str
    enabled: bool = True


class Thresholds(BaseModel):
    field_confidence: float = Field(ge=0, le=1)
    note_warning: float = Field(ge=0, le=1)


class RuleSet(BaseModel):
    constraints: list[str]
    ranking: list[RankingEntry]
    thresholds: Thresholds

    @property
    def enabled_ranking(self) -> list[str]:
        return [entry.name for entry in self.ranking if entry.enabled]


def validate_rules(rules: RuleSet) -> None:
    unknown = [n for n in rules.constraints if n not in CONSTRAINTS]
    unknown += [e.name for e in rules.ranking if e.name not in RANKING_CRITERIA]
    if unknown:
        raise RulesError(f"Unknown rule names: {', '.join(unknown)}")
    if not rules.enabled_ranking:
        raise RulesError("At least one ranking criterion must be enabled")


class RulesStore:
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> RuleSet:
        data = YAML(typ="safe").load(self._path.read_text(encoding="utf-8"))
        rules = RuleSet.model_validate(data)
        validate_rules(rules)
        return rules
