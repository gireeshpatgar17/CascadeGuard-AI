from __future__ import annotations
import networkx as nx


def predict_cascade(graph: nx.DiGraph, root: str, states: dict[str, str], recovered: bool = False) -> list[dict]:
    """Rank services likely to be affected, using reverse dependency traversal and transparent heuristics."""
    if root not in graph:
        return []
    candidates = nx.ancestors(graph, root) | {root}
    rows = []
    for service in candidates:
        distance = nx.shortest_path_length(graph.reverse(copy=False), source=root, target=service) if service != root else 0
        criticality = graph.nodes[service].get("criticality", 5)
        base = 100 if service == root else max(12, 78 - distance * 16 + criticality * 1.7)
        if recovered:
            base *= 0.18 if service != root else 0
        score = round(min(99, max(0, base)), 1)
        status = "Observed failure" if service == root and not recovered else ("Mitigated" if recovered else "Predicted impact")
        if service != root and not recovered and score < 35:
            status = "Watch"
        rows.append({"Service": service, "Risk score": score, "Status": status,
                     "Criticality": criticality, "Distance": distance,
                     "Reason": "Initiating component" if service == root else f"Depends on the failure chain ({distance} hop{'s' if distance != 1 else ''}); criticality {criticality}/10"})
    return sorted(rows, key=lambda r: (-r["Risk score"], r["Service"]))


def rank_recoveries(root: str, graph: nx.DiGraph) -> list[dict]:
    actions = {
        "Database connection exhaustion": [
            ("Restore database connectivity", 88, 4, 2, "Targets the initiating bottleneck and restores dependent queries."),
            ("Increase connection pool", 76, 5, 3, "Can relieve saturation if database capacity is available."),
            ("Restart affected application services", 43, 7, 4, "May clear stuck connections but does not address database capacity."),
        ],
        "Payment service failure": [
            ("Roll back payment deployment", 91, 3, 2, "Reverts the likely faulty release with limited blast radius."),
            ("Restart payment service", 72, 4, 2, "May restore service if the fault is transient."),
            ("Pause order processing", 48, 8, 3, "Reduces cascading pressure but delays customer orders."),
        ],
        "Redis cache failure": [
            ("Restore Redis connectivity", 87, 4, 2, "Restores cache access and reduces database pressure."),
            ("Enable controlled cache bypass", 69, 5, 3, "Keeps requests moving but may increase database load."),
            ("Rate-limit read-heavy traffic", 52, 7, 4, "Protects the database while reducing throughput."),
        ],
    }
    items = actions.get(root, [("Restart affected service", 60, 5, 3, "Generic recovery action.")])
    return [{"Action": a, "Risk reduction": r, "Recovery time (min)": t, "Operational cost (1–5)": c, "Rationale": why,
             "Score": round(r - t * 1.5 - c * 3, 1)} for a, r, t, c, why in items]
