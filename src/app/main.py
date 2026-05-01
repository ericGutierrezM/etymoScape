import json
from pathlib import Path

import streamlit as st
import pandas as pd

DATA_PATH = Path("data/prototype/sugar.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    word_data = json.load(f)

st.set_page_config(page_title="EtymoScape — Sugar", layout="wide")

st.title(word_data["title"])
st.caption(f"Language: {word_data['language']}")

st.write(word_data["short_summary"])

st.subheader("Etymology chain")

forms_by_id = {form["id"]: form for form in word_data["forms"]}

# Reverse the chain so oldest appears first
chain = list(reversed(word_data["forms"]))

for i, form in enumerate(chain):
    st.markdown(
        f"**{form['lemma']}** — {form['language']}  \n"
        f"*{form.get('period', '')}*  \n"
        f"{form.get('meaning', '')}"
    )
    if i < len(chain) - 1:
        st.markdown("↓")

st.subheader("Timeline")

timeline_df = pd.DataFrame([
    {
        "Form": form["lemma"],
        "Language": form["language"],
        "Period": form.get("period"),
        "Start": form.get("approx_start_year"),
        "End": form.get("approx_end_year"),
        "Meaning": form.get("meaning"),
    }
    for form in word_data["forms"]
]).sort_values("Start")

st.dataframe(timeline_df, use_container_width=True)

st.subheader("Map route")

map_df = pd.DataFrame([
    {
        "lat": point["lat"],
        "lon": point["lon"],
        "label": point["label"]
    }
    for point in word_data["map_route"]
])

st.map(map_df[["lat", "lon"]])

st.subheader("Edges")

edge_df = pd.DataFrame(word_data["edges"])
st.dataframe(edge_df, use_container_width=True)

st.subheader("Semantic stages")

semantic_df = pd.DataFrame(word_data["semantic_stages"])
st.dataframe(semantic_df, use_container_width=True)

st.subheader("Sources")

for source in word_data["sources"]:
    st.markdown(f"- [{source['name']}]({source['url']})")