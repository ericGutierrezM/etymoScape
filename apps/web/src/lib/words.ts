import fs from "node:fs";
import path from "node:path";

import type { WordEntry, WordSummary } from "./schema";

const DATA_DIR = path.resolve(process.cwd(), "../../data/final_data");
const FINAL_FILE_PATTERN = /^([a-z0-9-]+)_final\.json$/i;
const SAFE_SLUG_PATTERN = /^[a-z0-9-]+$/i;

export function getWordSlugs(): string[] {
  if (!fs.existsSync(DATA_DIR)) {
    return [];
  }

  return fs
    .readdirSync(DATA_DIR)
    .map((fileName) => fileName.match(FINAL_FILE_PATTERN)?.[1])
    .filter((slug): slug is string => Boolean(slug))
    .sort((a, b) => a.localeCompare(b));
}

export function getWordBySlug(slug: string): WordEntry | null {
  const normalizedSlug = normalizeSlug(slug);

  if (!normalizedSlug || !getWordSlugs().includes(normalizedSlug)) {
    return null;
  }

  const filePath = path.resolve(DATA_DIR, `${normalizedSlug}_final.json`);

  if (!filePath.startsWith(DATA_DIR)) {
    return null;
  }

  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as WordEntry;
}

export function getWordSummaries(): WordSummary[] {
  return getWordSlugs()
    .map((slug) => {
      const word = getWordBySlug(slug);

      if (!word) {
        return null;
      }

      return {
        word,
        slug,
      };
    })
    .filter((entry): entry is { word: WordEntry; slug: string } => Boolean(entry))
    .map(({ word, slug }) => ({
      slug,
      title: word.title || word.query_word,
      language: word.language,
      status: word.status,
    }));
}

export function getFeaturedWord(): WordEntry | null {
  return getWordBySlug("sugar") ?? getWordBySlug(getWordSlugs()[0] ?? "");
}

export function normalizeSlug(value: string): string {
  const slug = value.trim().toLowerCase().replace(/\s+/g, "-");
  return SAFE_SLUG_PATTERN.test(slug) ? slug : "";
}
