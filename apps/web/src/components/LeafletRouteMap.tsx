"use client";

import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, Tooltip } from "react-leaflet";

import { formatYear } from "@/lib/format";
import type { RoutePoint } from "@/lib/schema";

type LeafletRouteMapProps = {
  route: RoutePoint[];
  title: string;
};

type LatLngTuple = [number, number];

export default function LeafletRouteMap({ route, title }: LeafletRouteMapProps) {
  const points = route
    .map((point, index) => ({
      ...point,
      index,
      lat: Number(point.lat),
      lon: Number(point.lon),
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon));

  const positions = points.map((point) => [point.lat, point.lon] as LatLngTuple);
  const center = getMapCenter(positions);

  return (
    <MapContainer
      aria-label={`${title} route map`}
      center={center}
      className="leaflet-route-map"
      maxZoom={8}
      minZoom={2}
      scrollWheelZoom
      zoom={getInitialZoom(positions)}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {positions.length > 1 ? (
        <Polyline className="leaflet-route-line" positions={positions} />
      ) : null}

      {points.map((point, index) => (
        <CircleMarker
          center={[point.lat, point.lon]}
          className={index === points.length - 1 ? "leaflet-stage-dot final" : "leaflet-stage-dot"}
          key={`${point.label}-${index}`}
          pathOptions={{
            color: index === points.length - 1 ? "#171414" : "#cc3d2f",
            fillColor: index === points.length - 1 ? "#f2c94c" : "#ffffff",
            fillOpacity: 1,
            opacity: 1,
            weight: 3,
          }}
          radius={index === points.length - 1 ? 10 : 8}
        >
          <Tooltip direction="top" offset={[0, -8]} permanent>
            <span className="map-tooltip">
              {index + 1}. {point.label}
            </span>
          </Tooltip>
          <Popup>
            <div className="map-popup">
              <strong>
                {index + 1}. {point.label}
              </strong>
              {point.region_label ? <span>Region: {point.region_label}</span> : null}
              {point.approx_year ? <span>Approx. year: {formatYear(point.approx_year)}</span> : null}
              {point.meaning ? <span>Meaning: {point.meaning}</span> : null}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

function getMapCenter(positions: LatLngTuple[]): LatLngTuple {
  if (positions.length === 0) {
    return [25, 20];
  }

  const totals = positions.reduce(
    (acc, [lat, lon]) => ({
      lat: acc.lat + lat,
      lon: acc.lon + lon,
    }),
    { lat: 0, lon: 0 },
  );

  return [totals.lat / positions.length, totals.lon / positions.length];
}

function getInitialZoom(positions: LatLngTuple[]): number {
  if (positions.length < 2) {
    return 4;
  }

  const latitudes = positions.map(([lat]) => lat);
  const longitudes = positions.map(([, lon]) => lon);
  const latSpan = Math.max(...latitudes) - Math.min(...latitudes);
  const lonSpan = Math.max(...longitudes) - Math.min(...longitudes);
  const span = Math.max(latSpan, lonSpan);

  if (span > 90) {
    return 2;
  }

  if (span > 40) {
    return 3;
  }

  if (span > 18) {
    return 4;
  }

  return 5;
}
