# AI GTM Engine

A hackathon prototype that connects an approved ideal customer profile (ICP), evidence-backed prospect research, a knowledge graph, and human-reviewed outreach.

## Setup

Requires Python 3.14 for the pinned environment used during development.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a local `.env` file with your MOSS workspace credentials.

```dotenv
MOSS_PROJECT_ID=
MOSS_PROJECT_KEY=
```

```bash
python -m streamlit run app.py
```

## Demo workflow

1. Enter a product and approve its generated ICP.
2. Run discovery and open a source for a prospect's buying signal.
3. Select the prospect in the knowledge graph and inspect its connections.
4. Draft, edit and approve an email. Export the approved draft.
5. Simulate a pipeline transition and inspect activity history.

The prototype exports approved email drafts. The dashboard uses simulated activity for stage and conversion metrics.

[Architecture](docs/architecture.md)
