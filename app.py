
import streamlit as st

from models.product import Product
from models.icp import ICP
from services.icp_engine import generate_icp


# ==========================================
# Workspace Persistence
# ==========================================

import os

from dotenv import load_dotenv

from core.database import (
    STATE_KEYS,
    init_db,
    save_workspace,
    load_workspace,
)


load_dotenv()

PERSISTENCE_ENABLED = (
    os.getenv("GTM_LOCAL_PERSISTENCE", "0") == "1"
)


if PERSISTENCE_ENABLED:

    init_db()

    if "_workspace_loaded" not in st.session_state:

        has_existing_data = any(
            key in st.session_state
            for key in STATE_KEYS
        )

        if not has_existing_data:

            saved_data = load_workspace()

            for key in STATE_KEYS:

                if key in saved_data:

                    st.session_state[key] = (
                        saved_data[key]
                    )

        st.session_state["_workspace_loaded"] = True


st.set_page_config(
    page_title="Evidence GTM",
    page_icon="🎯",
    layout="wide",
)


def invalidate_approval():
    st.session_state.pop("approved_icp", None)


def reject_icp():
    st.session_state.pop("approved_icp", None)
    st.session_state.pop("icp_json", None)



def render_icp_profile(icp_data: dict):

    st.markdown("### Executive Summary")

    with st.container(border=True):
        st.write(icp_data.get("summary", ""))

    # Company profile
    company_size = icp_data.get(
        "company_size", {}
    )

    minimum = company_size.get("min_employees")
    maximum = company_size.get("max_employees")

    if minimum is not None and maximum is not None:
        employee_range = f"{minimum:,} - {maximum:,}"
    elif minimum is not None:
        employee_range = f"{minimum:,}+"
    elif maximum is not None:
        employee_range = f"Up to {maximum:,}"
    else:
        employee_range = "Unknown"

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Company Size",
        employee_range,
    )

    col2.metric(
        "Target Industries",
        len(icp_data.get("industries", [])),
    )

    col3.metric(
        "Buyer Personas",
        len(icp_data.get("buyer_personas", [])),
    )

    st.write(
        "Target Regions:",
        ", ".join(
            icp_data.get("target_regions", [])
        ) or "Not specified",
    )

    st.divider()

    # Target industries
    st.subheader("Target Industries")

    industries = icp_data.get("industries", [])

    for industry in industries:

        col1, col2 = st.columns([3, 1])

        confidence = industry.get(
            "confidence", 0
        )

        col1.markdown(
            f"**{industry['name']}**"
        )

        col2.write(f"{confidence:.0%}")

        st.progress(confidence)

        st.caption(
            f"NAICS: {industry.get('naics_code') or 'N/A'}"
            f" | SIC: {industry.get('sic_code') or 'N/A'}"
        )

    st.caption(
        "Confidence scores are AI-generated estimates."
    )

    st.divider()

    # Buyer personas
    st.subheader("Buyer Personas")

    personas = icp_data.get("buyer_personas", [])

    for i in range(0, len(personas), 2):

        columns = st.columns(2)

        for column, persona in zip(
            columns,
            personas[i:i + 2],
        ):

            with column:

                with st.container(border=True):

                    st.markdown(
                        f"#### {persona['title']}"
                    )

                    st.caption(
                        persona.get("department", "")
                    )

                    st.write(
                        "Seniority:",
                        persona.get("seniority", ""),
                    )

                    confidence = persona.get(
                        "confidence", 0
                    )

                    st.progress(confidence)

                    st.caption(
                        f"Confidence: {confidence:.0%}"
                    )

                    st.markdown("**Pain Points**")

                    for pain in persona.get(
                        "pain_points", []
                    ):

                        st.write("•", pain)

    st.divider()

    # Buying signals
    st.subheader("Buying Signals")

    for signal in icp_data.get(
        "buying_signals", []
    ):

        with st.container(border=True):

            st.markdown(
                f"**{signal['event']}**"
            )

            st.write(
                signal.get("reasoning", "")
            )

            confidence = signal.get(
                "confidence", 0
            )

            st.progress(confidence)

            st.caption(
                f"Confidence: {confidence:.0%}"
            )

    # Expansion opportunities
    with st.expander("Expansion Opportunities"):

        for segment in icp_data.get(
            "expansion_segments", []
        ):

            st.markdown(
                f"**{segment['industry']}**"
            )

            st.write(
                segment.get("use_case", "")
            )

            st.write(
                segment.get("reasoning", "")
            )

            st.caption(
                f"Confidence: "
                f"{segment.get('confidence', 0):.0%}"
            )

            st.divider()

    # Negative signals
    with st.expander("Negative Signals"):

        for signal in icp_data.get(
            "negative_signals", []
        ):

            st.warning(signal)

    # Assumptions
    with st.expander("AI Assumptions"):

        for assumption in icp_data.get(
            "assumptions", []
        ):

            st.write("•", assumption)


