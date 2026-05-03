import SiteHeader from "@/components/SiteHeader";
import { getWordSummaries } from "@/lib/words";

export default function AboutPage() {
  const words = getWordSummaries();

  return (
    <main className="page-shell text-page">
      <SiteHeader words={words} showSearch />
      <section className="about-copy" aria-labelledby="about-title">
        <p className="eyebrow">About</p>
        <h1 id="about-title">EtymoScape turns word histories into routes.</h1>
        <p>
          The current prototype starts from Wiktionary data extracted through
          Kaikki, then enriches each word into a structured story with forms,
          relationships, map points, semantic stages, and review status.
        </p>
        <p>
          This web UI is the production-facing layer. The Python pipeline and
          Streamlit prototype remain in place while the polished interface grows
          beside them.
        </p>
      </section>
    </main>
  );
}
