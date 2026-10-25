from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd
import streamlit as st
import plotly.express as px
from src.simulation import SCENARIOS, build_graph, scenario_state, generate_logs
from src.cascade_engine import predict_cascade, rank_recoveries
from src.root_cause import rank_root_causes
from src.visualizations import topology_figure

st.set_page_config(page_title="CascadeGuard AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background: radial-gradient(ellipse at top left, #172554 0%, #0b1120 36%, #080d18 100%); color:#e2e8f0;}
.block-container {padding-top:1.4rem; max-width:1500px;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif; letter-spacing:-.03em;}
[data-testid="stMetric"] {background:rgba(15,23,42,.72); border:1px solid rgba(148,163,184,.18); padding:16px 18px; border-radius:14px;}
[data-testid="stMetricLabel"] {color:#94a3b8;}
[data-testid="stMetricValue"] {color:#f8fafc;}
div.stButton > button {border-radius:10px; font-weight:700; min-height:2.7rem;}
section[data-testid="stSidebar"] {background:rgba(10,15,28,.94); border-right:1px solid #1e293b;}
.panel-note {color:#94a3b8;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

if "scenario" not in st.session_state: st.session_state.scenario = "Database connection exhaustion"
if "recovered" not in st.session_state: st.session_state.recovered = False
if "run_id" not in st.session_state: st.session_state.run_id = 0

with st.sidebar:
    st.markdown("# 🛡️ CascadeGuard")
    st.caption("PREDICTIVE INCIDENT INTELLIGENCE")
    st.divider()
    scenario_name = st.selectbox("Incident scenario", list(SCENARIOS), index=list(SCENARIOS).index(st.session_state.scenario))
    if scenario_name != st.session_state.scenario:
        st.session_state.scenario = scenario_name; st.session_state.recovered = False
    st.markdown("**Simulation controls**")
    st.caption(SCENARIOS[scenario_name]["description"])
    if st.button("▶ Run incident simulation", type="primary", use_container_width=True):
        st.session_state.run_id += 1; st.session_state.recovered = False
    st.divider()
    st.markdown("**System status**")
    st.success("Simulation engine ready")
    st.caption("Synthetic telemetry · No production systems connected")
    st.markdown("---")
    st.caption("Orcathon 2026 · Software & AI track")

state = scenario_state(scenario_name)
graph, root, states = state["graph"], state["root"], state["states"]
if st.session_state.recovered:
    states = {node: ("Mitigated" if s != "Healthy" else "Healthy") for node, s in states.items()}
    states[root] = "Mitigated"
risks_rows = predict_cascade(graph, root, states, recovered=st.session_state.recovered)
risks = {r["Service"]: r["Risk score"] for r in risks_rows}
root_rows = rank_root_causes(graph, state["states"], root)
logs = pd.DataFrame(generate_logs(scenario_name, seed=17 + st.session_state.run_id))

st.markdown("<div style='color:#60a5fa;font-weight:700;font-size:.78rem;letter-spacing:.16em'>INCIDENT OPERATIONS CENTER / LIVE SIMULATION</div>", unsafe_allow_html=True)
st.title("CascadeGuard AI")
st.markdown("Predict cascading failures. Find the likely root cause. Choose a safer recovery.")
st.markdown(f"<span style='background:#3f1d2a;color:#fda4af;border:1px solid #7f1d35;padding:5px 10px;border-radius:99px;font-size:.8rem'>● {'RECOVERY SIMULATED' if st.session_state.recovered else 'INCIDENT SIMULATED'}</span> &nbsp; <span style='color:#94a3b8;font-size:.85rem'>Scenario: {scenario_name}</span>", unsafe_allow_html=True)

impacted = [r for r in risks_rows if r["Service"] != root and r["Risk score"] >= 35]
failed_count = 0 if st.session_state.recovered else 1
degraded_count = 0 if st.session_state.recovered else len(impacted)
max_risk = max([r["Risk score"] for r in risks_rows if r["Service"] != root] or [0])
cols = st.columns(4)
cols[0].metric("Services monitored", len(graph.nodes))
cols[1].metric("Observed failures", failed_count, delta="Mitigated" if st.session_state.recovered else None)
cols[2].metric("Services at risk", degraded_count, delta="Risk reduced" if st.session_state.recovered else None)
cols[3].metric("Highest downstream risk", f"{max_risk:.0f}/100", delta="After recovery" if st.session_state.recovered else "Heuristic score")

left, right = st.columns([1.55, 1], gap="large")
with left:
    st.subheader("Service dependency topology")
    st.plotly_chart(topology_figure(graph, states, risks), use_container_width=True, config={"displayModeBar": False})
    st.caption("Green = healthy · Amber = degraded · Red = failed · Blue = mitigated. Relationships and telemetry are simulated.")
with right:
    st.subheader("Root-cause analysis")
    st.markdown(f"<div style='padding:16px;border:1px solid #7f1d35;background:rgba(127,29,53,.18);border-radius:14px'><div style='color:#fda4af;font-size:.75rem;font-weight:700;letter-spacing:.1em'>MOST LIKELY INITIATING COMPONENT</div><div style='font-size:1.35rem;font-weight:700;margin:6px 0'>{root}</div><div style='color:#cbd5e1;font-size:.9rem'>{SCENARIOS[scenario_name]['description']}</div></div>", unsafe_allow_html=True)
    st.markdown(" ")
    if root_rows:
        top = next((r for r in root_rows if r["Service"] == root), root_rows[0])
        st.metric("Root-cause evidence score", f"{top['Evidence score']:.1f}/100", help="Heuristic ranking score, not a calibrated probability.")
        st.write("**Evidence from simulated logs**")
        st.write("- " + SCENARIOS[scenario_name]["signals"][0])
        st.write("- " + SCENARIOS[scenario_name]["signals"][1])
        st.write("- Dependency topology shows a plausible downstream impact path.")
    st.info("This prototype ranks likely causes from known simulated scenarios. It does not diagnose real production incidents.")

st.divider()
impact_col, recovery_col = st.columns([1.05, 1], gap="large")
with impact_col:
    st.subheader("Predicted cascade")
    impact_df = pd.DataFrame(risks_rows)
    if not impact_df.empty:
        display_cols = ["Service", "Risk score", "Status", "Reason"]
        st.dataframe(impact_df[display_cols], hide_index=True, use_container_width=True, height=290,
                     column_config={"Risk score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100, format="%d/100")})
        chart_df = impact_df[impact_df["Service"] != root].sort_values("Risk score", ascending=True)
        if not chart_df.empty:
            fig = px.bar(chart_df, x="Risk score", y="Service", orientation="h", color="Risk score", range_color=[0,100], color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"])
            fig.update_layout(height=250, margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1", coloraxis_showscale=False, xaxis=dict(range=[0,100], gridcolor="#263244"), yaxis=dict(title=""))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
with recovery_col:
    st.subheader("Recovery strategy advisor")
    actions = rank_recoveries(root, graph)
    action_df = pd.DataFrame(actions)
    st.dataframe(action_df[["Action", "Risk reduction", "Recovery time (min)", "Operational cost (1–5)"]], hide_index=True, use_container_width=True, height=190)
    recommended = actions[0]
    st.markdown(f"**Recommended:** {recommended['Action']}  ")
    st.caption(recommended["Rationale"])
    selected_action = st.selectbox("Choose a recovery action to simulate", [a["Action"] for a in actions])
    chosen = next(a for a in actions if a["Action"] == selected_action)
    st.caption(f"Estimated risk reduction: {chosen['Risk reduction']}% · Estimated recovery: {chosen['Recovery time (min)']} min · Operational cost: {chosen['Operational cost (1–5)']}/5")
    if not st.session_state.recovered:
        if st.button("✓ Simulate selected recovery", type="primary", use_container_width=True):
            st.session_state.recovered = True
            st.session_state.selected_recovery = selected_action
            st.rerun()
    else:
        st.success(f"Simulated recovery applied: {st.session_state.get('selected_recovery', selected_action)}")
        if st.button("↺ Reset incident", use_container_width=True):
            st.session_state.recovered = False; st.rerun()

st.divider()
log_left, log_right = st.columns([1.4, 1], gap="large")
with log_left:
    st.subheader("Synthetic event stream")
    level_filter = st.multiselect("Filter severity", ["ERROR", "WARN", "INFO"], default=["ERROR", "WARN", "INFO"])
    filtered = logs[logs["Level"].isin(level_filter)].sort_index(ascending=False)
    st.dataframe(filtered, hide_index=True, use_container_width=True, height=290)
with log_right:
    st.subheader("Incident summary")
    st.write(f"**Scenario:** {scenario_name}")
    st.write(f"**Initiating component:** {root}")
    st.write(f"**Current simulated state:** {'Recovery applied' if st.session_state.recovered else 'Failure propagation predicted'}")
    st.write("**Recommended next step:** Validate the recovery action in a controlled environment before applying it to any real system.")
    st.download_button("⬇ Download simulated incident logs (CSV)", data=logs.to_csv(index=False), file_name="cascadeguard_simulated_logs.csv", mime="text/csv", use_container_width=True)

st.markdown("---")
st.caption("CascadeGuard AI is a hackathon prototype. Risk, confidence and recovery figures are illustrative heuristic estimates based on synthetic data, not validated production predictions.")