st.title("Evidence GTM")
st.caption("Better targeting, not more outreach.")


# ==========================================
# Workspace Navigation
# ==========================================

(
    workspace_tab_icp,
    workspace_tab_discovery,
    workspace_tab_graph,
    workspace_tab_outreach,
    workspace_tab_pipeline,
) = st.tabs([
    "Product & ICP",
    "Discovery",
    "Knowledge Graph",
    "Outreach",
    "Pipeline",
])


# ==========================================
# Module 1: Product Intake & ICP Engine
# ==========================================


with workspace_tab_icp:


    st.header("Product Intake")

    st.caption(
        "Define your product and target market."
    )

    saved_product = st.session_state.get(
        "product", {}
    )

    with st.form("product_intake"):

        name = st.text_input(
            "Product Name",
            value=saved_product.get("name", ""),
        )

        description = st.text_area(
            "Product Description",
            value=saved_product.get(
                "description", ""
            ),
            height=120,
        )

        col1, col2 = st.columns(2)

        with col1:

            features = st.text_area(
                "Core Features (one per line)",
                value="\n".join(
                    saved_product.get("features", [])
                ),
                height=180,
            )

            pricing = st.text_input(
                "Pricing",
                value=saved_product.get("pricing", ""),
            )

            monetization = st.text_input(
                "Monetization Model",
                value=saved_product.get(
                    "monetization_model", ""
                ),
            )

        with col2:

            constraints = st.text_area(
                "Technical Constraints",
                value=saved_product.get(
                    "technical_constraints", ""
                ),
                height=180,
            )

            contract_value = st.text_input(
                "Contract Value",
                value=saved_product.get(
                    "contract_value", ""
                ),
            )

            regions = st.text_input(
                "Target Regions (comma separated)",
                value=", ".join(
                    saved_product.get(
                        "target_regions", []
                    )
                ),
            )

        with st.expander(
            "Additional Business Information"
        ):

            customers = st.text_area(
                "Existing Customers",
                value=saved_product.get(
                    "existing_customers", ""
                ),
            )

            reference_wins = st.text_area(
                "Reference Wins",
                value=saved_product.get(
                    "reference_wins", ""
                ),
            )

        submitted = st.form_submit_button(
            "Generate ICP",
            type="primary",
        )

    if saved_product:

        st.caption(
            "Product information restored "
            "from workspace."
        )


    if submitted:

        reject_icp()

        try:
            product = Product(
                name=name.strip(),
                description=description.strip(),
                features=[
                    line.strip()
                    for line in features.splitlines()
                    if line.strip()
                ],
                technical_constraints=constraints,
                existing_customers=customers,
                reference_wins=reference_wins,
                pricing=pricing,
                contract_value=contract_value,
                monetization_model=monetization,
                target_regions=[
                    region.strip()
                    for region in regions.split(",")
                    if region.strip()
                ],
            )

            with st.spinner("Analyzing product with MOSS..."):
                icp = generate_icp(product)

            st.session_state["product"] = product.model_dump()

            st.session_state["icp_json"] = (
                icp.model_dump_json(indent=2)
            )

            st.success("ICP generated successfully.")

        except Exception as e:
            st.error(
                f"ICP generation failed: {type(e).__name__}"
            )


    if "icp_json" in st.session_state:

        st.divider()
        st.header("2. ICP Review")


        with st.expander(
            "Advanced ICP Editor (JSON)",
            expanded=(
                "approved_icp"
                not in st.session_state
            ),
        ):

            edited_json = st.text_area(
                "Review and edit the generated ICP",
                key="icp_json",
                height=500,
                on_change=invalidate_approval,
            )


        st.caption(
            "Confidence scores and expansion segments "
            "are AI-generated estimates, not verified facts."
        )

        approve_col, reject_col = st.columns(2)

        with approve_col:

            if st.button("Approve ICP", type="primary"):

                try:
                    approved = ICP.model_validate_json(
                        edited_json
                    )

                    st.session_state["approved_icp"] = (
                        approved.model_dump()
                    )

                except Exception:
                    st.error("Invalid ICP data.")

        with reject_col:

            st.button(
                "Reject ICP",
                on_click=reject_icp,
            )



    if "approved_icp" in st.session_state:

        st.divider()
        st.header("Ideal Customer Profile")

        st.success("ICP approved by the user.")

        render_icp_profile(
            st.session_state["approved_icp"]
        )

        with st.expander("Raw ICP Data"):

            st.json(
                st.session_state["approved_icp"]
            )


