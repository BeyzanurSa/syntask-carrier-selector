"""Reads the Rule set from rules.yaml (ADR 0002) and checks every name against the engine's registries."""

from pathlib import Path

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

from app.engine.constraints import CONSTRAINTS
from app.engine.ranking import RANKING_CRITERIA


RANKING_COMMENT = "Ranking criteria, highest priority first. Ties left after all criteria go to the carrier name."


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
        raise RulesError(f"Bilinmeyen kural adı: {', '.join(unknown)}")
    names = [*rules.constraints, *(e.name for e in rules.ranking)]
    if len(names) != len(set(names)):
        raise RulesError("Aynı kural birden fazla kez listelenemez")
    if not rules.enabled_ranking:
        raise RulesError("En az bir sıralama kriteri açık olmalı")


def rule_labels() -> dict[str, str]:
    """Turkish display names for every known Constraint and Ranking criterion."""
    return {name: rule.label for name, rule in (*CONSTRAINTS.items(), *RANKING_CRITERIA.items())}


class RulesStore:
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> RuleSet:
        data = YAML(typ="safe").load(self._path.read_text(encoding="utf-8"))
        rules = RuleSet.model_validate(data)
        validate_rules(rules)
        return rules

    def save(self, rules: RuleSet) -> None:
        """Validate, then rewrite rules.yaml in place. Round-trip mode keeps the file's comments."""
        validate_rules(rules)
        yaml = YAML()  # round-trip
        yaml.indent(mapping=2, sequence=4, offset=2)
        doc = yaml.load(self._path.read_text(encoding="utf-8"))
        doc["constraints"] = rules.constraints
        doc["ranking"] = [entry.model_dump() for entry in rules.ranking]
        for key, value in rules.thresholds.model_dump().items():
            doc["thresholds"][key] = value
        # ruamel attaches a comment above a key to the end of the previous list, which was just
        # replaced, so put the ranking section's comment back on the key itself.
        doc.yaml_set_comment_before_after_key("ranking", before=RANKING_COMMENT)
        with self._path.open("w", encoding="utf-8") as f:
            yaml.dump(doc, f)
