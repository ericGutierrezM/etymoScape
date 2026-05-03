"use client";

import { useId, useState, type FormEvent } from "react";
import { ArrowRight, Dices, Search } from "lucide-react";

import type { WordSummary } from "@/lib/schema";

type WordSearchProps = {
  words: WordSummary[];
  compact?: boolean;
  autoFocus?: boolean;
};

export default function WordSearch({
  words,
  compact = false,
  autoFocus = false,
}: WordSearchProps) {
  const [query, setQuery] = useState("");
  const listId = useId();

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    openQuery(query, words);
  }

  function openRandomWord() {
    if (words.length === 0) {
      return;
    }

    const randomWord = words[Math.floor(Math.random() * words.length)];
    window.location.assign(`/word/${randomWord.slug}`);
  }

  return (
    <form
      className={compact ? "word-search compact" : "word-search"}
      onSubmit={submitSearch}
      role="search"
    >
      <label className="visually-hidden" htmlFor={`${listId}-input`}>
        Search a word
      </label>
      <div className="search-input-wrap">
        <Search aria-hidden="true" size={compact ? 17 : 24} />
        <input
          autoFocus={autoFocus}
          id={`${listId}-input`}
          list={`${listId}-options`}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="ex: sugar"
          type="search"
          value={query}
        />
        <button
          aria-label="Search"
          className="search-submit-button"
          onClick={() => openQuery(query, words)}
          title="Search"
          type="button"
        >
          <ArrowRight aria-hidden="true" size={compact ? 17 : 22} />
        </button>
      </div>
      <datalist id={`${listId}-options`}>
        {words.map((word) => (
          <option key={word.slug} value={word.title} />
        ))}
      </datalist>
      <button
        aria-label="Open a random word"
        className="icon-button"
        onClick={openRandomWord}
        title="Open a random word"
        type="button"
      >
        <Dices aria-hidden="true" size={compact ? 18 : 26} />
      </button>
    </form>
  );
}

function getSlugForQuery(query: string, words: WordSummary[]): string {
  const normalized = query.trim().toLowerCase().replace(/\s+/g, "-");

  if (!normalized) {
    return "";
  }

  const exactMatch = words.find(
    (word) =>
      word.slug === normalized || word.title.trim().toLowerCase() === query.trim().toLowerCase(),
  );

  return exactMatch?.slug ?? normalized;
}

function openQuery(query: string, words: WordSummary[]) {
  const slug = getSlugForQuery(query, words);

  if (!slug) {
    return;
  }

  window.location.assign(`/word/${slug}`);
}
