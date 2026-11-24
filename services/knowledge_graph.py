
import networkx as nx
from graphviz import Digraph, escape

from models.product import Product
from models.lead import DiscoveryResult


NODE_COLORS = {
    "Product": "#2563EB",
    "Company": "#16A34A",
    "Person": "#9333EA",
    "Competitor": "#DC2626",
    "Signal": "#D97706",
}


def build_graph(
    product: Product,
    result: DiscoveryResult,
) -> nx.DiGraph:

    graph = nx.DiGraph()

    product_id = "product"

    graph.add_node(
        product_id,
        label=product.name,
        entity_type="Product",
        description=product.description,
    )

    # Prospective companies
    for i, prospect in enumerate(result.prospects):

        company_id = f"company_{i}"

        graph.add_node(
            company_id,
            label=prospect.company_name,
            entity_type="Company",
            industry=prospect.industry,
            website=str(prospect.website),
            fit_score=prospect.fit_score,
            description=prospect.description,
            sources=[
                source.model_dump(mode="json")
                for source in prospect.sources
            ],
        )

        graph.add_edge(
            company_id,
            product_id,
            relationship="matched_to",
        )

        # Named decision-makers
        if prospect.buyer_name:

            person_id = f"person_{i}"

            graph.add_node(
                person_id,
                label=prospect.buyer_name,
                entity_type="Person",
                title=prospect.buyer_title,
                verification="Agent-reported",
            )

            graph.add_edge(
                person_id,
                company_id,
                relationship="works_at",
            )

        # Buying signals
        for j, signal in enumerate(
            prospect.buying_signals
        ):

            signal_id = f"signal_{i}_{j}"

            graph.add_node(
                signal_id,
                label=signal,
                entity_type="Signal",
                verification="Agent-reported",
            )

            graph.add_edge(
                company_id,
                signal_id,
                relationship="has_signal",
            )

    # Competitors
    for i, competitor in enumerate(
        result.competitors
    ):

        competitor_id = f"competitor_{i}"

        graph.add_node(
            competitor_id,
            label=competitor.company_name,
            entity_type="Competitor",
            product_name=competitor.product_name,
            website=str(competitor.website),
            positioning=competitor.positioning,
            sources=[
                source.model_dump(mode="json")
                for source in competitor.sources
            ],
        )

        graph.add_edge(
            product_id,
            competitor_id,
            relationship="competes_with",
        )

    return graph


def build_graph_view(graph: nx.DiGraph, selected: str) -> dict:
    layers = list(nx.bfs_layers(graph.to_undirected(as_view=True), ["product"]))
    rows = max(map(len, layers))
    nodes = []
    relation_labels = {
        "matched_to": "Matches product",
        "works_at": "Works at",
        "has_signal": "Buying signal",
        "competes_with": "Competes with",
    }
    edges = [
        {"source": source, "target": target, "label": relation_labels.get(
            data["relationship"], data["relationship"].replace("_", " ").capitalize()
        )}
        for source, target, data in graph.edges(data=True)
    ]
    relations = {node: [] for node in graph}
    for edge in edges:
        origin, target = edge["source"], edge["target"]
        description = f"{graph.nodes[origin]['label']} / {edge['label']} / {graph.nodes[target]['label']}"
        relations[origin].append(description)
        relations[target].append(description)

    for column, layer in enumerate(layers):
        for index, node in enumerate(layer):
            data = graph.nodes[node]
            kind = data["entity_type"]
            description = data.get("description") or data.get("positioning")
            facts = [
                [label, str(data[field])]
                for field, label in (
                    ("industry", "Industry"),
                    ("title", "Role"),
                    ("product_name", "Product"),
                    ("verification", "Verification"),
                )
                if data.get(field)
            ]
            if data.get("fit_score") is not None:
                facts.insert(0, ["Fit score", f"{data['fit_score']}/100"])

            source_data = data
            if kind in {"Person", "Signal"}:
                for neighbor in (*graph.predecessors(node), *graph.successors(node)):
                    if graph.nodes[neighbor]["entity_type"] == "Company":
                        source_data = graph.nodes[neighbor]
                        break
            sources = [
                {"title": item["title"], "url": item["url"], "excerpt": item.get("excerpt")}
                for item in source_data.get("sources", [])
                if item["url"].lower().startswith(("https://", "http://"))
            ]
            nodes.append({
                "id": node,
                "name": data["label"],
                "kind": kind,
                "color": {
                    "Product": "#9cc4ff",
                    "Company": "#91e6b4",
                    "Person": "#dac0ff",
                    "Competitor": "#ffb2aa",
                    "Signal": "#ffd287",
                }[kind],
                "summary": description or " | ".join(value for _, value in facts[:2]),
                "description": description,
                "facts": facts,
                "relations": relations[node],
                "sources": sources,
                "source_heading": "Sources" if source_data is data else "Related company sources",
                "column": column,
                "row": index + (rows - len(layer)) / 2,
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "columns": len(layers),
        "rows": rows,
        "selected": selected,
        "signature": [(node["id"], node["name"]) for node in nodes],
    }


def visualize_graph(
    graph: nx.DiGraph,
) -> Digraph:

    dot = Digraph()

    dot.attr(
        rankdir="LR",
        bgcolor="transparent",
    )

    dot.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontcolor="white",
        fontsize="11",
    )

    dot.attr(
        "edge",
        color="#94A3B8",
        fontcolor="#94A3B8",
        fontsize="10",
    )

    for node_id, data in graph.nodes(data=True):

        entity_type = data["entity_type"]

        name = data["label"]

        if len(name) > 65:
            name = name[:62] + "..."

        label = f"{name}\n[{entity_type}]"

        if entity_type == "Company":
            label += (
                f"\nFit: {data['fit_score']}/100"
            )

        dot.node(
            node_id,
            label=escape(label),
            fillcolor=NODE_COLORS.get(
                entity_type,
                "#64748B",
            ),
            color="transparent",
        )

    for source, target, data in graph.edges(
        data=True
    ):

        dot.edge(
            source,
            target,
            label=escape(
                data["relationship"]
            ),
        )

    return dot


def find_opportunities(
    graph: nx.DiGraph,
) -> list[dict]:

    opportunities = []

    if "product" not in graph:
        return opportunities

    # Product <- Company -> Signal
    for company_id in graph.predecessors(
        "product"
    ):

        company = graph.nodes[company_id]

        if company["entity_type"] != "Company":
            continue

        for signal_id in graph.successors(
            company_id
        ):

            signal = graph.nodes[signal_id]

            if signal["entity_type"] != "Signal":
                continue

            opportunities.append({
                "company": company["label"],
                "fit_score": company["fit_score"],
                "signal": signal["label"],
                "path": (
                    f"{graph.nodes['product']['label']}"
                    f" <- {company['label']}"
                    f" -> {signal['label']}"
                ),
                "sources": company.get(
                    "sources", []
                ),
            })

    return sorted(
        opportunities,
        key=lambda item: item["fit_score"],
        reverse=True,
    )
