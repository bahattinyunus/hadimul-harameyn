#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hadimul-harameyn: Tarihsel Külliyat Hızlı Arama Motoru
---------------------------------------------------------
Depodaki tüm birincil kaynak alıntıları, menziller, sefer kayıtları,
kronoloji hadiseleri ve bibliyografik eserler arasında anahtar
kelime araması yapar ve renkli terminal çıktısı üretir.

Kullanım:
    python tools/search_corpus.py "Sinan Paşa"
    python tools/search_corpus.py "Sina" --type routes
    python tools/search_corpus.py "Topkapı" --type all
"""

import sys
import os
import json
import csv
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Windows konsolunda UTF-8 çıktıyı garanti altına al
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class TermColors:
    GOLD = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def highlight_match(text: str, query: str) -> str:
    """Metin içindeki eşleşen kelimeleri renklendirir."""
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"{TermColors.BOLD}{TermColors.GOLD}{m.group(0)}{TermColors.RESET}", text)


class CorpusSearchEngine:
    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent
        self.data_dir = self.root_dir / "data"

    def search_quotes(self, query: str) -> List[Dict[str, Any]]:
        quotes_file = self.data_dir / "quotes" / "historical-quotes.json"
        results = []
        if not quotes_file.exists():
            return results

        with open(quotes_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        q_lower = query.lower()
        for q in data.get("quotes", []):
            searchable = " ".join([
                q.get("quote_id", ""),
                q.get("speaker", ""),
                q.get("speaker_title", ""),
                q.get("event_or_context", ""),
                q.get("original_text", ""),
                q.get("transcription", ""),
                q.get("modern_turkish", ""),
                q.get("source_work", ""),
                q.get("author", "")
            ]).lower()

            if q_lower in searchable:
                results.append(q)
        return results

    def search_routes(self, query: str) -> List[Dict[str, Any]]:
        results = []
        routes_dir = self.data_dir / "routes"
        if not routes_dir.exists():
            return results

        q_lower = query.lower()
        for g_file in routes_dir.glob("*.geojson"):
            with open(g_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                searchable = " ".join([
                    props.get("node_id", ""),
                    props.get("name", ""),
                    props.get("historical_name", ""),
                    props.get("logistics_note", ""),
                    props.get("terrain_type", ""),
                    props.get("primary_source_ref", "")
                ]).lower()
                if q_lower in searchable:
                    results.append({
                        "file": g_file.name,
                        "campaign_name": data.get("name", ""),
                        "node": props,
                        "coordinates": feat.get("geometry", {}).get("coordinates", [])
                    })
        return results

    def search_campaigns(self, query: str) -> List[Dict[str, Any]]:
        results = []
        camp_dir = self.data_dir / "campaigns"
        if not camp_dir.exists():
            return results

        q_lower = query.lower()
        for c_file in camp_dir.glob("*.json"):
            with open(c_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_text = json.dumps(data, ensure_ascii=False).lower()
            if q_lower in raw_text:
                results.append({
                    "file": c_file.name,
                    "campaign_id": data.get("campaign_id", ""),
                    "title": data.get("title", ""),
                    "date": data.get("date", ""),
                    "region": data.get("region", "")
                })
        return results

    def search_timeline(self, query: str) -> List[Dict[str, Any]]:
        results = []
        csv_file = self.data_dir / "timeline" / "selim-i-chronology.csv"
        if csv_file.exists():
            q_lower = query.lower()
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    searchable = " ".join(str(v) for v in row.values() if v is not None).lower()
                    if q_lower in searchable:
                        results.append(row)
        return results

    def run_search(self, query: str, search_type: str = "all") -> Dict[str, Any]:
        out = {}
        if search_type in ("all", "quotes"):
            out["quotes"] = self.search_quotes(query)
        if search_type in ("all", "routes"):
            out["routes"] = self.search_routes(query)
        if search_type in ("all", "campaigns"):
            out["campaigns"] = self.search_campaigns(query)
        if search_type in ("all", "timeline"):
            out["timeline"] = self.search_timeline(query)
        return out


def main():
    parser = argparse.ArgumentParser(description="hadimul-harameyn Külliyat Arama Motoru")
    parser.add_argument("query", type=str, help="Aranacak terim (ör: 'Sinan Paşa', 'Tih', 'topçu')")
    parser.add_argument("--type", choices=["all", "quotes", "routes", "campaigns", "timeline"], default="all", help="Arama kapsamı")
    args = parser.parse_args()

    engine = CorpusSearchEngine()
    results = engine.run_search(args.query, args.type)

    total_hits = sum(len(v) for v in results.values())
    print("\n" + "=" * 70)
    print(f"  🔍 Arama Sonuçları: '{args.query}' ({total_hits} Eşleşme)")
    print("=" * 70)

    if "quotes" in results and results["quotes"]:
        print(f"\n{TermColors.BOLD}{TermColors.CYAN}📜 BİRİNCİL KAYNAK ALINTILARI ({len(results['quotes'])} Eşleşme):{TermColors.RESET}")
        for q in results["quotes"]:
            spk = highlight_match(q.get("speaker", ""), args.query)
            ctx = highlight_match(q.get("event_or_context", ""), args.query)
            tr = highlight_match(f'"{q.get("modern_turkish", "")}"', args.query)
            ref = highlight_match(f'{q.get("source_work", "")} ({q.get("author", "")})', args.query)
            print(f"  • [{q.get('quote_id')}] {spk} — {ctx}")
            print(f"    {tr}")
            print(f"    {TermColors.DIM}Kaynak: {ref}{TermColors.RESET}\n")

    if "routes" in results and results["routes"]:
        print(f"\n{TermColors.BOLD}{TermColors.GREEN}🗺️ COĞRAFİ MENZİLLER ({len(results['routes'])} Eşleşme):{TermColors.RESET}")
        for r in results["routes"]:
            node = r["node"]
            coords = r["coordinates"]
            name = highlight_match(node.get("name", ""), args.query)
            hname = highlight_match(node.get("historical_name", ""), args.query)
            note = highlight_match(node.get("logistics_note", ""), args.query)
            print(f"  • [{node.get('node_id')}] {name} ({hname}) — {r['campaign_name']}")
            print(f"    Koordinat: {coords} | İrtifa: {node.get('elevation_meters')}m | Tarih: {node.get('date_reached')}")
            print(f"    Not: {note}\n")

    if "campaigns" in results and results["campaigns"]:
        print(f"\n{TermColors.BOLD}{TermColors.RED}⚔️ SEFER & MUHAREBE KAYITLARI ({len(results['campaigns'])} Eşleşme):{TermColors.RESET}")
        for c in results["campaigns"]:
            t = highlight_match(c["title"], args.query)
            reg = highlight_match(c["region"], args.query)
            print(f"  • [{c['campaign_id']}] {t} ({c['date']})")
            print(f"    Bölge: {reg} | Dosya: data/campaigns/{c['file']}\n")

    if "timeline" in results and results["timeline"]:
        print(f"\n{TermColors.BOLD}{TermColors.GOLD}📅 KRONOLOJİ HADİSELERİ ({len(results['timeline'])} Eşleşme):{TermColors.RESET}")
        for row in results["timeline"]:
            t = highlight_match(row.get("title", ""), args.query)
            s = highlight_match(row.get("summary", ""), args.query)
            print(f"  • {row.get('date')} ({row.get('hijri_date')}) — {t} [{row.get('location')}]")
            print(f"    {s}\n")

    if total_hits == 0:
        print(f"\n  Aranan '{args.query}' ifadesiyle eşleşen kayıt bulunamadı.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
