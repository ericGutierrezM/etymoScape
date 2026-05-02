import json
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import folium_static


DATA_DIR = Path("data/final_data")


# -----------------------------
# Basic utilities
# -----------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_value(value, default="—"):
    if value is None or value == "":
        return default
    return value


def format_year(year):
    if year is None or year == "":
        return "—"

    try:
        year = int(year)
    except Exception:
        return str(year)

    if year < 0:
        return f"{abs(year)} BCE"
    return f"{year} CE"


def sort_forms_by_year(forms):
    return sorted(
        forms,
        key=lambda x: x.get("approx_start_year", 999999)
        if x.get("approx_start_year") is not None
        else 999999
    )


def sort_route_by_year_or_order(route):
    """
    Sort route by approx_year if available.
    If not available, preserve current order.
    """
    indexed_route = list(enumerate(route))

    return [
        point for _, point in sorted(
            indexed_route,
            key=lambda item: (
                item[1].get("approx_year") is None,
                item[1].get("approx_year", item[0]),
                item[0],
            )
        )
    ]


# -----------------------------
# Route enrichment
# -----------------------------

def normalize_text(text):
    return str(text or "").lower().strip()


def find_matching_form(route_point, forms):
    """
    Try to match a map route point to one of the forms.

    Current JSON does not include stage_id in map_route, so we infer it from
    the label. Example:
    route label: "Sanskrit śárkarā"
    form lemma:  "śárkarā"
    """
    label = normalize_text(route_point.get("label"))

    if not label:
        return None

    # 1. Match by exact lemma contained in route label.
    for form in forms:
        lemma = normalize_text(form.get("lemma"))
        if lemma and lemma in label:
            return form

    # 2. Match by language contained in route label.
    for form in forms:
        language = normalize_text(form.get("language"))
        if language and language in label:
            return form

    # 3. Match by coordinates if exactly equal or very close.
    route_lat = route_point.get("lat")
    route_lon = route_point.get("lon")

    if route_lat is not None and route_lon is not None:
        for form in forms:
            form_lat = form.get("lat")
            form_lon = form.get("lon")

            if form_lat is None or form_lon is None:
                continue

            try:
                if abs(float(route_lat) - float(form_lat)) < 0.01 and abs(float(route_lon) - float(form_lon)) < 0.01:
                    return form
            except Exception:
                pass

    return None


def enrich_map_route(word_data):
    """
    Add missing route fields from forms when possible.

    This lets the app show region and approximate year even if map_route only has:
    label, lat, lon.
    """
    route = word_data.get("map_route", [])
    forms = word_data.get("forms", [])

    enriched_route = []

    for point in route:
        enriched = dict(point)
        match = find_matching_form(point, forms)

        if match:
            enriched.setdefault("stage_id", match.get("id"))
            enriched.setdefault("region_label", match.get("region_label"))

            # Use midpoint-ish display year if possible.
            # Prefer approx_start_year because it gives route ordering.
            if "approx_year" not in enriched or enriched.get("approx_year") in [None, ""]:
                enriched["approx_year"] = match.get("approx_start_year")

            enriched.setdefault("language", match.get("language"))
            enriched.setdefault("period", match.get("period"))
            enriched.setdefault("meaning", match.get("meaning"))

        enriched_route.append(enriched)

    return enriched_route


# -----------------------------
# Automatic symbolic map markers
# -----------------------------

def get_auto_marker(point):
    """
    Assign a symbolic marker automatically.

    We avoid modern national flags because historical languages and word routes
    do not map cleanly to modern nation-states.
    """
    text = " ".join([
        str(point.get("label", "")),
        str(point.get("language", "")),
        str(point.get("region_label", "")),
    ]).lower()

    if "proto" in text:
        return "◇"
    if "sanskrit" in text or "india" in text:
        return "⚑"
    if "gandhari" in text or "gandhara" in text:
        return "◆"
    if "persian" in text or "persia" in text or "iran" in text:
        return "◆"
    if "arabic" in text or "arab" in text:
        return "✦"
    if "italian" in text or "italy" in text:
        return "◈"
    if "french" in text or "france" in text:
        return "⚜"
    if "english" in text or "england" in text:
        return "⚐"
    if "greek" in text or "greece" in text:
        return "✧"

    return "⚑"


# -----------------------------
# Distance utilities
# -----------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Approximate distance between two lat/lon points in kilometers."""
    earth_radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c


