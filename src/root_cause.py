from __future__ import annotations
import networkx as nx


def rank_root_causes(graph: nx.DiGraph, states: dict[str, str], root: str) -> list[dict]:
    rows = []
    for node in graph.nodes:
        if states.get(node) == "Healthy":
            continue
        # Heuristic evidence score, not a calibrated probability.
        score = 55 + graph.nodes[node].get("criticality", 5) * 2.5
        if node == root:
            score += 22
        score += min(10, len(nx.ancestors(graph, node)) * 1.5)
        score = min(99, round(score, 1))
        evidence = "Observed initiating failure in simulated telemetry" if node == root else "Downstream symptoms are consistent with dependency impact"
        rows.append({"Service": node, "Evidence score": score, "Evidence": evidence,
                     "Affected dependents": len(nx.ancestors(graph, node))})
    return sorted(rows, key=lambda r: (-r["Evidence score"], r["Service"]))
