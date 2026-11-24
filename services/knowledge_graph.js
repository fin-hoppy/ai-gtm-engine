const CARD_WIDTH = 228;
const CARD_HEIGHT = 116;
const STEP_X = 380;
const STEP_Y = 154;
const MARGIN = 24;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function svg(tag, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

function paperContent(paper, node) {
  paper.replaceChildren(element("div", "kg-kicker", node.kind), element("h3", "", node.name));
  function section(title, content) {
    const group = element("section");
    group.append(element("h4", "", title), content);
    paper.append(group);
  }

  if (node.description) section("Overview", element("p", "", node.description));
  if (node.facts.length) {
    const facts = element("dl");
    for (const [label, value] of node.facts) {
      const item = element("div");
      item.append(element("dt", "", label), element("dd", "", value));
      facts.append(item);
    }
    section("At a glance", facts);
  }
  if (node.relations.length) {
    const relations = element("ul");
    for (const relation of node.relations) relations.append(element("li", "", relation));
    section("Connections", relations);
  }
  if (node.sources.length) {
    const sources = element("ul");
    for (const source of node.sources) {
      const item = element("li");
      const link = element("a", "", source.title);
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      item.append(link);
      if (source.excerpt) item.append(element("p", "", source.excerpt));
      sources.append(item);
    }
    section(node.source_heading, sources);
  }
}

export default function render({parentElement, data, setTriggerValue}) {
  const shell = parentElement.querySelector(".kg-shell");
  const viewport = shell.querySelector(".kg-viewport");
  const space = shell.querySelector(".kg-space");
  const scene = shell.querySelector(".kg-scene");
  const paper = shell.querySelector(".kg-paper");
  const previous = shell.graphView;
  const signature = JSON.stringify(data.signature);
  const graphChanged = previous?.signature !== signature;
  const changedSelection = previous?.selected !== data.selected;
  const events = new AbortController();
  const listen = (node, event, handler, options = {}) =>
    node.addEventListener(event, handler, {...options, signal: events.signal});
  let closeTimer;
  let paperOwner;
  let pan;
  let zoom = previous?.zoom ?? 1;
  let selected = data.selected;

  const height = (data.rows - 1) * STEP_Y + CARD_HEIGHT + MARGIN * 2;
  const width = (data.columns - 1) * STEP_X + CARD_WIDTH + MARGIN * 2;
  if (graphChanged && viewport.clientWidth) {
    zoom = Math.max(0.8, Math.min(1, viewport.clientWidth / width));
  }
  const oldLeft = viewport.scrollLeft;
  const oldTop = viewport.scrollTop;
  viewport.style.setProperty("--viewport-height", Math.min(Math.max(height, 330), 560) + "px");
  scene.style.width = width + "px";
  scene.style.height = height + "px";

  function hidePaper() {
    clearTimeout(closeTimer);
    paper.hidden = true;
    paperOwner?.setAttribute("aria-expanded", "false");
    paperOwner = null;
  }

  function showPaper(card, node) {
    clearTimeout(closeTimer);
    if (paperOwner === card && !paper.hidden) return;
    paperOwner?.setAttribute("aria-expanded", "false");
    paperOwner = card;
    card.setAttribute("aria-expanded", "true");
    paperContent(paper, node);
    paper.hidden = false;
    const anchor = card.getBoundingClientRect();
    const bounds = shell.getBoundingClientRect();
    const right = anchor.right - bounds.left + 10;
    const left = anchor.left - bounds.left - paper.offsetWidth - 10;
    const fitsRight = right + paper.offsetWidth <= bounds.width - 8;
    if (fitsRight || left >= 8) {
      paper.style.left = (fitsRight ? right : left) + "px";
      paper.style.maxHeight = Math.min(390, viewport.clientHeight - 24) + "px";
      const preferredTop = anchor.top - bounds.top;
      paper.style.top = Math.max(38, Math.min(preferredTop, bounds.height - paper.offsetHeight - 8)) + "px";
    } else {
      const below = anchor.bottom - bounds.top + 7;
      const above = anchor.top - bounds.top - 7;
      const placeBelow = bounds.height - below >= above - 8;
      const available = placeBelow ? bounds.height - below - 8 : above - 8;
      paper.style.left = "8px";
      paper.style.maxHeight = Math.max(85, Math.min(340, available)) + "px";
      paper.style.top = (placeBelow ? below : above - paper.offsetHeight) + "px";
    }
    paper.scrollTop = 0;
  }

  function scheduleClose() {
    clearTimeout(closeTimer);
    closeTimer = setTimeout(hidePaper, 180);
  }

  function applyZoom(value) {
    zoom = value;
    scene.style.transform = "scale(" + zoom + ")";
    space.style.width = Math.ceil(width * zoom) + "px";
    space.style.height = Math.ceil(height * zoom) + "px";
    shell.graphView = {signature, selected, zoom};
  }

  function changeZoom(value, anchorX, anchorY) {
    const next = Math.max(0.35, Math.min(1.6, value));
    const ratio = next / zoom;
    const left = (viewport.scrollLeft + anchorX) * ratio - anchorX;
    const top = (viewport.scrollTop + anchorY) * ratio - anchorY;
    hidePaper();
    applyZoom(next);
    viewport.scrollTo(left, top);
  }

  const coordinates = new Map(data.nodes.map(node => [node.id, {
    x: MARGIN + node.column * STEP_X,
    y: MARGIN + node.row * STEP_Y,
  }]));
  const links = svg("svg", {class: "kg-links", width, height, "aria-hidden": "true"});
  const edges = [];
  for (const edge of data.edges) {
    const source = coordinates.get(edge.source);
    const target = coordinates.get(edge.target);
    const forward = source.x < target.x;
    const fromX = source.x + (forward ? CARD_WIDTH : 0);
    const toX = target.x + (forward ? 0 : CARD_WIDTH);
    const fromY = source.y + CARD_HEIGHT / 2;
    const toY = target.y + CARD_HEIGHT / 2;
    const midX = (fromX + toX) / 2;
    const midY = (fromY + toY) / 2;
    const direction = forward ? 1 : -1;
    const caption = forward ? edge.label + "  →" : "←  " + edge.label;
    const labelWidth = Math.max(92, caption.length * 7 + 16);
    const lead = midX - direction * labelWidth / 2;
    const tail = midX + direction * labelWidth / 2;
    const group = svg("g", {class: "kg-edge"});
    const route = [
      "M", fromX, fromY,
      "C", fromX + 22 * direction, fromY, lead - 20 * direction, midY, lead, midY,
      "H", tail,
      "C", tail + 20 * direction, midY, toX - 22 * direction, toY, toX, toY,
    ].join(" ");
    group.append(svg("path", {d: route}));
    group.append(svg("rect", {x: midX - labelWidth / 2, y: midY - 14, width: labelWidth, height: 28, rx: 14}));
    const label = svg("text", {x: midX, y: midY});
    label.textContent = caption;
    group.append(label);
    links.append(group);
    edges.push([edge, group]);
  }

  const cards = new Map();
  scene.replaceChildren(links);
  for (const node of data.nodes) {
    const card = element("button", "kg-node");
    card.type = "button";
    card.setAttribute("aria-expanded", "false");
    const {x, y} = coordinates.get(node.id);
    card.style.left = x + "px";
    card.style.top = y + "px";
    card.style.setProperty("--kind-color", node.color);
    card.append(element("span", "kg-kind", node.kind), element("span", "kg-name", node.name));
    if (node.summary) card.append(element("span", "kg-summary", node.summary));
    listen(card, "pointerenter", event => {
      if (event.pointerType !== "touch") showPaper(card, node);
    });
    listen(card, "pointerleave", scheduleClose);
    listen(card, "focus", () => showPaper(card, node));
    listen(card, "blur", scheduleClose);
    listen(card, "click", () => {
      selected = node.id;
      refreshSelection();
      showPaper(card, node);
      setTriggerValue("node_pick", {id: node.id, name: node.name});
    });
    cards.set(node.id, card);
    scene.append(card);
  }

  function refreshSelection() {
    for (const [id, card] of cards) card.setAttribute("aria-pressed", String(id === selected));
    for (const [edge, group] of edges) {
      group.classList.toggle("is-active", edge.source === selected || edge.target === selected);
    }
    shell.graphView = {signature, selected, zoom};
  }

  hidePaper();
  applyZoom(zoom);
  viewport.scrollTo(graphChanged ? 0 : oldLeft, graphChanged ? 0 : oldTop);
  if (changedSelection && coordinates.has(selected)) {
    const {x, y} = coordinates.get(selected);
    const left = (x + CARD_WIDTH / 2) * zoom - viewport.clientWidth / 2;
    const top = (y + CARD_HEIGHT / 2) * zoom - viewport.clientHeight / 2;
    viewport.scrollTo(left, top);
  }
  refreshSelection();

  listen(paper, "pointerenter", () => clearTimeout(closeTimer));
  listen(paper, "pointerleave", scheduleClose);
  listen(paper, "focusin", () => clearTimeout(closeTimer));
  listen(paper, "focusout", event => { if (!paper.contains(event.relatedTarget)) scheduleClose(); });
  listen(shell, "keydown", event => { if (event.key === "Escape") hidePaper(); });
  listen(viewport, "scroll", hidePaper);
  for (const button of shell.querySelectorAll("[data-zoom]")) {
    listen(button, "click", () => {
      if (button.dataset.zoom === "fit") {
        applyZoom(Math.max(0.35, Math.min(1, viewport.clientWidth / width, viewport.clientHeight / height)));
        hidePaper();
        viewport.scrollTo(0, 0);
      } else {
        changeZoom(zoom * Number(button.dataset.zoom), viewport.clientWidth / 2, viewport.clientHeight / 2);
      }
    });
  }
  listen(viewport, "wheel", event => {
    if (!event.ctrlKey && !event.metaKey) return;
    event.preventDefault();
    const bounds = viewport.getBoundingClientRect();
    changeZoom(zoom * (event.deltaY > 0 ? 0.9 : 1.1), event.clientX - bounds.left, event.clientY - bounds.top);
  }, {passive: false});
  listen(viewport, "pointerdown", event => {
    if (event.button !== 0 || event.pointerType === "touch" || event.target.closest("button")) return;
    pan = {x: event.clientX, y: event.clientY, left: viewport.scrollLeft, top: viewport.scrollTop};
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("is-panning");
  });
  listen(viewport, "pointermove", event => {
    if (pan) viewport.scrollTo(pan.left + pan.x - event.clientX, pan.top + pan.y - event.clientY);
  });
  listen(viewport, "lostpointercapture", () => {
    pan = null;
    viewport.classList.remove("is-panning");
  });
  return () => {
    events.abort();
    clearTimeout(closeTimer);
    viewport.classList.remove("is-panning");
  };
}