# ==========================================
# Module 2: Customer & Competitor Discovery
# ==========================================

from models.lead import DiscoveryResult
from services.discovery import discover


with workspace_tab_discovery:


    st.header("Customer & Competitor Discovery")

    if "approved_icp" in st.session_state:

        product = Product.model_validate(
            st.session_state["product"]
        )

        approved_icp = ICP.model_validate(
            st.session_state["approved_icp"]
        )

        research_context = (
            product.model_dump_json()
            + approved_icp.model_dump_json()
        )

        if (
            st.session_state.get("research_context")
            != research_context
        ):
            st.session_state.pop(
                "discovery_result", None
            )

        st.caption(
            "MOSS researches public web sources "
            "to identify potential customers "
            "and competitors."
        )

        if st.button(
            "Discover Customers & Competitors",
            type="primary",
        ):

            st.session_state.pop(
                "discovery_result", None
            )

            try:

                with st.spinner(
                    "MOSS is researching public sources..."
                ):

                    result = discover(
                        product,
                        approved_icp,
                    )

                st.session_state["discovery_result"] = (
                    result.model_dump(mode="json")
                )

                st.session_state["research_context"] = (
                    research_context
                )

                st.success("Research completed.")

            except Exception as e:

                st.error(
                    f"Discovery failed: "
                    f"{type(e).__name__}"
                )

                if getattr(e, "code", None):
                    st.code(str(e.code))

                if isinstance(e, RuntimeError):
                    st.warning(str(e))


        if "discovery_result" in st.session_state:

            result = DiscoveryResult.model_validate(
                st.session_state["discovery_result"]
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Prospective Companies",
                len(result.prospects),
            )

            col2.metric(
                "Competitors",
                len(result.competitors),
            )

            st.caption(
                "AI-researched candidates and "
                "heuristic scores. Review sources "
                "before using the results."
            )

            prospects_tab, competitors_tab = st.tabs([
                "Prospects",
                "Competitors",
            ])

            with prospects_tab:

                if not result.prospects:
                    st.info("No supported prospects found.")

                prospects = sorted(
                    result.prospects,
                    key=lambda p: p.fit_score,
                    reverse=True,
                )

                for prospect in prospects:

                    with st.container(border=True):

                        st.subheader(
                            prospect.company_name
                        )

                        score_col, detail_col = st.columns(
                            [1, 3]
                        )

                        with score_col:

                            st.metric(
                                "Fit Score",
                                f"{prospect.fit_score}/100",
                            )

                            st.progress(
                                prospect.fit_score / 100
                            )

                        with detail_col:

                            st.write(
                                "Industry:",
                                prospect.industry,
                            )

                            st.write(
                                "Headquarters:",
                                prospect.headquarters
                                or "Unknown",
                            )

                            st.write(
                                "Employees:",
                                prospect.employee_count
                                if prospect.employee_count
                                is not None
                                else "Unknown",
                            )

                            st.link_button(
                                "Company Website",
                                str(prospect.website),
                            )

                        st.write(prospect.description)

                        st.markdown("**Why this company?**")
                        st.write(prospect.match_reason)

                        st.markdown("**Potential Buyer**")

                        st.write(
                            prospect.buyer_name
                            or "Not verified"
                        )

                        st.write(
                            prospect.buyer_title
                            or "Unknown"
                        )

                        st.markdown("**Buying Signals**")

                        for signal in prospect.buying_signals:
                            st.write("•", signal)

                        if prospect.negative_signals:

                            st.markdown(
                                "**Negative Signals**"
                            )

                            for signal in prospect.negative_signals:
                                st.warning(signal)

                        with st.expander("Evidence & Sources"):

                            for source in prospect.sources:

                                st.link_button(
                                    source.title,
                                    str(source.url),
                                )

                                st.text(source.excerpt)


            with competitors_tab:

                if not result.competitors:
                    st.info("No supported competitors found.")

                for competitor in result.competitors:

                    with st.container(border=True):

                        st.subheader(
                            competitor.company_name
                        )

                        st.write(
                            "Product:",
                            competitor.product_name,
                        )

                        st.write(
                            "Positioning:",
                            competitor.positioning,
                        )

                        st.write(
                            "Value Proposition:",
                            competitor.value_proposition,
                        )

                        st.write(
                            "Pricing:",
                            competitor.pricing
                            or "Not publicly verified",
                        )

                        st.link_button(
                            "Competitor Website",
                            str(competitor.website),
                        )

                        st.markdown(
                            "**Differentiators**"
                        )

                        for item in competitor.differentiators:
                            st.write("•", item)

                        with st.expander("Evidence & Sources"):

                            for source in competitor.sources:

                                st.link_button(
                                    source.title,
                                    str(source.url),
                                )

                                st.text(source.excerpt)
    else:
        st.info("Open Product & ICP and approve an ICP to start discovery.")