def build_travel_table(route):
    rows = []

    for i in range(1, len(route)):
        origin = route[i - 1]
        destination = route[i]

        distance = haversine_km(
            float(origin["lat"]),
            float(origin["lon"]),
            float(destination["lat"]),
            float(destination["lon"]),
        )

        rows.append({
            "Step": i,
            "From": safe_value(origin.get("label")),
            "To": safe_value(destination.get("label")),
            "Origin region": safe_value(origin.get("region_label")),
            "Destination region": safe_value(destination.get("region_label")),
            "Approx. transition year": format_year(destination.get("approx_year")),
            "Distance traveled": f"{round(distance):,} km",
        })

    return pd.DataFrame(rows)


def get_total_distance_km(route):
    if len(route) < 2:
        return 0

    total = 0

    for i in range(1, len(route)):
        origin = route[i - 1]
        destination = route[i]

        total += haversine_km(
            float(origin["lat"]),
            float(origin["lon"]),
            float(destination["lat"]),
            float(destination["lon"]),
        )

    return total


# -----------------------------
# Visual word timeline
# -----------------------------

def render_word_timeline(word_data):
    forms = word_data.get("forms", [])

    if not forms:
        st.info("No timeline data available.")
        return

    forms_sorted = sort_forms_by_year(forms)

    colors = [
        "#F8D66D",
        "#F4978E",
        "#E78AC3",
        "#8ECAE6",
        "#B7E4C7",
        "#CDB4DB",
        "#FFD6A5",
        "#A0C4FF",
    ]

    html = """
    <div style="overflow-x: auto; padding: 18px 0 28px 0; font-family: sans-serif;">
        <div style="display: flex; align-items: stretch; min-width: 760px;">
    """

    for i, form in enumerate(forms_sorted):
        lemma = safe_value(form.get("lemma"), "")
        language = safe_value(form.get("language"))
        start_year = form.get("approx_start_year")
        year_label = format_year(start_year)

        color = colors[i % len(colors)]

        html += f"""
        <div style="
            flex: 1;
            min-width: 135px;
            margin-right: 6px;
            position: relative;
        ">
            <div style="
                background: {color};
                color: #111;
                border-radius: 15px;
                padding: 14px 12px;
                text-align: center;
                font-weight: 800;
                font-size: 18px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.22);
                white-space: nowrap;
            ">
                {lemma}
            </div>
            <div style="
                text-align: center;
                margin-top: 8px;
                font-size: 13px;
                color: #888;
                white-space: nowrap;
            ">
                ~{year_label}
            </div>
            <div style="
                text-align: center;
                font-size: 12px;
                color: #777;
                white-space: nowrap;
            ">
                {language}
            </div>
        </div>
        """

        if i < len(forms_sorted) - 1:
            html += """
            <div style="
                width: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #999;
                font-size: 24px;
                font-weight: bold;
                padding-bottom: 36px;
            ">
                →
            </div>
            """

    html += """
        </div>
    </div>
    """

    components.html(html, height=190, scrolling=True)


# -----------------------------
# Map
# -----------------------------

