from __future__ import annotations
import random
from datetime import datetime, timedelta
import networkx as nx

SCENARIOS = {
    "Database connection exhaustion": {
        "root": "PostgreSQL Database", "severity": "Critical",
        "description": "Connection pool saturation causes query latency and upstream request failures.",
        "signals": ["connection pool exhausted", "query timeout", "HTTP 503 from dependent service"]
    },
    "Payment service failure": {
        "root": "Payment Service", "severity": "High",
        "description": "Payment requests time out, backing up order processing and customer notifications.",
        "signals": ["payment provider timeout", "retry queue growing", "order confirmation delayed"]
    },
    "Redis cache failure": {
        "root": "Redis Cache", "severity": "High",
        "description": "Cache misses increase database load and slow user-facing services.",
        "signals": ["cache connection refused", "cache miss ratio elevated", "database query rate increased"]
    },
}

# Edges point from a dependency to the services that rely on it.
def build_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    services = {
        "API Gateway": (10, "edge"), "Authentication Service": (8, "identity"),
        "User Service": (6, "application"), "Order Service": (9, "application"),
        "Payment Service": (9, "application"), "Inventory Service": (7, "application"),
        "Notification Service": (4, "application"), "PostgreSQL Database": (10, "data"),
        "Redis Cache": (6, "data"),
    }
    for name, (criticality, kind) in services.items():
        graph.add_node(name, criticality=criticality, kind=kind)
    graph.add_edges_from([
        ("API Gateway", "Authentication Service"), ("API Gateway", "User Service"),
        ("API Gateway", "Order Service"), ("Authentication Service", "User Service"),
        ("User Service", "Order Service"), ("Order Service", "Payment Service"),
        ("Order Service", "Inventory Service"), ("Order Service", "Notification Service"),
        ("Payment Service", "PostgreSQL Database"), ("Inventory Service", "PostgreSQL Database"),
        ("User Service", "PostgreSQL Database"), ("User Service", "Redis Cache"),
        ("Order Service", "Redis Cache"),
    ])
    return graph


def scenario_state(scenario_name: str) -> dict:
    scenario = SCENARIOS[scenario_name]
    graph = build_graph()
    root = scenario["root"]
    # The root and its upstream consumers can be impacted; dependency edges are traversed in reverse.
    impacted = set(nx.ancestors(graph, root)) | {root}
    states = {}
    for node in graph.nodes:
        if node == root:
            states[node] = "Failed"
        elif node in impacted:
            states[node] = "Degraded"
        else:
            states[node] = "Healthy"
    return {"graph": graph, "root": root, "states": states, "scenario": scenario}


def generate_logs(scenario_name: str, seed: int = 17, count: int = 32) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now().replace(microsecond=0)
    scenario = SCENARIOS[scenario_name]
    services = list(build_graph().nodes)
    rows = []
    for i in range(count):
        service = scenario["root"] if i % 4 == 0 else rng.choice(services)
        if i % 4 == 0:
            level, message = "ERROR", rng.choice(scenario["signals"])
        elif i % 5 == 0:
            level, message = "WARN", rng.choice(["latency above baseline", "retry count elevated", "dependency response slowed"])
        else:
            level, message = "INFO", rng.choice(["health check passed", "request completed", "connection pool within limits", "cache response received"])
        rows.append({"Timestamp": (now - timedelta(minutes=count-i)).strftime("%H:%M:%S"), "Level": level, "Service": service, "Message": message})
    return rows