# ==========================================
# Module 3: Dynamic Knowledge Graph
# ==========================================

from services.knowledge_graph import (
    build_graph,
    build_graph_view,
    find_opportunities,
    visualize_graph,
)


from pathlib import Path as GraphAssetPath

_graph_assets = GraphAssetPath(__file__).resolve().parent / "services"
_graph_canvas = st.components.v2.component(
    "knowledge_graph_canvas",
    html="""
    <div class="kg-shell">
      <div class="kg-toolbar">
        <span class="kg-help">Hover to preview. Click to select. Drag the background to move.</span>
        <div class="kg-controls" role="group" aria-label="Graph zoom">
          <button type="button" data-zoom="0.85" aria-label="Zoom out">&minus;</button>
          <button type="button" data-zoom="1.18" aria-label="Zoom in">+</button>
          <button type="button" data-zoom="fit">Fit</button>
        </div>
      </div>
      <div class="kg-viewport" role="region" aria-label="Knowledge graph">
        <div class="kg-space"><div class="kg-scene"></div></div>
      </div>
      <article class="kg-paper" aria-label="Entity preview" hidden></article>
    </div>
    """,
    css=(_graph_assets / "knowledge_graph.css").read_text(encoding="utf-8"),
    js=(_graph_assets / "knowledge_graph.js").read_text(encoding="utf-8"),
)


