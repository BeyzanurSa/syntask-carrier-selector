from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.services.rules_store import RuleSet, RulesError, RulesStore, rule_labels

router = APIRouter(prefix="/rules", tags=["rules"])


class RulesOut(RuleSet):
    labels: dict[str, str]


def get_rules_store(request: Request) -> RulesStore:
    return RulesStore(request.app.state.settings.rules_path)


RulesStoreDep = Annotated[RulesStore, Depends(get_rules_store)]


def _out(rules: RuleSet) -> RulesOut:
    return RulesOut(**rules.model_dump(), labels=rule_labels())


@router.get("", response_model=RulesOut)
def read_rules(store: RulesStoreDep) -> RulesOut:
    return _out(store.load())


@router.put("", response_model=RulesOut)
def replace_rules(rules: RuleSet, store: RulesStoreDep) -> RulesOut:
    """Replace the Rule set in rules.yaml. Unknown names or no enabled ranking criterion → 400, file untouched."""
    try:
        store.save(rules)
    except RulesError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return _out(store.load())