def draw_route_map(route, stage_index):
    """Draw route up to the selected stage with symbolic stage flags."""
    if not route:
        st.info("No map route available.")
        return

    avg_lat = sum(float(p["lat"]) for p in route) / len(route)
    avg_lon = sum(float(p["lon"]) for p in route) / len(route)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=3,
        tiles="CartoDB positron",
    )

    visible_route = route[:stage_index + 1]
    coordinates = []

    for i, point in enumerate(visible_route):
        lat = float(point["lat"])
        lon = float(point["lon"])
        label = safe_value(point.get("label"), f"Stage {i + 1}")
        marker_symbol = point.get("flag") or get_auto_marker(point)

        region = safe_value(point.get("region_label"))
        year = format_year(point.get("approx_year"))

        coordinates.append([lat, lon])

        popup_html = f"""
        <b>{i + 1}. {label}</b><br>
        Region: {region}<br>
        Approx. year: {year}
        """

        folium.Marker(
            location=[lat, lon],
            tooltip=f"{i + 1}. {label}",
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    transform: translate(-10px, -24px);
                    font-size: 24px;
                    font-weight: bold;
                    color: #111;
                    text-shadow: 0px 1px 4px rgba(255,255,255,0.95);
                ">
                    <span>{marker_symbol}</span>
                    <span style="
                        background: white;
                        border: 1px solid #555;
                        border-radius: 10px;
                        padding: 1px 6px;
                        font-size: 11px;
                        line-height: 16px;
                    ">
                        {i + 1}
                    </span>
                </div>
                """
            ),
        ).add_to(m)

    if len(coordinates) > 1:
        folium.PolyLine(
            coordinates,
            weight=4,
            opacity=0.85,
            tooltip="Approximate transmission route",
        ).add_to(m)

    all_coordinates = [[float(p["lat"]), float(p["lon"])] for p in route]

    if len(all_coordinates) > 1:
        m.fit_bounds(all_coordinates, padding=(30, 30))

    folium_static(m, width=900, height=500)


# -----------------------------
# Lexical summary
# -----------------------------

def render_lexical_info(word_data):
    lex = word_data.get("lexical_info", {})

    if not lex:
        return

    st.subheader("Word summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Part of speech**  \n{safe_value(lex.get('part_of_speech'))}")

    with col2:
        word_type = (
            lex.get("noun_type")
            or lex.get("verb_type")
            or lex.get("adjective_type")
        )
        st.markdown(f"**Type**  \n{safe_value(word_type)}")

    with col3:
        forms = (
            lex.get("plural")
            or lex.get("forms")
            or lex.get("inflection")
        )
        st.markdown(f"**Plural / forms**  \n{safe_value(forms)}")

    pronunciation = lex.get("pronunciation") or lex.get("pronunciations")

    if isinstance(pronunciation, list):
        pronunciation = ", ".join(pronunciation)

    if pronunciation:
        st.markdown(f"**Pronunciation:** {pronunciation}")

    if lex.get("main_definition"):
        st.markdown(f"**Meaning:** {lex['main_definition']}")

    if lex.get("usage_note"):
        st.markdown(f"**Usage note:** {lex['usage_note']}")

    st.divider()


# -----------------------------
# Raw etymology
# -----------------------------

def render_raw_etymology(word_data):
    raw = word_data.get("raw_etymology", {})

    if not raw:
        return

    st.subheader("Raw etymology")

    source = raw.get("source")
    source_url = raw.get("source_url") or raw.get("url")

    if source:
        if source_url:
            st.markdown(f"**Source:** [{source}]({source_url})")
        else:
            st.markdown(f"**Source:** {source}")

    text = raw.get("text")

    if text:
        with st.expander("Show raw etymology text"):
            st.text(text)


# -----------------------------
# App setup
# -----------------------------

st.set_page_config(page_title="EtymoScape Prototype", layout="wide")

st.sidebar.title("EtymoScape")

word_files = sorted(DATA_DIR.glob("*.json"))

if not word_files:
    st.error("No JSON files found in data/curated/")
    st.stop()

word_options = {path.stem: path for path in word_files}

selected_word = st.sidebar.selectbox(
    "Search a word",
    options=list(word_options.keys()),
    placeholder="Type a word...",
    key="word_selector",
)

selected_file = word_options[selected_word]
word_data = load_json(selected_file)


# -----------------------------
# Header
# -----------------------------

title = word_data.get("title", word_data.get("query_word", selected_file.stem))
language = word_data.get("language", "Unknown language")
status = word_data.get("status", "draft")
story_type = word_data.get("story_type")

st.title(title)

caption_parts = [language, f"status: {status}"]

if story_type:
    caption_parts.append(f"story type: {story_type}")

st.caption(" · ".join(caption_parts))

if status != "published":
    st.warning("Draft entry — not fully validated yet.")

if word_data.get("short_summary"):
    st.write(word_data["short_summary"])

if word_data.get("confidence_summary"):
    with st.expander("Confidence summary"):
        st.write(word_data["confidence_summary"])


# -----------------------------
# Tabs
# -----------------------------

tab_overview, tab_map, tab_data = st.tabs(["Overview", "Map", "Raw data"])


# -----------------------------
# Overview tab
# -----------------------------

with tab_overview:
    render_lexical_info(word_data)

    st.subheader("Word evolution timeline")
    render_word_timeline(word_data)

    st.subheader("Etymology chain")

    forms = word_data.get("forms", [])
    forms_sorted = sort_forms_by_year(forms)

    for i, form in enumerate(forms_sorted):
        lemma = safe_value(form.get("lemma"), "")

        st.markdown(
            f"**{lemma}** — {safe_value(form.get('language'))}  \n"
            f"*{safe_value(form.get('period'))}*  \n"
            f"{safe_value(form.get('meaning'))}"
        )

        if i < len(forms_sorted) - 1:
            st.markdown("↓")

    st.subheader("Detailed timeline table")

    if forms:
        timeline_df = pd.DataFrame([
            {
                "Form": safe_value(f.get("lemma")),
                "Language": safe_value(f.get("language")),
                "Period": safe_value(f.get("period")),
                "Start": format_year(f.get("approx_start_year")),
                "End": format_year(f.get("approx_end_year")),
                "Region": safe_value(f.get("region_label")),
                "Meaning": safe_value(f.get("meaning")),
            }
            for f in forms
        ])

        st.dataframe(timeline_df, use_container_width=True, hide_index=True)

    st.subheader("Edges")

    edges = word_data.get("edges", [])

    if edges:
        edges_df = pd.DataFrame([
            {
                "From": safe_value(e.get("from")),
                "Relation": safe_value(e.get("relation")),
                "To": safe_value(e.get("to")),
                "Confidence": safe_value(e.get("confidence")),
                "Note": safe_value(e.get("note")),
            }
            for e in edges
        ])

        st.dataframe(edges_df, use_container_width=True, hide_index=True)
    else:
        st.info("No etymology edges available.")

    st.subheader("Semantic stages")

    semantic_stages = word_data.get("semantic_stages", [])

    if semantic_stages:
        semantic_df = pd.DataFrame([
            {
                "Stage": safe_value(s.get("label")),
                "Meaning": safe_value(s.get("meaning")),
                "Language": safe_value(s.get("language")),
                "Period": safe_value(s.get("period")),
                "Approx. year": format_year(s.get("approx_year")),
            }
            for s in semantic_stages
        ])

        st.dataframe(semantic_df, use_container_width=True, hide_index=True)
    else:
        st.info("No semantic stages yet.")

    if word_data.get("historical_context"):
        st.subheader("Historical context")
        st.write(word_data["historical_context"])

    related_words = word_data.get("related_words", [])

    if related_words:
        st.subheader("Related words")

        related_df = pd.DataFrame([
            {
                "Word": safe_value(r.get("lemma")),
                "Language": safe_value(r.get("language")),
                "Relationship": safe_value(r.get("relationship")),
            }
            for r in related_words
        ])

        st.dataframe(related_df, use_container_width=True, hide_index=True)

    render_raw_etymology(word_data)

    st.subheader("Sources")

    sources = word_data.get("sources", [])

    if sources:
        for source in sources:
            name = source.get("name", "Source")
            url = source.get("url")
            source_type = source.get("type")
            via = source.get("via")

            label = name

            if source_type:
                label += f" — {source_type}"

            if via:
                label += f" via {via}"

            if url:
                st.markdown(f"- [{label}]({url})")
            else:
                st.markdown(f"- {label}")
    else:
        st.info("No sources yet.")


# -----------------------------
# Map tab
# -----------------------------

with tab_map:
    st.subheader("Word route map")

    route = enrich_map_route(word_data)
    route = sort_route_by_year_or_order(route)

    if route:
        stage_index = st.slider(
            "Move through the word route",
            min_value=0,
            max_value=len(route) - 1,
            value=len(route) - 1,
            step=1,
            key=f"slider_{selected_word}",
        )

        draw_route_map(route, stage_index)

        current_stage = route[stage_index]

        st.markdown("### Current stage")
        st.markdown(f"**{stage_index + 1}. {safe_value(current_stage.get('label'))}**")

        st.markdown(f"**Region:** {safe_value(current_stage.get('region_label'))}")
        st.markdown(f"**Approx. year:** {format_year(current_stage.get('approx_year'))}")

        if current_stage.get("meaning"):
            st.markdown(f"**Meaning:** {safe_value(current_stage.get('meaning'))}")

        st.caption(
            "Map points are approximate cultural/geographic anchors, "
            "not exact birthplaces of the word."
        )

        if len(route) > 1:
            travel_df = build_travel_table(route)
            total_distance = get_total_distance_km(route)

            st.subheader("Travel summary")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Route stages", len(route))

            with col2:
                st.metric("Approx. total distance", f"{round(total_distance):,} km")

            st.subheader("Travel steps")
            st.dataframe(travel_df, use_container_width=True, hide_index=True)

    else:
        st.info("No map route available.")


# -----------------------------
# Raw data tab
# -----------------------------

with tab_data:
    st.subheader("Raw JSON")
    st.json(word_data)