def render_graph_explorer(graph):
    import re

    def plain(value):
        return re.sub(r"([\\*_{}\[\]<>!~|])", r"\\\1", " ".join(str(value).split()))

    root = "product"
    selection_key = "graph_selected_entity"
    saved_id, saved_label = st.session_state.get(selection_key, (root, ""))
    selected = root
    if saved_id in graph and graph.nodes[saved_id]["label"] == saved_label:
        selected = saved_id

    chart_key = "knowledge_graph_canvas"

    def select_from_chart():
        pick = st.session_state.get(chart_key, {}).get("node_pick")
        if not isinstance(pick, dict):
            return
        node_id, name = pick.get("id"), pick.get("name")
        if node_id in graph and graph.nodes[node_id]["label"] == name:
            st.session_state[selection_key] = (node_id, name)
            st.session_state["graph_entity_search"] = ""

    st.subheader("Graph overview")
    _graph_canvas(
        data=build_graph_view(graph, selected),
        key=chart_key,
        on_node_pick_change=select_from_chart,
    )

    def node_button(node_id):
        label = graph.nodes[node_id]["label"]
        st.button(
            plain(label),
            key=f"graph_entity_{node_id}",
            type="primary" if node_id == selected else "secondary",
            width="stretch",
            on_click=st.session_state.update,
            args=({selection_key: (node_id, label)},),
        )

    tree, details = st.columns([3, 2], gap="large")
    with tree:
        st.subheader("Explore entities")
        query = st.text_input(
            "Find an entity",
            placeholder="Search products, companies, people, or signals",
            key="graph_entity_search",
        ).strip().casefold()

        def matches(node_id):
            return query in graph.nodes[node_id]["label"].casefold()

        root_matches = matches(root)
        if root_matches:
            st.caption("Product")
            node_button(root)

        prospects = []
        for company in graph.predecessors(root):
            children = [
                node for node in (*graph.predecessors(company), *graph.successors(company))
                if node != root
            ]
            if not matches(company):
                children = [node for node in children if matches(node)]
                if not children:
                    continue
            prospects.append((company, children))

        competitors = [node for node in graph.successors(root) if matches(node)]
        if prospects:
            st.markdown("**Prospects**")
        for company, children in prospects:
            company_data = graph.nodes[company]
            label = plain(company_data["label"])
            score = company_data["fit_score"]
            with st.expander(
                f"{label} (Fit {score}/100)",
                expanded=bool(query) or selected == company or selected in children,
            ):
                node_button(company)
                for child in children:
                    kind = graph.nodes[child]["entity_type"]
                    st.caption("Decision-maker" if kind == "Person" else "Buying signal")
                    node_button(child)

        if competitors:
            st.markdown("**Competitors**")
            for competitor in competitors:
                node_button(competitor)

        if not prospects and not competitors:
            if query and not root_matches:
                st.info("No entities match your search.")
            elif not query:
                st.info("Discovery returned no prospects or competitors.")

    with details:
        data = graph.nodes[selected]
        st.subheader("Entity details")
        st.markdown(f"**{plain(data['label'])}**")
        st.caption(data["entity_type"])
        for field, label in (
            ("industry", "Industry"),
            ("fit_score", "Fit score"),
            ("title", "Role"),
            ("product_name", "Product"),
            ("verification", "Verification"),
        ):
            if data.get(field) is not None:
                value = f"{data[field]}/100" if field == "fit_score" else data[field]
                st.markdown(f"**{label}**: {plain(value)}")
        for field in ("description", "positioning"):
            if data.get(field):
                st.write(plain(data[field]))
        if data.get("website"):
            st.link_button("Company website", data["website"])

        edges = list(graph.in_edges(selected, data=True)) + list(graph.out_edges(selected, data=True))
        if edges:
            st.markdown("**Relationships**")
        evidence = data.get("sources", [])
        for origin, destination, edge in edges:
            source = graph.nodes[origin]
            target = graph.nodes[destination]
            relation = edge["relationship"].replace("_", " ")
            st.write(f"{plain(source['label'])} **{relation}** {plain(target['label'])}")
            if data["entity_type"] in {"Person", "Signal"}:
                related = source if destination == selected else target
                if related["entity_type"] == "Company":
                    evidence = related.get("sources", [])

        if evidence:
            heading = "Related company sources" if data["entity_type"] in {"Person", "Signal"} else "Sources"
            st.markdown(f"**{heading}**")
            for item in evidence:
                st.link_button(plain(item["title"]), item["url"])
                st.write(plain(item["excerpt"]))


with workspace_tab_graph:


    st.header("Dynamic Knowledge Graph")

    if (
        "approved_icp" in st.session_state
        and "discovery_result" in st.session_state
    ):

        st.caption(
            "Connect products, companies, "
            "decision-makers and buying signals."
        )

        graph_product = Product.model_validate(
            st.session_state["product"]
        )

        graph_result = DiscoveryResult.model_validate(
            st.session_state["discovery_result"]
        )

        graph = build_graph(
            graph_product,
            graph_result,
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Entities",
            graph.number_of_nodes(),
        )

        col2.metric(
            "Relationships",
            graph.number_of_edges(),
        )

        col3.metric(
            "Entity Types",
            len({
                data["entity_type"]
                for _, data in graph.nodes(data=True)
            }),
        )

        render_graph_explorer(graph)

        with st.expander("Directed graph overview"):
            st.graphviz_chart(visualize_graph(graph), width="stretch")

        # Relationship inspection
        with st.expander("Explore Relationships"):

            relationships = []

            for source, target, data in graph.edges(
                data=True
            ):

                relationships.append({
                    "Source": graph.nodes[source]["label"],
                    "Relationship": data["relationship"],
                    "Target": graph.nodes[target]["label"],
                })

            if relationships:
                st.dataframe(relationships)
            else:
                st.info("No relationships available.")

        # Multi-hop reasoning
        st.subheader("Graph-based Opportunities")

        opportunities = find_opportunities(graph)

        if not opportunities:

            st.info(
                "No buying-signal paths found "
                "in the current graph."
            )

        for opportunity in opportunities:

            with st.container(border=True):

                st.markdown(
                    f"### {opportunity['company']}"
                )

                st.metric(
                    "Fit Score",
                    f"{opportunity['fit_score']}/100",
                )

                st.write(
                    "Buying Signal:",
                    opportunity["signal"],
                )

                st.code(
                    opportunity["path"],
                    language=None,
                )

                with st.expander(
                    "Related Company Sources"
                ):

                    for source in opportunity["sources"]:

                        st.link_button(
                            source["title"],
                            source["url"],
                        )

                        st.text(source["excerpt"])
    elif "approved_icp" not in st.session_state:
        st.info("Open Product & ICP and approve an ICP first.")
    else:
        st.info(
            "Open Discovery and select Discover Customers & Competitors."
        )


