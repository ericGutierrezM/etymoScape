import type { Metadata } from "next";
import { notFound } from "next/navigation";

import RouteMap from "@/components/RouteMap";
import SiteHeader from "@/components/SiteHeader";
import WordDetailsTabs from "@/components/WordDetailsTabs";
import WordFactsPanel from "@/components/WordFactsPanel";
import WordTimeline from "@/components/WordTimeline";
import { getWordBySlug, getWordSlugs, getWordSummaries } from "@/lib/words";

type WordPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export function generateStaticParams() {
  return getWordSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: WordPageProps): Promise<Metadata> {
  const { slug } = await params;
  const word = getWordBySlug(slug);

  if (!word) {
    return {
      title: "Word not found - EtymoScape",
    };
  }

  return {
    title: `${word.title} - EtymoScape`,
    description: word.short_summary,
  };
}

export default async function WordPage({ params }: WordPageProps) {
  const { slug } = await params;
  const word = getWordBySlug(slug);
  const words = getWordSummaries();

  if (!word) {
    notFound();
  }

  return (
    <main className="page-shell word-shell">
      <SiteHeader words={words} showSearch />

      <section className="word-hero" aria-labelledby="word-title">
        <RouteMap word={word} />
        <WordFactsPanel word={word} titleId="word-title" />
      </section>

      <WordTimeline forms={word.forms} />
      <WordDetailsTabs word={word} />
    </main>
  );
}
