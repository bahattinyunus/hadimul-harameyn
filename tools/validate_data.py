#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hadimul-harameyn: Veri Doğrulama ve Bütünlük Denetim Motoru
------------------------------------------------------------
Bu script; data/ altındaki tüm JSON, GeoJSON ve CSV dosyalarını
schemas/ altındaki şemalar, coğrafi sınırlar, tarih formatları
ve çapraz referanslar açısından denetler.
"""

import sys
import os
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Windows konsolunda UTF-8 çıktıyı garanti altına al
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ANSI Renk Kodları (Terminal çıktısı için)
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class DataValidator:
    def __init__(self, root_dir: Optional[Path] = None, verbose: bool = False):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent
        self.schemas_dir = self.root_dir / "schemas"
        self.data_dir = self.root_dir / "data"
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: int = 0
        self.schemas: Dict[str, dict] = {}
        self.loaded_campaign_ids: set = set()

    def log_success(self, msg: str):
        self.passed_checks += 1
        if self.verbose:
            print(f"  {Colors.GREEN}✓ [GEÇTİ]{Colors.ENDC} {msg}")

    def log_error(self, msg: str):
        self.errors.append(msg)
        print(f"  {Colors.FAIL}✗ [HATA]{Colors.ENDC} {msg}")

    def log_warning(self, msg: str):
        self.warnings.append(msg)
        print(f"  {Colors.WARNING}⚠ [UYARI]{Colors.ENDC} {msg}")

    def load_schemas(self):
        """schemas/ altındaki JSON şemalarını önbelleğe alır."""
        if not self.schemas_dir.exists():
            self.log_error(f"Şema dizini bulunamadı: {self.schemas_dir}")
            return

        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    self.schemas[schema_file.name] = json.load(f)
                self.log_success(f"Şema yüklendi: {schema_file.name}")
            except Exception as e:
                self.log_error(f"Şema yüklenirken hata oluştu ({schema_file.name}): {e}")

    def validate_json_schema(self, data: dict, schema_name: str, file_name: str) -> bool:
        """JSON verisini ilgili JSON Schema ile denetler."""
        if not HAS_JSONSCHEMA:
            self.log_warning("jsonschema kütüphanesi kurulu değil, derin şema doğrulaması atlandı.")
            return True

        if schema_name not in self.schemas:
            self.log_error(f"{file_name} için eşleşen şema bulunamadı: {schema_name}")
            return False

        schema = self.schemas[schema_name]
        try:
            jsonschema.validate(instance=data, schema=schema)
            self.log_success(f"{file_name} -> {schema_name} şema doğrulaması başarılı.")
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.log_error(f"{file_name} şema hatası: {e.message} (Yol: {'/'.join(str(p) for p in e.path)})")
            return False

    def validate_campaigns(self):
        """data/campaigns/*.json dosyalarını denetler."""
        campaigns_dir = self.data_dir / "campaigns"
        if not campaigns_dir.exists():
            self.log_error("data/campaigns dizini mevcut değil!")
            return

        print(f"\n{Colors.BOLD}🔍 Sefer Verileri Denetleniyor (data/campaigns/)...{Colors.ENDC}")
        for json_path in sorted(campaigns_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Schema Doğrulama
                self.validate_json_schema(data, "campaign.schema.json", json_path.name)

                # Mantıksal Alan Kontrolleri
                cid = data.get("campaign_id")
                if not cid:
                    self.log_error(f"{json_path.name}: 'campaign_id' alanı eksik!")
                else:
                    self.loaded_campaign_ids.add(cid)

                coords = data.get("coordinates", {})
                lat = coords.get("latitude")
                lon = coords.get("longitude")
                if lat is None or lon is None:
                    self.log_error(f"{json_path.name}: Koordinat bilgisi eksik!")
                elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    self.log_error(f"{json_path.name}: Geçersiz koordinat aralığı: [{lat}, {lon}]")
                else:
                    self.log_success(f"{json_path.name}: Koordinatlar geçerli [{lat}, {lon}].")

                # Komutanlar kontrolü
                commanders = data.get("commanders", {})
                if not commanders.get("ottoman"):
                    self.log_error(f"{json_path.name}: Osmanlı komutanlar listesi boş!")
                else:
                    self.log_success(f"{json_path.name}: {len(commanders.get('ottoman', []))} Osmanlı komutanı kayıtlı.")

            except Exception as e:
                self.log_error(f"{json_path.name} okunamadı veya bozuk JSON: {e}")

    def validate_routes(self):
        """data/routes/*.geojson dosyalarını denetler."""
        routes_dir = self.data_dir / "routes"
        if not routes_dir.exists():
            self.log_error("data/routes dizini mevcut değil!")
            return

        print(f"\n{Colors.BOLD}🔍 Menzil ve GIS Rotaları Denetleniyor (data/routes/)...{Colors.ENDC}")
        for geojson_path in sorted(routes_dir.glob("*.geojson")):
            try:
                with open(geojson_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Şema doğrulaması
                self.validate_json_schema(data, "route-node.schema.json", geojson_path.name)

                # GeoJSON temel yapısı
                if data.get("type") != "FeatureCollection":
                    self.log_error(f"{geojson_path.name}: GeoJSON root 'FeatureCollection' olmalı!")
                    continue

                features = data.get("features", [])
                if not features:
                    self.log_error(f"{geojson_path.name}: Hiçbir menzil (Feature) içermiyor!")
                    continue

                seen_orders = set()
                seen_nodes = set()
                prev_date = None

                for idx, feat in enumerate(features):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})

                    node_id = props.get("node_id")
                    order = props.get("step_order")
                    name = props.get("name")
                    cid = props.get("campaign_id")
                    date_str = props.get("date_reached")

                    # Node ID ve Order benzersizlik kontrolü
                    if not node_id:
                        self.log_error(f"{geojson_path.name} [özellik #{idx}]: 'node_id' eksik!")
                    elif node_id in seen_nodes:
                        self.log_error(f"{geojson_path.name}: Tekrarlanan node_id: {node_id}")
                    else:
                        seen_nodes.add(node_id)

                    if order is None:
                        self.log_error(f"{geojson_path.name} ({node_id}): 'step_order' eksik!")
                    elif order in seen_orders:
                        self.log_error(f"{geojson_path.name}: Tekrarlanan step_order: {order}")
                    else:
                        seen_orders.add(order)

                    # Çapraz Sefer Referans Kontrolü
                    if cid and cid not in self.loaded_campaign_ids:
                        self.log_warning(f"{geojson_path.name} ({name}): Bilinmeyen campaign_id referansı: '{cid}'")

                    # Geometri ve Koordinat Kontrolleri (WGS84: [boylam, enlem])
                    if geom.get("type") != "Point":
                        self.log_error(f"{geojson_path.name} ({node_id}): Geometri tipi 'Point' olmalı!")
                    coords = geom.get("coordinates", [])
                    if len(coords) < 2:
                        self.log_error(f"{geojson_path.name} ({node_id}): Eksik koordinat!")
                    else:
                        lon, lat = coords[0], coords[1]
                        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                            self.log_error(f"{geojson_path.name} ({node_id}): Koordinatlar sınır dışı [boylam={lon}, enlem={lat}]")

                    # Kronolojik Tarih Kontrolü
                    if date_str:
                        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                            self.log_error(f"{geojson_path.name} ({node_id}): Geçersiz tarih formatı '{date_str}', YYYY-MM-DD bekleniyor.")

                self.log_success(f"{geojson_path.name}: Toplam {len(features)} menzil noktası ve geometrisi doğrulandı.")

            except Exception as e:
                self.log_error(f"{geojson_path.name} okunurken hata: {e}")

    def validate_timeline(self):
        """data/timeline/ altındaki CSV ve JSON dosyalarını denetler."""
        timeline_dir = self.data_dir / "timeline"
        if not timeline_dir.exists():
            self.log_error("data/timeline dizini bulunamadı!")
            return

        print(f"\n{Colors.BOLD}🔍 Kronoloji Verileri Denetleniyor (data/timeline/)...{Colors.ENDC}")

        # CSV Kontrolü
        csv_path = timeline_dir / "selim-i-chronology.csv"
        if csv_path.exists():
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    required_headers = {"date", "hijri_date", "event_type", "location", "title", "summary", "primary_source"}
                    if not required_headers.issubset(set(reader.fieldnames or [])):
                        self.log_error(f"{csv_path.name}: Eksik sütun başlıkları! Beklenen: {required_headers}")
                    else:
                        rows = list(reader)
                        self.log_success(f"{csv_path.name}: Sütun yapısı geçerli, {len(rows)} kayıt bulundu.")

                        # Tarih format ve kronoloji artış kontrolü
                        last_date = ""
                        for r_idx, row in enumerate(rows):
                            d = row["date"]
                            if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                                self.log_error(f"{csv_path.name} satır #{r_idx+2}: Geçersiz tarih '{d}'")
                            if last_date and d < last_date:
                                self.log_warning(f"{csv_path.name} satır #{r_idx+2}: Kronolojik sıra geriye gitti ({last_date} -> {d})")
                            last_date = d

            except Exception as e:
                self.log_error(f"{csv_path.name} okunurken hata: {e}")

        # JSON Kontrolü
        admin_json = timeline_dir / "administrative-events.json"
        if admin_json.exists():
            try:
                with open(admin_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.validate_json_schema(data, "timeline.schema.json", admin_json.name)
                events = data.get("events", [])
                self.log_success(f"{admin_json.name}: {len(events)} idari hadise kaydı doğrulandı.")
            except Exception as e:
                self.log_error(f"{admin_json.name} JSON okuma hatası: {e}")

    def validate_primary_sources(self):
        """data/primary-sources/ altındaki JSON dosyalarını denetler."""
        sources_dir = self.data_dir / "primary-sources"
        if not sources_dir.exists():
            self.log_error("data/primary-sources dizini bulunamadı!")
            return

        print(f"\n{Colors.BOLD}🔍 Birincil Kaynak Katalogları Denetleniyor (data/primary-sources/)...{Colors.ENDC}")
        for json_path in sorted(sources_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.validate_json_schema(data, "primary-sources.schema.json", json_path.name)
                sources = data.get("sources", [])
                self.log_success(f"{json_path.name}: {len(sources)} bibliyografik eser kaydı doğrulandı.")
            except Exception as e:
                self.log_error(f"{json_path.name} okuma hatası: {e}")

    def validate_quotes(self):
        """data/quotes/ altındaki alıntı ve tarihsel kelâm JSON dosyalarını denetler."""
        quotes_dir = self.data_dir / "quotes"
        if not quotes_dir.exists():
            self.log_error("data/quotes dizini bulunamadı!")
            return

        print(f"\n{Colors.BOLD}🔍 Birincil Kaynak Alıntıları ve Kelâm Külliyatı Denetleniyor (data/quotes/)...{Colors.ENDC}")
        for json_path in sorted(quotes_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.validate_json_schema(data, "quotes.schema.json", json_path.name)
                quotes = data.get("quotes", [])
                seen_qids = set()
                for q in quotes:
                    qid = q.get("quote_id")
                    if qid in seen_qids:
                        self.log_error(f"{json_path.name}: Tekrarlanan quote_id: {qid}")
                    else:
                        seen_qids.add(qid)
                self.log_success(f"{json_path.name}: Toplam {len(quotes)} tarihsel alıntı ve kaynak referansı doğrulandı.")
            except Exception as e:
                self.log_error(f"{json_path.name} okuma hatası: {e}")

    def run_all(self) -> bool:
        """Tüm doğrulama testlerini baştan sona çalıştırır."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}    hadimul-harameyn :: Veri Bütünlüğü Doğrulama Motoru{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}======================================================{Colors.ENDC}\n")

        self.load_schemas()
        self.validate_campaigns()
        self.validate_routes()
        self.validate_timeline()
        self.validate_primary_sources()
        self.validate_quotes()

        print(f"\n{Colors.BOLD}=================== DOĞRULAMA ÖZETİ ==================={Colors.ENDC}")
        print(f"Başarılı Denetimler: {Colors.GREEN}{self.passed_checks}{Colors.ENDC}")
        print(f"Uyarılar          : {Colors.WARNING}{len(self.warnings)}{Colors.ENDC}")
        print(f"Hatalar           : {Colors.FAIL if self.errors else Colors.GREEN}{len(self.errors)}{Colors.ENDC}")

        if self.errors:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ DOĞRULAMA BAŞARISIZ OLDU! ({len(self.errors)} hata tespit edildi.){Colors.ENDC}")
            for err in self.errors:
                print(f"  - {err}")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✨ TÜM VERİLER VE ŞEMALAR MÜKEMMEL BİÇİMDE DOĞRULANDI!{Colors.ENDC}\n")
            return True


if __name__ == "__main__":
    validator = DataValidator(verbose=True)
    success = validator.run_all()
    sys.exit(0 if success else 1)
