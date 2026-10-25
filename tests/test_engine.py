from src.simulation import build_graph, scenario_state, SCENARIOS
from src.cascade_engine import predict_cascade, rank_recoveries
from src.root_cause import rank_root_causes


def test_graph_is_directed_and_has_expected_services():
    graph = build_graph()
    assert graph.is_directed()
    assert "PostgreSQL Database" in graph
    assert "Payment Service" in graph


def test_database_scenario_marks_root_failed():
    state = scenario_state("Database connection exhaustion")
    assert state["states"]["PostgreSQL Database"] == "Failed"
    assert state["states"]["Payment Service"] == "Degraded"


def test_cascade_includes_root_and_dependents():
    state = scenario_state("Payment service failure")
    rows = predict_cascade(state["graph"], state["root"], state["states"])
    names = {row["Service"] for row in rows}
    assert state["root"] in names
    assert "Order Service" in names


def test_root_cause_ranked_first_for_known_scenario():
    state = scenario_state("Redis cache failure")
    rows = rank_root_causes(state["graph"], state["states"], state["root"])
    assert rows[0]["Service"] == state["root"]


def test_recovery_actions_have_required_fields():
    state = scenario_state("Database connection exhaustion")
    rows = rank_recoveries(state["root"], state["graph"])
    assert rows
    assert all("Action" in row and "Score" in row for row in rows)


def test_all_scenarios_have_root_node():
    graph = build_graph()
    for scenario in SCENARIOS.values():
        assert scenario["root"] in graph
