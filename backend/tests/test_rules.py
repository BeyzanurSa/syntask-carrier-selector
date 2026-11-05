"""The Rule set is read and replaced through the API, written to rules.yaml, and used by the next selection."""

from tests.conftest import select


def ranking(*entries: tuple[str, bool]) -> list[dict]:
    return [{"name": name, "enabled": enabled} for name, enabled in entries]


def rule_set(client, ranking_entries: list[dict]) -> dict:
    current = client.get("/rules").json()
    return {"constraints": current["constraints"], "ranking": ranking_entries, "thresholds": current["thresholds"]}


def test_current_rule_set_is_returned_with_labels(client):
    rules = client.get("/rules").json()

    assert rules["constraints"] == ["active", "distance_range", "container_size", "cargo_type"]
    assert rules["ranking"] == ranking(("total_cost", True), ("hq_proximity", True))
    assert rules["thresholds"] == {"field_confidence": 0.75, "note_warning": 0.7}
    assert rules["labels"]["total_cost"] == "Toplam ücret"
    assert rules["labels"]["distance_range"]


def test_putting_hq_proximity_first_changes_the_next_selection(client):
    before = select(client, "Miami", "Orlando", 40, "Dry")
    assert before["selected_carrier"]["name"] == "S-Logistics"
    assert before["rules_used"] == ["total_cost", "hq_proximity"]

    saved = client.put("/rules", json=rule_set(client, ranking(("hq_proximity", True), ("total_cost", True))))
    assert saved.status_code == 200

    after = select(client, "Miami", "Orlando", 40, "Dry")
    # Houston → Miami is 1190 mi; Tampa → Miami is not measurable, so S ranks last on proximity.
    assert after["selected_carrier"]["name"] == "M-Logistics"
    assert after["rules_used"] == ["hq_proximity", "total_cost"]
    assert client.get("/rules").json()["ranking"][0]["name"] == "hq_proximity"


def test_disabled_criterion_is_skipped(client):
    client.put("/rules", json=rule_set(client, ranking(("total_cost", True), ("hq_proximity", False))))

    result = select(client, "Miami", "Atlanta", 20, "Reefer")

    # B and M tie on cost; without HQ proximity the tie falls through to the carrier name.
    assert result["rules_used"] == ["total_cost"]
    assert result["selected_carrier"]["name"] == "B-Logistics"
    assert "isim" in result["eligible_carriers"][0]["lost_on"]


def test_saving_keeps_the_comments_in_rules_yaml(client, rules_path):
    client.put("/rules", json=rule_set(client, ranking(("hq_proximity", True), ("total_cost", True))))

    text = rules_path.read_text(encoding="utf-8")
    assert "# Rule set for carrier selection" in text
    assert text.count("# Ranking criteria, highest priority first") == 1
    assert "# Jev Choice answers below this confidence" in text
    assert text.index("hq_proximity") < text.index("total_cost")


def test_unknown_criterion_is_refused_and_the_file_is_untouched(client, rules_path):
    original = rules_path.read_text(encoding="utf-8")

    response = client.put("/rules", json=rule_set(client, ranking(("total_cost", True), ("reliabilty", True))))

    assert response.status_code == 400
    assert "reliabilty" in response.json()["detail"]
    assert rules_path.read_text(encoding="utf-8") == original


def test_ranking_with_no_enabled_criterion_is_refused(client):
    response = client.put("/rules", json=rule_set(client, ranking(("total_cost", False), ("hq_proximity", False))))

    assert response.status_code == 400


def test_duplicate_criterion_is_refused(client):
    response = client.put("/rules", json=rule_set(client, ranking(("total_cost", True), ("total_cost", True))))

    assert response.status_code == 400


def test_unknown_constraint_is_refused(client):
    rules = rule_set(client, ranking(("total_cost", True)))
    rules["constraints"] = [*rules["constraints"], "max_weight"]

    assert client.put("/rules", json=rules).status_code == 400
