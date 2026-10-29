#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hadimul-harameyn: Askerî Sefer ve Lojistik Analiz Motoru
-----------------------------------------------------------
Bu araç; data/routes/ altındaki GeoJSON menzil verilerini ve
data/campaigns/ altındaki sefer kayıtlarını analiz ederek
mesafe (km/fersah), irtifa profili, konaklama süreleri ve
akademik kaynak kapsama istatistiklerini hesaplar.
"""

import sys
import os
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Windows konsolunda UTF-8 çıktıyı garanti altına al
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def haversine(c1: List[float], c2: List[float]) -> float:
    """İki [boylam, enlem] koordinatı arasındaki küresel mesafeyi (km) hesaplar."""
    lon1, lat1 = c1[0], c1[1]
    lon2, lat2 = c2[0], c2[1]
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


class CampaignAnalyzer:
    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent
        self.routes_dir = self.root_dir / "data" / "routes"
        self.campaigns_dir = self.root_dir / "data" / "campaigns"
        self.quotes_file = self.root_dir / "data" / "quotes" / "historical-quotes.json"
        self.sources_dir = self.root_dir / "data" / "primary-sources"

    def analyze_route(self, geojson_path: Path) -> Dict[str, Any]:
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        if not features:
            return {}

        total_distance = 0.0
        elevations = []
        stays = []
        terrains = set()

        for i in range(len(features)):
            props = features[i]["properties"]
            elev = props.get("elevation_meters")
            if elev is not None:
                elevations.append(elev)
            stay = props.get("stay_duration_days")
            if stay is not None:
                stays.append(stay)
            terrain = props.get("terrain_type")
            if terrain:
                terrains.add(terrain)

            if i < len(features) - 1:
                c1 = features[i]["geometry"]["coordinates"]
                c2 = features[i + 1]["geometry"]["coordinates"]
                total_distance += haversine(c1, c2)

        return {
            "name": data.get("name", geojson_path.stem),
            "file": geojson_path.name,
            "node_count": len(features),
            "total_distance_km": round(total_distance, 2),
            "total_distance_fersah": round(total_distance / 5.6, 1),  # 1 Osmanlı fersahı ~ 5.6 km
            "min_elevation_m": min(elevations) if elevations else None,
            "max_elevation_m": max(elevations) if elevations else None,
            "avg_elevation_m": round(sum(elevations) / len(elevations), 1) if elevations else None,
            "total_recorded_stay_days": sum(stays) if stays else 0,
            "avg_stay_days": round(sum(stays) / len(stays), 1) if stays else 0,
            "terrains": sorted(list(terrains))
        }

    def analyze_all_routes(self) -> List[Dict[str, Any]]:
        results = []
        for p in sorted(self.routes_dir.glob("*.geojson")):
            res = self.analyze_route(p)
            if res:
                results.append(res)
        return results

    def get_summary_metrics(self) -> Dict[str, Any]:
        route_stats = self.analyze_all_routes()
        total_km = sum(r["total_distance_km"] for r in route_stats)
        total_nodes = sum(r["node_count"] for r in route_stats)

        campaigns_count = len(list(self.campaigns_dir.glob("*.json")))

        quotes_count = 0
        if self.quotes_file.exists():
            with open(self.quotes_file, "r", encoding="utf-8") as f:
                q_data = json.load(f)
                quotes_count = len(q_data.get("quotes", []))

        sources_count = 0
        for s_file in self.sources_dir.glob("*.json"):
            with open(s_file, "r", encoding="utf-8") as f:
                s_data = json.load(f)
                sources_count += len(s_data.get("sources", []))

        return {
            "total_campaign_routes": len(route_stats),
            "total_georeferenced_menzils": total_nodes,
            "total_linear_distance_km": round(total_km, 2),
            "total_linear_distance_fersah": round(total_km / 5.6, 1),
            "registered_campaigns": campaigns_count,
            "verified_primary_quotes": quotes_count,
            "primary_source_works": sources_count,
            "routes": route_stats
        }

    def print_text_report(self):
        metrics = self.get_summary_metrics()

        print("\n" + "=" * 70)
        print("    hadimul-harameyn :: Askerî Sefer & Menzil Lojistik Raporu")
        print("=" * 70)
        print(f"  Toplam Doğrulanmış Menzil (WGS84): {metrics['total_georeferenced_menzils']}")
        print(f"  Toplam Karasal Güzergâh Mesafesi : {metrics['total_linear_distance_km']} km ({metrics['total_linear_distance_fersah']} fersah)")
        print(f"  Kayıtlı Meydan Muharebeleri       : {metrics['registered_campaigns']}")
        print(f"  Birincil Tarihsel Kelâm & Alıntı  : {metrics['verified_primary_quotes']}")
        print(f"  Vakayinâme & Arşiv Kaynakları     : {metrics['primary_source_works']}")
        print("-" * 70)

        print("\n📍 SEFER GÜZERGÂHLARI DETAY ANALİZİ:")
        print(f"{'Sefer / Rota':<32} | {'Menzil':<6} | {'Mesafe (km)':<12} | {'Ort. İrtifa':<11} | {'Konaklama'}")
        print("-" * 75)
        for r in metrics["routes"]:
            avg_el = f"{r['avg_elevation_m']} m" if r['avg_elevation_m'] is not None else "N/A"
            stay = f"{r['total_recorded_stay_days']} gün"
            print(f"{r['name']:<32} | {r['node_count']:<6} | {r['total_distance_km']:<12} | {avg_el:<11} | {stay}")

        print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="hadimul-harameyn Lojistik Analiz Motoru")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Rapor formatı")
    args = parser.parse_args()

    analyzer = CampaignAnalyzer()
    if args.format == "json":
        print(json.dumps(analyzer.get_summary_metrics(), ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        metrics = analyzer.get_summary_metrics()
        print(f"# Sefer Analiz Raporu\n")
        print(f"- **Menzil:** {metrics['total_georeferenced_menzils']}")
        print(f"- **Toplam Mesafe:** {metrics['total_linear_distance_km']} km\n")
        print("| Rota | Menzil | Mesafe (km) | Ort. İrtifa |")
        print("| :--- | :---: | :---: | :---: |")
        for r in metrics["routes"]:
            print(f"| {r['name']} | {r['node_count']} | {r['total_distance_km']} km | {r['avg_elevation_m']} m |")
    else:
        analyzer.print_text_report()


if __name__ == "__main__":
    main()