# ==========================================
# Module 4: Enrichment & Outreach
# ==========================================

import hashlib
from uuid import uuid4

from models.outreach import OutreachStatus
from services.outreach import generate_outreach

with workspace_tab_outreach:

    st.header("Enrichment & Outreach")

    if (
        "approved_icp" in st.session_state
        and "discovery_result" in st.session_state
    ):

        outreach_product = Product.model_validate(
            st.session_state["product"]
        )

        outreach_result = DiscoveryResult.model_validate(
            st.session_state["discovery_result"]
        )

        prospects = outreach_result.prospects

        if not prospects:

            st.info("Discovery found no prospects to contact. Review the approved ICP in Product & ICP and run Discovery again.")

        else:

            selected_index = st.selectbox(
                "Select a prospective customer",
                options=list(range(len(prospects))),
                format_func=lambda i: (
                    prospects[i].company_name
                ),
            )

            prospect = prospects[selected_index]

            # Isolate records belonging to different
            # products, ICPs and discovery results.
            context = (
                outreach_product.model_dump_json()
                + ICP.model_validate(
                    st.session_state["approved_icp"]
                ).model_dump_json()
                + outreach_result.model_dump_json()
            )

            scope = hashlib.sha256(
                context.encode()
            ).hexdigest()[:20]

            record_key = f"{scope}_{selected_index}"

            records = st.session_state.setdefault(
                "outreach_records",
                {},
            )

            st.subheader("Contact Intelligence")

            col1, col2 = st.columns(2)

            col1.metric(
                "Company",
                prospect.company_name,
            )

            col2.metric(
                "Fit Score",
                f"{prospect.fit_score}/100",
            )

            st.write(
                "Potential decision-maker:",
                prospect.buyer_name or "Unknown",
            )

            st.write(
                "Position:",
                prospect.buyer_title or "Unknown",
            )

            st.link_button(
                "Visit Official Website",
                str(prospect.website),
            )

            st.caption(
                "Agent-reported identity. "
                "Contact verification is not automated."
            )

            st.markdown("**Buying Signals**")

            for signal in prospect.buying_signals:
                st.write("•", signal)

            if st.button(
                "Generate Personalized Outreach",
                type="primary",
                key=f"generate_{record_key}",
            ):

                records.pop(record_key, None)

                try:

                    with st.spinner(
                        "MOSS is generating outreach..."
                    ):

                        draft = generate_outreach(
                            outreach_product,
                            prospect,
                        )

                    records[record_key] = {
                        "scope": scope,
                        "company": prospect.company_name,
                        "website": str(prospect.website),
                        "draft": draft.model_dump(),
                        "contact": "",
                        "contact_source": "",
                        "status": OutreachStatus.DRAFT.value,
                        "revision": uuid4().hex,
                    }

                except Exception as e:

                    st.error(
                        f"Outreach generation failed: "
                        f"{type(e).__name__}"
                    )

            record = records.get(record_key)

            if record:

                st.subheader("Human-in-the-Loop Review")

                if record["status"] == "Rejected":

                    st.warning("Message rejected.")

                else:

                    draft = record["draft"]
                    revision = record["revision"]

                    editor_col, evidence_col = st.columns([3, 2])
                    with editor_col:
                        st.markdown("#### Email Draft")
                        subject = st.text_input(
                            "Subject",
                            value=draft["subject"],
                            key=f"subject_{revision}",
                        )

                        body = st.text_area(
                            "Email Body",
                            value=draft["body"],
                            height=260,
                            key=f"body_{revision}",
                        )

                        contact = st.text_input(
                            "Public Business Contact (optional)",
                            value=record["contact"],
                            key=f"contact_{revision}",
                        )

                        contact_source = st.text_input(
                            "Contact Source URL (optional)",
                            value=record["contact_source"],
                            key=f"contact_source_{revision}",
                        )

                    with evidence_col:
                        st.markdown("#### Review Evidence")
                        with st.expander(
                            "Generation Rationale"
                        ):

                            st.write(draft["reasoning"])

                            st.caption(
                                "Rationale for the original "
                                "AI-generated draft."
                            )

                        with st.expander(
                            "Evidence Used",
                            expanded=True,
                        ):

                            for index in draft["source_indices"]:

                                source = prospect.sources[index]

                                st.write(source.title)
                                st.text(str(source.url))
                                st.text(source.excerpt)

                    # Any edit invalidates earlier approval.
                    if (
                        subject != draft["subject"]
                        or body != draft["body"]
                        or contact != record["contact"]
                        or contact_source
                        != record["contact_source"]
                    ):

                        record["status"] = "Draft"

                        draft["subject"] = subject
                        draft["body"] = body

                        record["contact"] = contact
                        record["contact_source"] = (
                            contact_source
                        )

                    st.caption(
                        "Review the message and its sources "
                        "before approving. No message is "
                        "automatically transmitted."
                    )

                    approve_col, reject_col = st.columns(2)

                    with approve_col:

                        if st.button(
                            "Approve Outreach",
                            type="primary",
                            key=f"approve_{revision}",
                            disabled=(
                                not subject.strip()
                                or not body.strip()
                            ),
                        ):

                            record["status"] = "Approved"

                    with reject_col:

                        if st.button(
                            "Reject Outreach",
                            key=f"reject_{revision}",
                        ):

                            record["status"] = "Rejected"
                            st.rerun()

                    st.write(
                        "Status:",
                        record["status"],
                    )

                    if record["status"] == "Approved":

                        st.success(
                            "Message approved by the user."
                        )

                        export_text = (
                            f"Company: "
                            f"{record['company']}\n"
                            f"Contact: {contact}\n"
                            f"Subject: {subject}\n\n"
                            f"{body}"
                        )

                        st.download_button(
                            "Export Approved Email",
                            data=export_text,
                            file_name="approved_outreach.txt",
                            mime="text/plain",
                            key=f"export_{revision}",
                        )

                        st.info(
                            "Approved draft only. "
                            "No email has been sent."
                        )
    elif "approved_icp" not in st.session_state:
        st.info("Open Product & ICP and approve an ICP first.")
    else:
        st.info(
            "Open Discovery and select Discover Customers & Competitors."
        )


