import math
import networkx as nx
import plotly.graph_objects as go

COLORS = {"Healthy": "#22c55e", "Degraded": "#f59e0b", "Failed": "#ef4444", "Mitigated": "#38bdf8"}


def topology_figure(graph: nx.DiGraph, states: dict[str, str], risks: dict[str, float] | None = None):
    risks = risks or {}
    # spring layout is deterministic for a stable demo
    pos = nx.spring_layout(graph, seed=14, k=1.35, iterations=80)
    edge_x, edge_y = [], []
    for source, target in graph.edges:
        x0, y0 = pos[source]; x1, y1 = pos[target]
        edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1.3, color="#475569"), hoverinfo="none")
    node_x, node_y, node_colors, node_sizes, hover = [], [], [], [], []
    for node in graph.nodes:
        x, y = pos[node]
        node_x.append(x); node_y.append(y)
        state = states.get(node, "Healthy")
        node_colors.append(COLORS.get(state, "#64748b"))
        node_sizes.append(22 + graph.nodes[node].get("criticality", 5) * 1.2)
        hover.append(f"<b>{node}</b><br>Status: {state}<br>Criticality: {graph.nodes[node].get('criticality', 5)}/10<br>Risk score: {risks.get(node, 0)}")
    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=list(graph.nodes), textposition="bottom center",
        textfont=dict(color="#e2e8f0", size=10), hovertext=hover, hoverinfo="text",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1.5, color="#cbd5e1")))
    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(height=440, margin=dict(l=10, r=10, t=15, b=25), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False, font=dict(color="#e2e8f0"),
        annotations=[dict(text="Dependency links point from a service to the component it relies on", x=0.01, y=0.99, xref="paper", yref="paper", showarrow=False, font=dict(size=10, color="#94a3b8"))])
    return fig
