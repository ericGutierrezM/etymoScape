import Link from "next/link";

import type { WordSummary } from "@/lib/schema";

import WordSearch from "./WordSearch";

type SiteHeaderProps = {
  words: WordSummary[];
  showSearch?: boolean;
};

export default function SiteHeader({ words, showSearch = false }: SiteHeaderProps) {
  return (
    <header className="site-header">
      <Link className="brand-link" href="/" aria-label="EtymoScape home">
        EtymoScape
      </Link>

      <div className="header-actions">
        {showSearch ? <WordSearch words={words} compact /> : null}
        <Link className="about-link" href="/about">
          About
        </Link>
      </div>
    </header>
  );
}