# ==========================================
# Module 5: Lead Management & Dashboard
# ==========================================

import json

from services.lead_manager import (
    STAGES,
    TRANSITIONS,
    sync_pipeline,
    update_stage,
    calculate_metrics,
)


with workspace_tab_pipeline:


    st.header("Lead Management & Dashboard")

    if (
        "approved_icp" in st.session_state
        and "discovery_result" in st.session_state
    ):

        pipeline_product = Product.model_validate(
            st.session_state["product"]
        )

        pipeline_icp = ICP.model_validate(
            st.session_state["approved_icp"]
        )

        pipeline_result = DiscoveryResult.model_validate(
            st.session_state["discovery_result"]
        )

        pipeline_context = (
            pipeline_product.model_dump_json()
            + pipeline_icp.model_dump_json()
            + pipeline_result.model_dump_json()
        )

        pipeline_scope = hashlib.sha256(
            pipeline_context.encode()
        ).hexdigest()[:20]

        pipelines = st.session_state.setdefault(
            "pipelines",
            {},
        )

        pipeline = pipelines.setdefault(
            pipeline_scope,
            {},
        )

        outreach_records = st.session_state.get(
            "outreach_records",
            {},
        )

        pipeline = sync_pipeline(
            pipeline,
            pipeline_result.prospects,
            outreach_records,
            pipeline_scope,
        )

        metrics = calculate_metrics(pipeline)

        st.info(
            "Demo mode: pipeline transitions are "
            "simulated. No emails are transmitted."
        )

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Leads",
            metrics["total"],
        )

        col2.metric(
            "Approved Drafts",
            metrics["approved"],
        )

        col3.metric(
            "Meetings",
            metrics["reached"]["Meeting Booked"],
        )

        col4.metric(
            "Closed Deals",
            metrics["reached"]["Closed"],
        )

        # Kanban board
        st.subheader("Sales Pipeline")

        kanban_stages = [
            "Matched",
            "Contacted",
            "Replied",
            "Meeting Booked",
            "Closed / Lost",
        ]

        columns = st.columns(5)

        for column, stage in zip(
            columns, kanban_stages
        ):

            with column:

                st.markdown(f"**{stage}**")

                for lead in pipeline.values():

                    matches = (
                        lead["stage"] == stage
                        or (
                            stage == "Closed / Lost"
                            and lead["stage"] in [
                                "Closed", "Lost"
                            ]
                        )
                    )

                    if not matches:
                        continue

                    with st.container(border=True):

                        st.write(lead["company"])

                        st.caption(
                            f"Fit: {lead['fit_score']}/100"
                        )

                        st.caption(
                            f"Outreach: "
                            f"{lead['outreach_status']}"
                        )

                        if lead["stage"] in [
                            "Closed", "Lost"
                        ]:
                            st.write(lead["stage"])

        # Lead management
        st.subheader("Manage Lead")

        if pipeline:

            lead_id = st.selectbox(
                "Select Lead",
                options=list(pipeline.keys()),
                format_func=lambda key: (
                    pipeline[key]["company"]
                ),
                key=f"pipeline_select_{pipeline_scope}",
            )

            selected_lead = pipeline[lead_id]

            st.write(
                "Current Stage:",
                selected_lead["stage"],
            )

            st.write(
                "Outreach Status:",
                selected_lead["outreach_status"],
            )

            available_stages = TRANSITIONS[
                selected_lead["stage"]
            ]

            if available_stages:

                next_stage = st.selectbox(
                    "Next Stage",
                    options=available_stages,
                    key=(
                        f"stage_{lead_id}_"
                        f"{selected_lead['stage']}"
                    ),
                )

                if st.button(
                    "Simulate Stage Transition",
                    key=f"transition_{lead_id}",
                ):

                    try:

                        update_stage(
                            selected_lead,
                            next_stage,
                        )

                        st.rerun()

                    except ValueError as error:
                        st.warning(str(error))

            else:

                st.info(
                    "This lead has reached "
                    "a terminal stage."
                )

        else:

            st.info("No leads to move. The pipeline is populated from prospects found in Discovery.")

        # Conversion analytics
        st.subheader("Performance Analytics")

        def display_rate(value):

            if value is None:
                return "N/A"

            return f"{value:.1f}%"

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Reply Rate",
            display_rate(metrics["reply_rate"]),
        )

        col2.metric(
            "Meeting Conversion",
            display_rate(metrics["meeting_rate"]),
        )

        col3.metric(
            "Close Rate",
            display_rate(metrics["close_rate"]),
        )

        st.caption(
            "Conversion metrics are based on "
            "simulated lead transitions, "
            "not real campaign performance."
        )

        st.markdown("**Funnel Progression**")

        for stage in STAGES:

            count = metrics["reached"][stage]

            ratio = (
                count / metrics["total"]
                if metrics["total"]
                else 0
            )

            st.write(f"{stage}: {count}")

            st.progress(ratio)

        # Audit log
        st.subheader("Activity & Audit Log")

        history = []

        for lead in pipeline.values():

            for event in lead["history"]:

                history.append({
                    "Company": lead["company"],
                    "Timestamp": event["timestamp"],
                    "Actor": event["actor"],
                    "Action": event["action"],
                    "From": event["from"],
                    "To": event["to"],
                    "Simulated": event["simulated"],
                })

        history.sort(
            key=lambda event: event["Timestamp"],
            reverse=True,
        )

        if history:

            st.dataframe(
                history,
                hide_index=True,
            )

        else:

            st.info("No activity recorded.")

        # Export
        st.download_button(
            "Export Pipeline Data",
            data=json.dumps(
                {
                    "mode": "demo",
                    "product": pipeline_product.name,
                    "leads": list(pipeline.values()),
                    "metrics": metrics,
                },
                indent=2,
                ensure_ascii=False,
            ),
            file_name="pipeline_export.json",
            mime="application/json",
            key=f"export_pipeline_{pipeline_scope}",
        )
    elif "approved_icp" not in st.session_state:
        st.info("Open Product & ICP and approve an ICP first.")
    else:
        st.info(
            "Open Discovery and select Discover Customers & Competitors."
        )


# ==========================================
# Save Workspace
# ==========================================

if PERSISTENCE_ENABLED:

    try:

        save_workspace(st.session_state)

        st.sidebar.caption(
            "Workspace: Saved locally"
        )

    except Exception as error:

        st.sidebar.warning(
            f"Workspace save failed: "
            f"{type(error).__name__}"
        )

