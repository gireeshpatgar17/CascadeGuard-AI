# CascadeGuard AI

**Orca Coders: Orcathon 2026 — Software & AI track**

CascadeGuard AI is a Streamlit prototype that demonstrates how software failures can propagate across a dependency graph, ranks a likely initiating component, and compares simulated recovery actions. All telemetry is synthetic; it does not connect to production infrastructure.

## Features
- Interactive service dependency topology
- Three repeatable incident scenarios
- Synthetic, filterable server event stream
- Heuristic cascade risk scoring
- Root-cause ranking with visible evidence
- Recovery strategy comparison and what-if simulation
- CSV export of simulated logs

## Run locally (Windows PowerShell)

```powershell
cd cascadeguard-ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks environment activation, run the app with the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run tests

```powershell
pytest -q
```

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository and push this project.
2. Open Streamlit Community Cloud and connect your GitHub account.
3. Select the repository, branch, and `app.py` as the main file.
4. Deploy. No secrets or API keys are required.

## Architecture
- `app.py`: Streamlit UI and interaction state
- `src/simulation.py`: service graph, scenario state, synthetic logs
- `src/cascade_engine.py`: cascade scoring and recovery ranking
- `src/root_cause.py`: heuristic root-cause ranking
- `src/visualizations.py`: Plotly service topology
- `tests/`: core engine tests

## Model and scoring notes
This version uses transparent graph traversal and deterministic heuristic scoring, not a trained machine-learning model. Risk and evidence scores are illustrative ranking scores, not calibrated probabilities. Scenario events, recovery outcomes, and estimated reductions are simulated. No real recovery commands are executed.

## Hackathon disclosure
This repository is a prototype prepared with AI-assisted development. Before submission, accurately disclose the tools used and any pre-existing code or assets, as required by the event rules. Verify the final application and deployment yourself before sharing the live link.
