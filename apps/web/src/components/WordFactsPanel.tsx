import { Info, MapPinned, Milestone } from "lucide-react";

import { formatYear, getEarliestForm, getLatestForm, getTotalDistanceKm } from "@/lib/format";
import { enrichMapRoute, sortRouteByYearOrOrder } from "@/lib/route";
import type { WordEntry } from "@/lib/schema";

type WordFactsPanelProps = {
  word: WordEntry;
  titleId: string;
};

export default function WordFactsPanel({ word, titleId }: WordFactsPanelProps) {
  const earliestForm = getEarliestForm(word.forms);
  const latestForm = getLatestForm(word.forms);
  const route = sortRouteByYearOrOrder(enrichMapRoute(word));
  const distanceKm = Math.round(getTotalDistanceKm(route));

  return (
    <aside className="word-facts-panel" aria-labelledby={titleId}>
      <p className="status-line">{word.status ?? "draft"}</p>
      <h1 id={titleId}>{word.title}</h1>
      <p className="word-language">
        {word.language}
        {word.story_type ? <span>story type: {word.story_type}</span> : null}
      </p>

      {word.status !== "published" ? (
        <p className="draft-warning">Draft entry - not fully validated yet.</p>
      ) : null}

      {word.short_summary ? (
        <p className="word-summary">{word.short_summary}</p>
      ) : null}

      <dl className="fact-list">
        <div>
          <dt>
            <Milestone aria-hidden="true" size={18} />
            Earliest form
          </dt>
          <dd>
            <strong>{earliestForm?.lemma ?? "-"}</strong>
            <span>{formatYear(earliestForm?.approx_start_year)}</span>
          </dd>
        </div>
        <div>
          <dt>
            <MapPinned aria-hidden="true" size={18} />
            Route distance
          </dt>
          <dd>
            <strong>{distanceKm.toLocaleString()} km</strong>
            <span>{route.length} map stages</span>
          </dd>
        </div>
        <div>
          <dt>
            <Info aria-hidden="true" size={18} />
            Current form
          </dt>
          <dd>
            <strong>{latestForm?.lemma ?? word.title}</strong>
            <span>{latestForm?.period ?? "Modern usage"}</span>
          </dd>
        </div>
      </dl>

      <a className="primary-link" href="#word-details">
        More info
      </a>
    </aside>
  );
}
