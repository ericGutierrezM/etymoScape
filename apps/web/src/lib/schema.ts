export type ConfidenceLabel = "low" | "medium" | "high" | string;

export type WordSummary = {
  slug: string;
  title: string;
  language: string;
  status?: string;
};

export type LexicalInfo = {
  part_of_speech?: string;
  noun_type?: string;
  verb_type?: string;
  adjective_type?: string;
  plural?: string;
  forms?: string;
  inflection?: string;
  pronunciation?: string | string[];
  pronunciations?: string | string[];
  main_definition?: string;
  usage_note?: string;
};

export type RawEtymology = {
  text?: string;
  source?: string;
  source_url?: string;
  url?: string;
  templates?: unknown[];
};

export type WordForm = {
  id: string;
  lemma: string;
  language: string;
  period?: string;
  approx_start_year?: number | null;
  approx_end_year?: number | null;
  region_label?: string;
  lat?: number | string | null;
  lon?: number | string | null;
  meaning?: string;
};

export type WordEdge = {
  from: string;
  to: string;
  relation: string;
  confidence?: ConfidenceLabel;
  note?: string;
};

export type RoutePoint = {
  label: string;
  lat: number | string;
  lon: number | string;
  approx_year?: number | null;
  region_label?: string;
  language?: string;
  period?: string;
  meaning?: string;
};

export type SemanticStage = {
  label: string;
  meaning?: string;
  language?: string;
  period?: string;
  approx_year?: number | null;
};

export type Source = {
  name: string;
  url?: string;
  type?: string;
  via?: string;
  retrieval_date?: string;
};

export type RelatedWord = {
  lemma?: string;
  language?: string;
  relationship?: string;
};

export type WordEntry = {
  id: string;
  query_word: string;
  language: string;
  title: string;
  story_type?: string;
  lexical_info?: LexicalInfo;
  raw_etymology?: RawEtymology;
  forms: WordForm[];
  edges: WordEdge[];
  map_route: RoutePoint[];
  semantic_stages: SemanticStage[];
  sources: Source[];
  short_summary?: string;
  confidence_summary?: string;
  status?: string;
  historical_context?: string;
  related_words?: RelatedWord[];
};
