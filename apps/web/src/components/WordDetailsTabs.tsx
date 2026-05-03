"use client";

import { useState } from "react";

import { formatYear, getTotalDistanceKm, sortFormsByYear } from "@/lib/format";
import { buildTravelSteps, enrichMapRoute, sortRouteByYearOrOrder } from "@/lib/route";
import type { WordEntry } from "@/lib/schema";

type WordDetailsTabsProps = {
  word: WordEntry;
};

type TableRow = Record<string, string | number>;
type TabId =
  | "overview"
  | "timeline"
  | "travel"
  | "edges"
  | "semantic-stages"
  | "sources"
  | "raw-data";

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "timeline", label: "Timeline" },
  { id: "travel", label: "Travel" },
  { id: "edges", label: "Edges" },
  { id: "semantic-stages", label: "Semantic stages" },
  { id: "sources", label: "Sources" },
  { id: "raw-data", label: "Raw data" },
];

export default function WordDetailsTabs({ word }: WordDetailsTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  return (
    <section className="details-section" id="word-details" aria-labelledby="details-title">
      <div className="section-heading">
        <p className="eyebrow">Deep dive</p>
        <h2 id="details-title">Word details</h2>
      </div>

      <div className="tab-list" role="tablist" aria-label={`${word.title} details`}>
        {TABS.map((tab) => (
          <button
            aria-controls={`panel-${tab.id}`}
            aria-selected={activeTab === tab.id}
            className={activeTab === tab.id ? "tab-button active" : "tab-button"}
            id={`tab-${tab.id}`}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div
        aria-labelledby={`tab-${activeTab}`}
        className="tab-panel"
        id={`panel-${activeTab}`}
        role="tabpanel"
      >
        {activeTab === "overview" ? <OverviewPanel word={word} /> : null}
        {activeTab === "timeline" ? <TimelinePanel word={word} /> : null}
        {activeTab === "travel" ? <TravelPanel word={word} /> : null}
        {activeTab === "edges" ? <EdgesPanel word={word} /> : null}
        {activeTab === "semantic-stages" ? <SemanticStagesPanel word={word} /> : null}
        {activeTab === "sources" ? <SourcesPanel word={word} /> : null}
        {activeTab === "raw-data" ? <RawDataPanel word={word} /> : null}
      </div>
    </section>
  );
}

function OverviewPanel({ word }: WordDetailsTabsProps) {
  const lex = word.lexical_info;
  const forms = sortFormsByYear(word.forms);
  const pronunciation = Array.isArray(lex?.pronunciation)
    ? lex.pronunciation.join(", ")
    : lex?.pronunciation ?? (Array.isArray(lex?.pronunciations) ? lex.pronunciations.join(", ") : lex?.pronunciations);
  const wordType = lex?.noun_type ?? lex?.verb_type ?? lex?.adjective_type;
  const wordForms = lex?.plural ?? lex?.forms ?? lex?.inflection;

  return (
    <div className="prose-panel">
      {word.confidence_summary ? (
        <p className="confidence-copy">{word.confidence_summary}</p>
      ) : null}

      {lex ? (
        <section className="panel-section" aria-labelledby="word-summary-heading">
          <h3 id="word-summary-heading">Word summary</h3>
          <div className="summary-grid">
            <InfoTile label="Part of speech" value={lex.part_of_speech} />
            <InfoTile label="Type" value={wordType} />
            <InfoTile label="Plural / forms" value={wordForms} />
            <InfoTile label="Pronunciation" value={pronunciation} />
          </div>
        </section>
      ) : null}

      {lex?.main_definition ? (
        <div className="text-block">
          <h3>Meaning</h3>
          <p>{lex.main_definition}</p>
        </div>
      ) : null}

      {lex?.usage_note ? (
        <div className="text-block">
          <h3>Usage note</h3>
          <p>{lex.usage_note}</p>
        </div>
      ) : null}

      {forms.length > 0 ? (
        <section className="panel-section" aria-labelledby="etymology-chain-heading">
          <h3 id="etymology-chain-heading">Etymology chain</h3>
          <ol className="chain-list">
            {forms.map((form) => (
              <li key={form.id}>
                <strong>{form.lemma}</strong>
                <span>{form.language}</span>
                <em>{form.period ?? "-"}</em>
                <p>{form.meaning ?? "-"}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {word.raw_etymology?.text ? (
        <section className="panel-section" aria-labelledby="raw-etymology-heading">
          <h3 id="raw-etymology-heading">Raw etymology</h3>
          <RawEtymologySource word={word} />
          <details className="raw-text-details">
            <summary>Show raw etymology text</summary>
            <p>{word.raw_etymology.text}</p>
          </details>
        </section>
      ) : null}

      {word.historical_context ? (
        <div className="text-block">
          <h3>Historical context</h3>
          <p>{word.historical_context}</p>
        </div>
      ) : null}

      {word.related_words && word.related_words.length > 0 ? (
        <div className="text-block">
          <h3>Related words</h3>
          <DataTable
            columns={["Word", "Language", "Relationship"]}
            rows={word.related_words.map((related) => ({
              Word: related.lemma ?? "-",
              Language: related.language ?? "-",
              Relationship: related.relationship ?? "-",
            }))}
          />
        </div>
      ) : null}
    </div>
  );
}

function TimelinePanel({ word }: WordDetailsTabsProps) {
  const forms = sortFormsByYear(word.forms);

  if (forms.length === 0) {
    return <p>No timeline data available.</p>;
  }

  return (
    <section className="panel-section" aria-labelledby="timeline-table-heading">
      <h3 id="timeline-table-heading">Detailed timeline table</h3>
      <DataTable
        columns={["Form", "Language", "Period", "Start", "End", "Region", "Meaning"]}
        rows={forms.map((form) => ({
          Form: form.lemma,
          Language: form.language,
          Period: form.period ?? "-",
          Start: formatYear(form.approx_start_year),
          End: formatYear(form.approx_end_year),
          Region: form.region_label ?? "-",
          Meaning: form.meaning ?? "-",
        }))}
      />
    </section>
  );
}

function TravelPanel({ word }: WordDetailsTabsProps) {
  const route = sortRouteByYearOrOrder(enrichMapRoute(word));
  const travelSteps = buildTravelSteps(route);

  if (route.length === 0) {
    return <p>No map route available.</p>;
  }

  return (
    <div className="route-data-panel">
      <section className="panel-section" aria-labelledby="travel-summary-heading">
        <h3 id="travel-summary-heading">Travel summary</h3>
        <div className="summary-grid compact-summary">
          <InfoTile label="Route stages" value={route.length.toLocaleString()} />
          <InfoTile
            label="Approx. total distance"
            value={`${Math.round(getTotalDistanceKm(route)).toLocaleString()} km`}
          />
        </div>
        <p className="caption-copy">
          Map points are approximate cultural/geographic anchors, not exact
          birthplaces of the word.
        </p>
      </section>

      <section className="panel-section" aria-labelledby="route-points-heading">
        <h3 id="route-points-heading">Route points</h3>
        <DataTable
          columns={["Stage", "Label", "Region", "Approx. year", "Language", "Period", "Meaning"]}
          rows={route.map((point, index) => ({
            Stage: index + 1,
            Label: point.label,
            Region: point.region_label ?? "-",
            "Approx. year": formatYear(point.approx_year),
            Language: point.language ?? "-",
            Period: point.period ?? "-",
            Meaning: point.meaning ?? "-",
          }))}
        />
      </section>

      <section className="panel-section" aria-labelledby="travel-steps-heading">
        <h3 id="travel-steps-heading">Travel steps</h3>
        <DataTable
          columns={[
            "Step",
            "From",
            "To",
            "Origin region",
            "Destination region",
            "Approx. transition year",
            "Distance traveled",
          ]}
          rows={travelSteps.map((step) => ({
            Step: step.step,
            From: step.from,
            To: step.to,
            "Origin region": step.originRegion,
            "Destination region": step.destinationRegion,
            "Approx. transition year": step.transitionYear,
            "Distance traveled": step.distance,
          }))}
        />
      </section>
    </div>
  );
}

function EdgesPanel({ word }: WordDetailsTabsProps) {
  if (word.edges.length === 0) {
    return <p>No etymology edges available.</p>;
  }

  return (
    <section className="panel-section" aria-labelledby="edges-heading">
      <h3 id="edges-heading">Edges</h3>
      <DataTable
        columns={["From", "Relation", "To", "Confidence", "Note"]}
        rows={word.edges.map((edge) => ({
          From: edge.from,
          Relation: edge.relation.replace(/_/g, " "),
          To: edge.to,
          Confidence: edge.confidence ?? "-",
          Note: edge.note ?? "",
        }))}
      />
    </section>
  );
}

function SemanticStagesPanel({ word }: WordDetailsTabsProps) {
  if (word.semantic_stages.length === 0) {
    return <p>No semantic stages yet.</p>;
  }

  return (
    <section className="panel-section" aria-labelledby="semantic-stages-heading">
      <h3 id="semantic-stages-heading">Semantic stages</h3>
      <DataTable
        columns={["Stage", "Meaning", "Language", "Period", "Approx. year"]}
        rows={word.semantic_stages.map((stage) => ({
          Stage: stage.label,
          Meaning: stage.meaning ?? "-",
          Language: stage.language ?? "-",
          Period: stage.period ?? "-",
          "Approx. year": formatYear(stage.approx_year),
        }))}
      />
    </section>
  );
}

function SourcesPanel({ word }: WordDetailsTabsProps) {
  if (word.sources.length === 0) {
    return <p>No sources yet.</p>;
  }

  return (
    <section className="panel-section" aria-labelledby="sources-heading">
      <h3 id="sources-heading">Sources</h3>
      <ul className="source-list">
        {word.sources.map((source) => (
          <li key={`${source.name}-${source.url}`}>
            {source.url ? (
              <a href={source.url} rel="noreferrer" target="_blank">
                {source.name}
              </a>
            ) : (
              <span>{source.name}</span>
            )}
            <small>
              {[source.type, source.via ? `via ${source.via}` : null, source.retrieval_date]
                .filter(Boolean)
                .join(" - ")}
            </small>
          </li>
        ))}
      </ul>
    </section>
  );
}

function RawDataPanel({ word }: WordDetailsTabsProps) {
  return (
    <section className="panel-section" aria-labelledby="raw-json-heading">
      <h3 id="raw-json-heading">Raw JSON</h3>
      <pre className="json-panel">
        <code>{JSON.stringify(word, null, 2)}</code>
      </pre>
    </section>
  );
}

function DataTable({ columns, rows }: { columns: string[]; rows: TableRow[] }) {
  if (rows.length === 0) {
    return <p>No rows available.</p>;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>{row[column] || "-"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="info-tile">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

function RawEtymologySource({ word }: WordDetailsTabsProps) {
  const raw = word.raw_etymology;

  if (!raw?.source) {
    return null;
  }

  const sourceUrl = raw.source_url ?? raw.url;

  return (
    <p className="source-inline">
      <strong>Source:</strong>{" "}
      {sourceUrl ? (
        <a href={sourceUrl} rel="noreferrer" target="_blank">
          {raw.source}
        </a>
      ) : (
        raw.source
      )}
    </p>
  );
}
