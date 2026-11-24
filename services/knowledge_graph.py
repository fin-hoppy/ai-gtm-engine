
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
