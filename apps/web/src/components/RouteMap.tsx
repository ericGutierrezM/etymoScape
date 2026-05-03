"use client";

import dynamic from "next/dynamic";

import { enrichMapRoute, sortRouteByYearOrOrder } from "@/lib/route";
import type { WordEntry } from "@/lib/schema";

const LeafletRouteMap = dynamic(() => import("./LeafletRouteMap"), {
  loading: () => (
    <div className="map-loading" aria-label="Loading map">
      Loading map
    </div>
  ),
  ssr: false,
});

type RouteMapProps = {
  word: WordEntry;
};

export default function RouteMap({ word }: RouteMapProps) {
  const route = sortRouteByYearOrOrder(enrichMapRoute(word));

  return (
    <section className="route-map-panel" aria-label={`${word.title} route map`}>
      <div className="map-frame">
        {route.length > 0 ? (
          <LeafletRouteMap route={route} title={word.title} />
        ) : (
          <div className="empty-state">No route points yet.</div>
        )}
      </div>
    </section>
  );
}
