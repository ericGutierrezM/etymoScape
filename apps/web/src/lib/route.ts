import { formatYear, haversineKm } from "./format";
import type { RoutePoint, WordEntry, WordForm } from "./schema";

export type EnrichedRoutePoint = RoutePoint & {
  approx_year?: number | null;
  language?: string;
  period?: string;
  region_label?: string;
  meaning?: string;
  stage_id?: string;
};

export type TravelStep = {
  step: number;
  from: string;
  to: string;
  originRegion: string;
  destinationRegion: string;
  transitionYear: string;
  distance: string;
};

export function enrichMapRoute(word: WordEntry): EnrichedRoutePoint[] {
  return word.map_route.map((point) => {
    const match = findMatchingForm(point, word.forms);

    if (!match) {
      return point;
    }

    return {
      ...point,
      stage_id: match.id,
      approx_year: point.approx_year ?? match.approx_start_year,
      language: point.language ?? match.language,
      period: point.period ?? match.period,
      region_label: point.region_label ?? match.region_label,
      meaning: point.meaning ?? match.meaning,
    };
  });
}

export function sortRouteByYearOrOrder(route: EnrichedRoutePoint[]): EnrichedRoutePoint[] {
  return route
    .map((point, index) => ({ point, index }))
    .sort((a, b) => {
      const aYear = a.point.approx_year;
      const bYear = b.point.approx_year;

      if (aYear === null || aYear === undefined) {
        return bYear === null || bYear === undefined ? a.index - b.index : 1;
      }

      if (bYear === null || bYear === undefined) {
        return -1;
      }

      return aYear - bYear || a.index - b.index;
    })
    .map(({ point }) => point);
}

export function buildTravelSteps(route: EnrichedRoutePoint[]): TravelStep[] {
  return route.slice(1).flatMap((destination, index) => {
    const origin = route[index];
    const lat1 = Number(origin.lat);
    const lon1 = Number(origin.lon);
    const lat2 = Number(destination.lat);
    const lon2 = Number(destination.lon);

    if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) {
      return [];
    }

    const distanceKm = Math.round(haversineKm(lat1, lon1, lat2, lon2));

    return [
      {
        step: index + 1,
        from: safeValue(origin.label),
        to: safeValue(destination.label),
        originRegion: safeValue(origin.region_label),
        destinationRegion: safeValue(destination.region_label),
        transitionYear: formatYear(destination.approx_year),
        distance: `${distanceKm.toLocaleString()} km`,
      },
    ];
  });
}

function findMatchingForm(routePoint: RoutePoint, forms: WordForm[]): WordForm | null {
  const label = normalizeText(routePoint.label);

  if (!label) {
    return null;
  }

  for (const form of forms) {
    const lemma = normalizeText(form.lemma);

    if (lemma && label.includes(lemma)) {
      return form;
    }
  }

  for (const form of forms) {
    const language = normalizeText(form.language);

    if (language && label.includes(language)) {
      return form;
    }
  }

  const routeLat = Number(routePoint.lat);
  const routeLon = Number(routePoint.lon);

  if (!Number.isFinite(routeLat) || !Number.isFinite(routeLon)) {
    return null;
  }

  for (const form of forms) {
    const formLat = Number(form.lat);
    const formLon = Number(form.lon);

    if (!Number.isFinite(formLat) || !Number.isFinite(formLon)) {
      continue;
    }

    if (Math.abs(routeLat - formLat) < 0.01 && Math.abs(routeLon - formLon) < 0.01) {
      return form;
    }
  }

  return null;
}

function normalizeText(text: unknown): string {
  return String(text ?? "").toLowerCase().trim();
}

function safeValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value);
}
