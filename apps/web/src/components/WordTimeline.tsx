import type { CSSProperties } from "react";

import { formatYear, sortFormsByYear } from "@/lib/format";
import type { WordForm } from "@/lib/schema";

type WordTimelineProps = {
  forms: WordForm[];
};

const STAGE_COLORS = [
  "#f2c94c",
  "#ef8a78",
  "#d968b4",
  "#72c6d6",
  "#7ac88d",
  "#9c80d7",
  "#f0a35e",
  "#5b9bd5",
];

export default function WordTimeline({ forms }: WordTimelineProps) {
  const sortedForms = sortFormsByYear(forms);

  if (sortedForms.length === 0) {
    return null;
  }

  return (
    <section className="timeline-section" aria-labelledby="timeline-title">
      <h2 id="timeline-title">Word evolution timeline</h2>
      <ol className="word-timeline">
        {sortedForms.map((form, index) => (
          <li
            className="timeline-stage"
            key={`${form.id}-${index}`}
            style={{
              "--stage-color": STAGE_COLORS[index % STAGE_COLORS.length],
            } as CSSProperties}
          >
            <div className="stage-block">
              <strong>{form.lemma}</strong>
              <span>{form.language}</span>
            </div>
            <time>{formatYear(form.approx_start_year)}</time>
          </li>
        ))}
      </ol>
    </section>
  );
}
