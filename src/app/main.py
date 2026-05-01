import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


DATA_DIR = Path("data/prototype")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def draw_route_map(route, stage_index):
    avg_lat = sum(p["lat"] for p in route) / len(route)
    avg_lon = sum(p["lon"] for p in route) / len(route)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=3,
        tiles="CartoDB positron"
    )

    visible_route = route[:stage_index + 1]
    coordinates = []

    for i, point in enumerate(visible_route):
        lat = point["lat"]
        lon = point["lon"]
        label = point.get("label", f"Stage {i + 1}")

        coordinates.append([lat, lon])

        folium.Marker(
            location=[lat, lon],
            tooltip=f"{i + 1}. {label}",
            popup=label
        ).add_to(m)

    if len(coordinates) > 1:
        folium.PolyLine(
            coordinates,
            weight=4,
            opacity=0.8
        ).add_to(m)

    st_folium(m, width=900, height=500)


# -----------------------------
# App
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
)

selected_file = word_options[selected_word]

word_data = load_json(selected_file)

# -----------------------------
# Header
# -----------------------------

title = word_data.get("title", word_data.get("query_word", selected_file.stem))
language = word_data.get("language", "Unknown language")
status = word_data.get("status", "draft")

st.title(title)
st.caption(f"{language} · status: {status}")

if status != "published":
    st.warning("Draft entry — not fully validated yet.")

st.write(word_data.get("short_summary", ""))

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
    st.subheader("Etymology chain")

    forms = word_data.get("forms", [])

    forms_sorted = sorted(
        forms,
        key=lambda x: x.get("approx_start_year", 999999)
    )

    for i, form in enumerate(forms_sorted):
        lemma = form.get("lemma", "")
        transliteration = form.get("transliteration")

        if transliteration:
            lemma = f"{lemma} / {transliteration}"

        st.markdown(
            f"**{lemma}** — {form.get('language', '')}  \n"
            f"*{form.get('period', '')}*  \n"
            f"{form.get('meaning', '')}"
        )

        if i < len(forms_sorted) - 1:
            st.markdown("↓")

    st.subheader("Timeline")

    if forms:
        timeline_df = pd.DataFrame([
            {
                "Form": f.get("lemma"),
                "Language": f.get("language"),
                "Period": f.get("period"),
                "Start": f.get("approx_start_year"),
                "End": f.get("approx_end_year"),
                "Meaning": f.get("meaning"),
            }
            for f in forms
        ]).sort_values("Start")

        st.dataframe(timeline_df, use_container_width=True)

    st.subheader("Semantic stages")

    semantic_stages = word_data.get("semantic_stages", [])

    if semantic_stages:
        st.dataframe(pd.DataFrame(semantic_stages), use_container_width=True)
    else:
        st.info("No semantic stages yet.")

    st.subheader("Sources")

    sources = word_data.get("sources", [])

    if sources:
        for source in sources:
            name = source.get("name", "Source")
            url = source.get("url")
            if url:
                st.markdown(f"- [{name}]({url})")
            else:
                st.markdown(f"- {name}")
    else:
        st.info("No sources yet.")


# -----------------------------
# Map tab
# -----------------------------

with tab_map:
    st.subheader("Word route map")

    route = word_data.get("map_route", [])

    if route:
        stage_index = st.slider(
            "Move through the word route",
            min_value=0,
            max_value=len(route) - 1,
            value=len(route) - 1,
            step=1
        )

        draw_route_map(route, stage_index)

        current_stage = route[stage_index]

        st.markdown("### Current stage")
        st.markdown(f"**{stage_index + 1}. {current_stage.get('label', '')}**")

        st.caption(
            "Map points are approximate cultural/geographic anchors, "
            "not exact birthplaces of the word."
        )

        st.dataframe(pd.DataFrame(route), use_container_width=True)

    else:
        st.info("No map route available.")


# -----------------------------
# Raw data tab
# -----------------------------

with tab_data:
    st.subheader("Raw JSON")
    st.json(word_data)