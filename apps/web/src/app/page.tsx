import Link from "next/link";

import SiteHeader from "@/components/SiteHeader";
import WordSearch from "@/components/WordSearch";
import { getFeaturedWord, getWordSummaries } from "@/lib/words";

export default function HomePage() {
  const words = getWordSummaries();
  const featuredWord = getFeaturedWord();

  return (
    <main className="page-shell landing-shell">
      <SiteHeader words={words} />

      <section className="landing-hero" aria-labelledby="home-title">
        <p className="eyebrow">The way of words</p>
        <h1 id="home-title">Explore how words travel across cultures, maps, and meanings</h1>
        <WordSearch words={words} autoFocus />
        <p className="landing-copy">
          Trace how words move across languages, places, and meanings through
          maps, timelines, and source-backed etymology data.
        </p>
      </section>

      {featuredWord ? (
        <section className="featured-strip" aria-label="Available words">
          {words.map((word) => (
            <Link
              className="word-chip"
              href={`/word/${word.slug}`}
              key={word.slug}
            >
              <span>{word.title}</span>
              <small>{word.language}</small>
            </Link>
          ))}
        </section>
      ) : null}
    </main>
  );
}
