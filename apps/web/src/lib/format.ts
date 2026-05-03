import type { RoutePoint, WordForm } from "./schema";

export function formatYear(year: number | string | null | undefined): string {
  if (year === null || year === undefined || year === "") {
    return "-";
  }

  const numericYear = Number(year);

  if (!Number.isFinite(numericYear)) {
    return String(year);
  }

  if (numericYear < 0) {
    return `${Math.abs(Math.round(numericYear))} BCE`;
  }

  return `${Math.round(numericYear)} CE`;
}

export function sortFormsByYear(forms: WordForm[]): WordForm[] {
  return [...forms].sort((a, b) => {
    const aYear = a.approx_start_year ?? Number.POSITIVE_INFINITY;
    const bYear = b.approx_start_year ?? Number.POSITIVE_INFINITY;
    return aYear - bYear;
  });
}

export function getEarliestForm(forms: WordForm[]): WordForm | undefined {
  return sortFormsByYear(forms)[0];
}

export function getLatestForm(forms: WordForm[]): WordForm | undefined {
  const sortedForms = sortFormsByYear(forms);
  return sortedForms[sortedForms.length - 1];
}

export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const earthRadiusKm = 6371;
  const dLat = degreesToRadians(lat2 - lat1);
  const dLon = degreesToRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(degreesToRadians(lat1)) *
      Math.cos(degreesToRadians(lat2)) *
      Math.sin(dLon / 2) ** 2;

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function getTotalDistanceKm(route: RoutePoint[]): number {
  if (route.length < 2) {
    return 0;
  }

  return route.slice(1).reduce((total, point, index) => {
    const previous = route[index];
    const lat1 = Number(previous.lat);
    const lon1 = Number(previous.lon);
    const lat2 = Number(point.lat);
    const lon2 = Number(point.lon);

    if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) {
      return total;
    }

    return total + haversineKm(lat1, lon1, lat2, lon2);
  }, 0);
}

function degreesToRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}
