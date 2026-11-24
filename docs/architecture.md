# Architecture

Streamlit owns the workspace and review flow. Pydantic validates structured product, ICP, discovery, and outreach data. MOSS inference and browser tasks support generation and public-source research. SQLite stores workspace state. The graph is rebuilt from saved discovery results.

## Knowledge graph

NetworkX stores the graph in memory. The node types are Product, Company, Person, Competitor, and Signal. Directed edges record matches, employment, competition, and buying signals. The explorer follows Product, Company, and Signal paths to surface opportunities and show their evidence.

## Approval and pipeline

The app drafts an email from prospect context and selected evidence. Human approval gates export, and editing an approved draft returns it to review. The pipeline demonstrates stage transitions and records simulated activity for its metrics.

Provider-backed enrichment, live email and LinkedIn delivery, delivery and reply webhooks, and continuous signal ingestion are future integrations.
