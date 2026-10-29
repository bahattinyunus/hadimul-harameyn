#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hadimul-harameyn: Coğrafi Menzil ve Sefer Haritası Üretim Motoru
----------------------------------------------------------------
data/routes/ altındaki GeoJSON menzil verilerini ve data/campaigns/
altındaki sefer detaylarını okuyarak yüksek çözünürlüklü, interaktif,
akademik Leaflet ve Folium haritaları üretir.

Kullanım:
    python tools/generate_route_map.py --campaign egypt-1517
    python tools/generate_route_map.py --campaign caldiran-1514
    python tools/generate_route_map.py --campaign all
"""

import sys
import os
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Windows konsolunda UTF-8 çıktıyı garanti altına al
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import folium
    from folium.plugins import AntPath
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False


def haversine_distance(coord1: List[float], coord2: List[float]) -> float:
    """İki [boylam, enlem] koordinatı arasındaki küresel mesafeyi (km) hesaplar."""
    lon1, lat1 = coord1[0], coord1[1]
    lon2, lat2 = coord2[0], coord2[1]
    R = 6371.0  # Dünya yarıçapı km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class RouteMapGenerator:
    def __init__(self, root_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent
        self.routes_dir = self.root_dir / "data" / "routes"
        self.campaigns_dir = self.root_dir / "data" / "campaigns"
        self.output_dir = output_dir or (self.root_dir / "build")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_geojson(self, filename: str) -> dict:
        filepath = self.routes_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"GeoJSON dosyası bulunamadı: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_campaign(self, filename: str) -> dict:
        filepath = self.campaigns_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_interactive_html(self, campaign_key: str) -> Path:
        """Kendi kendine yeten, modern ve tarihsel temalı zengin bir Leaflet haritası üretir."""
        if campaign_key in ("caldiran", "caldiran-1514", "1514"):
            geojson_file = "caldiran-expedition.geojson"
            campaign_file = "1514-caldiran.json"
            out_filename = "caldiran-campaign-map.html"
            theme_color = "#c0392b"  # Kırmızı/Yakut Safevî-Osmanlı
            title = "Çaldıran Seferi ve Tebriz Menzil Güzergâhı (1514)"
        elif campaign_key in ("turnadagi", "turnadagi-1515", "1515"):
            geojson_file = "turnadagi-expedition.geojson"
            campaign_file = "1515-turnadagi.json"
            out_filename = "turnadagi-campaign-map.html"
            theme_color = "#e67e22"  # Turuncu Dulkadir & Anadolu
            title = "Turnadağı Seferi ve Dulkadir İntikali (1515)"
        elif campaign_key in ("kochisir", "kochisir-1516", "1516"):
            geojson_file = "kochisir-expedition.geojson"
            campaign_file = "1516-kochisir.json"
            out_filename = "kochisir-campaign-map.html"
            theme_color = "#2980b9"  # Mavi Cezire & Fırat/Dicle
            title = "Koçhisar Seferi ve Mardin/Cezire İntikali (1516)"
        else:
            geojson_file = "egypt-conquest.geojson"
            campaign_file = "1517-ridaniye.json"
            out_filename = "egypt-campaign-map.html"
            theme_color = "#d4af37"  # Hilafet ve Mısır Altını
            title = "Mısır ve Suriye Seferi Menzil Güzergâhı (1516-1517)"

        geojson_data = self.load_geojson(geojson_file)
        campaign_data = self.load_campaign(campaign_file)

        features = geojson_data.get("features", [])
        total_distance = 0.0
        for i in range(len(features) - 1):
            c1 = features[i]["geometry"]["coordinates"]
            c2 = features[i + 1]["geometry"]["coordinates"]
            total_distance += haversine_distance(c1, c2)

        # JSON verisini güvenli biçimde HTML içine göm
        raw_geojson_json = json.dumps(geojson_data, ensure_ascii=False)
        raw_campaign_json = json.dumps(campaign_data, ensure_ascii=False)

        html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | hadimul-harameyn</title>
  
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  
  <!-- Google Fonts: Cinzel & Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  <style>
    :root {{
      --primary-gold: #d4af37;
      --secondary-gold: #aa8c2c;
      --bg-dark: #0f141c;
      --panel-bg: rgba(18, 24, 34, 0.94);
      --card-bg: #1a2230;
      --border-color: #2c384d;
      --text-main: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: {theme_color};
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}

    /* Header */
    header {{
      background: linear-gradient(180deg, #161e2b 0%, #0d121a 100%);
      border-bottom: 2px solid var(--primary-gold);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 1000;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}

    .logo-section {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .monogram {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: radial-gradient(circle, #2d3748 0%, #1a202c 100%);
      border: 2px solid var(--primary-gold);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Cinzel', serif;
      font-weight: 900;
      color: var(--primary-gold);
      font-size: 1.2rem;
      box-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    }}

    .title-group h1 {{
      font-family: 'Cinzel', serif;
      font-size: 1.25rem;
      letter-spacing: 0.05em;
      color: #fff;
    }}

    .title-group p {{
      font-size: 0.8rem;
      color: var(--primary-gold);
    }}

    .stats-bar {{
      display: flex;
      gap: 20px;
    }}

    .stat-badge {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 6px 14px;
      font-size: 0.82rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}

    .stat-badge .stat-value {{
      font-weight: 700;
      color: var(--primary-gold);
      font-size: 0.95rem;
    }}

    .stat-badge .stat-label {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}

    /* Main Container */
    #main-wrapper {{
      display: flex;
      flex: 1;
      height: calc(100vh - 68px);
      position: relative;
    }}

    #map {{
      flex: 1;
      height: 100%;
      background: #090d13;
    }}

    /* Sidebar Panel */
    #sidebar {{
      width: 380px;
      background: var(--panel-bg);
      border-left: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      backdrop-filter: blur(8px);
      z-index: 999;
      box-shadow: -4px 0 25px rgba(0,0,0,0.4);
      transition: transform 0.3s ease;
    }}

    .sidebar-header {{
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-color);
      background: rgba(0,0,0,0.2);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .sidebar-header h2 {{
      font-family: 'Cinzel', serif;
      font-size: 1rem;
      color: var(--primary-gold);
    }}

    .timeline-controls {{
      padding: 12px 20px;
      background: #141b26;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      gap: 10px;
      align-items: center;
    }}

    .btn {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 7px 16px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .btn:hover {{
      opacity: 0.9;
      transform: translateY(-1px);
    }}

    .btn-secondary {{
      background: #2a374a;
      color: #e2e8f0;
    }}

    .menzil-list {{
      flex: 1;
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .menzil-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 12px 14px;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
    }}

    .menzil-card:hover, .menzil-card.active {{
      border-color: var(--primary-gold);
      background: #212c3d;
      transform: translateX(4px);
    }}

    .menzil-card.active::before {{
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background: var(--primary-gold);
      border-top-left-radius: 6px;
      border-bottom-left-radius: 6px;
    }}

    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}

    .card-order {{
      font-size: 0.7rem;
      background: rgba(212, 175, 55, 0.15);
      color: var(--primary-gold);
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 700;
    }}

    .card-date {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    .card-title {{
      font-size: 0.95rem;
      font-weight: 600;
      color: #fff;
      margin-bottom: 2px;
    }}

    .card-historical {{
      font-size: 0.8rem;
      color: var(--primary-gold);
      font-style: italic;
      margin-bottom: 8px;
    }}

    .card-excerpt {{
      font-size: 0.78rem;
      color: #cbd5e1;
      line-height: 1.4;
    }}

    /* Selected Details Modal/Overlay */
    #detail-overlay {{
      display: none;
      position: absolute;
      bottom: 24px;
      left: 24px;
      width: 440px;
      max-width: calc(100vw - 48px);
      background: var(--panel-bg);
      border: 1px solid var(--primary-gold);
      border-radius: 8px;
      padding: 20px;
      z-index: 1000;
      box-shadow: 0 10px 35px rgba(0,0,0,0.7);
      backdrop-filter: blur(10px);
    }}

    #detail-overlay h3 {{
      font-family: 'Cinzel', serif;
      color: var(--primary-gold);
      font-size: 1.15rem;
      margin-bottom: 4px;
    }}

    #detail-overlay .sub-name {{
      font-size: 0.85rem;
      color: #94a3b8;
      font-style: italic;
      margin-bottom: 12px;
    }}

    .meta-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 12px;
      background: rgba(0,0,0,0.3);
      padding: 10px;
      border-radius: 6px;
    }}

    .meta-item {{
      font-size: 0.75rem;
    }}

    .meta-item strong {{
      color: #e2e8f0;
    }}

    .detail-text {{
      font-size: 0.82rem;
      color: #e2e8f0;
      line-height: 1.5;
      margin-bottom: 10px;
    }}

    .detail-source {{
      border-left: 2px solid var(--primary-gold);
      padding-left: 10px;
      font-size: 0.75rem;
      color: #cbd5e1;
      font-style: italic;
    }}

    .close-btn {{
      position: absolute;
      top: 14px;
      right: 14px;
      background: none;
      border: none;
      color: #94a3b8;
      font-size: 1.2rem;
      cursor: pointer;
    }}

    .close-btn:hover {{
      color: #fff;
    }}

    /* Custom Leaflet Markers */
    .custom-menzil-icon {{
      background: #111827;
      border: 2px solid var(--primary-gold);
      color: var(--primary-gold);
      font-weight: 700;
      font-size: 11px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px rgba(212, 175, 55, 0.6);
      transition: all 0.3s;
    }}

    .custom-menzil-icon:hover {{
      transform: scale(1.3);
      background: var(--primary-gold);
      color: #000;
    }}
  </style>
</head>
<body>

  <header>
    <div class="logo-section">
      <div class="monogram">خ</div>
      <div class="title-group">
        <h1>{title}</h1>
        <p>Hâdimü'l-Haremeyn :: Dijital Askeri Coğrafya ve Lojistik Arşivi</p>
      </div>
    </div>
    <div class="stats-bar">
      <div class="stat-badge">
        <span class="stat-value">{len(features)}</span>
        <span class="stat-label">Menzil Sayısı</span>
      </div>
      <div class="stat-badge">
        <span class="stat-value">~{int(total_distance):,} km</span>
        <span class="stat-label">Toplam İntikal</span>
      </div>
      <div class="stat-badge">
        <span class="stat-value">1512 - 1520</span>
        <span class="stat-label">Devr-i Selîmî</span>
      </div>
    </div>
  </header>

  <div id="main-wrapper">
    <div id="map"></div>

    <div id="sidebar">
      <div class="sidebar-header">
        <h2>Menzilnâme Kayıtları</h2>
        <span style="font-size: 0.75rem; color: var(--text-muted);">{geojson_data.get('name', '')}</span>
      </div>
      
      <div class="timeline-controls">
        <button id="playBtn" class="btn">▶ Seferi Oynat</button>
        <button id="resetBtn" class="btn btn-secondary">↺ Sıfırla</button>
      </div>

      <div class="menzil-list" id="menzilList"></div>
    </div>

    <!-- Selected Detail Modal -->
    <div id="detail-overlay">
      <button class="close-btn" onclick="closeDetail()">&times;</button>
      <h3 id="detName">Menzil İsmi</h3>
      <div class="sub-name" id="detHistName">Tarihsel İmla</div>
      <div class="meta-grid">
        <div class="meta-item">📅 <strong>Tarih:</strong> <span id="detDate">-</span></div>
        <div class="meta-item">⏳ <strong>İkâmet:</strong> <span id="detStay">-</span></div>
        <div class="meta-item">⛰️ <strong>Rakım:</strong> <span id="detElev">-</span></div>
        <div class="meta-item">💧 <strong>Su Hali:</strong> <span id="detWater">-</span></div>
      </div>
      <div class="detail-text" id="detLogistics">Lojistik notu buraya gelir.</div>
      <div class="detail-source" id="detSource">Kaynak: Haydar Çelebi Ruznâmesi</div>
    </div>
  </div>

  <script>
    const geojsonData = {raw_geojson_json};
    const campaignData = {raw_campaign_json};
    
    // Haritayı başlat
    const map = L.map('map', {{
      center: [36.5, 36.0],
      zoom: 6,
      zoomControl: true
    }});

    // Koyu harita altlığı (CartoDB DarkMatter)
    const cartoDark = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap &copy; CARTO | hadimul-harameyn',
      subdomains: 'abcd',
      maxZoom: 19
    }}).addTo(map);

    // Uydu altlığı alternatifi
    const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      attribution: 'Tiles &copy; Esri'
    }});

    L.control.layers({{
      "Karanlık Arşiv Haritası": cartoDark,
      "Tarihsel Uydu Görünümü": esriSat
    }}).addTo(map);

    const latlngs = [];
    const markers = [];
    const features = geojsonData.features || [];

    // Polyline güzergah hattı
    features.forEach(f => {{
      const coords = f.geometry.coordinates;
      latlngs.push([coords[1], coords[0]]);
    }});

    const routeLine = L.polyline(latlngs, {{
      color: '{theme_color}',
      weight: 3.5,
      opacity: 0.85,
      dashArray: '6, 8',
      lineCap: 'round'
    }}).addTo(map);

    if (latlngs.length > 0) {{
      map.fitBounds(routeLine.getBounds(), {{ padding: [50, 50] }});
    }}

    // Sidebar Listesi & Marker'lar
    const listContainer = document.getElementById('menzilList');

    features.forEach((feat, index) => {{
      const p = feat.properties;
      const coords = feat.geometry.coordinates;
      const latlng = [coords[1], coords[0]];

      // Custom HTML Marker
      const customIcon = L.divIcon({{
        className: 'custom-menzil-icon',
        html: `<span>${{p.step_order}}</span>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      }});

      const marker = L.marker(latlng, {{ icon: customIcon }}).addTo(map);
      marker.on('click', () => selectMenzil(index));
      markers.push(marker);

      // Sidebar Card
      const card = document.createElement('div');
      card.className = 'menzil-card';
      card.id = `card-${{index}}`;
      card.innerHTML = `
        <div class="card-top">
          <span class="card-order">MENZİL #${{p.step_order}}</span>
          <span class="card-date">${{p.date_reached || ''}}</span>
        </div>
        <div class="card-title">${{p.name}}</div>
        <div class="card-historical">${{p.historical_name || ''}}</div>
        <div class="card-excerpt">${{p.logistics_note ? p.logistics_note.substring(0, 85) + '...' : ''}}</div>
      `;
      card.onclick = () => selectMenzil(index);
      listContainer.appendChild(card);
    }});

    function selectMenzil(index) {{
      const feat = features[index];
      const p = feat.properties;
      const coords = feat.geometry.coordinates;
      const latlng = [coords[1], coords[0]];

      // Pan harita
      map.flyTo(latlng, 9, {{ duration: 1.2 }});

      // Kart aktifliği
      document.querySelectorAll('.menzil-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById(`card-${{index}}`);
      if (activeCard) {{
        activeCard.classList.add('active');
        activeCard.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
      }}

      // Modal doldur
      document.getElementById('detName').textContent = `#${{p.step_order}} ${{p.name}}`;
      document.getElementById('detHistName').textContent = p.historical_name || '';
      document.getElementById('detDate').textContent = p.date_reached || '-';
      document.getElementById('detStay').textContent = p.stay_duration_days ? `${{p.stay_duration_days}} gün` : 'Günübirlik';
      document.getElementById('detElev').textContent = p.elevation_meters ? `${{p.elevation_meters}} m` : '-';
      document.getElementById('detWater').textContent = p.water_supply_status || 'Kayıt yok';
      document.getElementById('detLogistics').textContent = p.logistics_note || (p.historical_event || '');
      document.getElementById('detSource').textContent = p.primary_source_ref ? `Kaynak: ${{p.primary_source_ref}}` : '';

      document.getElementById('detail-overlay').style.display = 'block';
    }}

    function closeDetail() {{
      document.getElementById('detail-overlay').style.display = 'none';
      document.querySelectorAll('.menzil-card').forEach(c => c.classList.remove('active'));
    }}

    // Play Simulation
    let playInterval = null;
    let currentStep = 0;
    const playBtn = document.getElementById('playBtn');

    playBtn.addEventListener('click', () => {{
      if (playInterval) {{
        clearInterval(playInterval);
        playInterval = null;
        playBtn.textContent = '▶ Seferi Oynat';
        playBtn.classList.remove('btn-secondary');
      }} else {{
        playBtn.textContent = '⏸ Duraklat';
        playBtn.classList.add('btn-secondary');
        if (currentStep >= features.length) currentStep = 0;

        playInterval = setInterval(() => {{
          if (currentStep < features.length) {{
            selectMenzil(currentStep);
            currentStep++;
          }} else {{
            clearInterval(playInterval);
            playInterval = null;
            playBtn.textContent = '▶ Tekrar Oynat';
            playBtn.classList.remove('btn-secondary');
          }}
        }}, 2200);
      }}
    }});

    document.getElementById('resetBtn').addEventListener('click', () => {{
      if (playInterval) {{
        clearInterval(playInterval);
        playInterval = null;
        playBtn.textContent = '▶ Seferi Oynat';
      }}
      currentStep = 0;
      closeDetail();
      if (latlngs.length > 0) {{
        map.fitBounds(routeLine.getBounds(), {{ padding: [50, 50] }});
      }}
    }});
  </script>
</body>
</html>
"""
        out_path = self.output_dir / out_filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  ✓ İnteraktif Harita Üretildi: {out_path.resolve()}")
        return out_path

    def generate_folium_map(self, campaign_key: str) -> Optional[Path]:
        """Folium kütüphanesi kullanarak alternatif HTML üretir."""
        if not HAS_FOLIUM:
            return None

        if campaign_key in ("caldiran", "caldiran-1514", "1514"):
            geojson_file = "caldiran-expedition.geojson"
            out_filename = "caldiran-folium.html"
            line_color = "#e74c3c"
        elif campaign_key in ("turnadagi", "turnadagi-1515", "1515"):
            geojson_file = "turnadagi-expedition.geojson"
            out_filename = "turnadagi-folium.html"
            line_color = "#e67e22"
        elif campaign_key in ("kochisir", "kochisir-1516", "1516"):
            geojson_file = "kochisir-expedition.geojson"
            out_filename = "kochisir-folium.html"
            line_color = "#3498db"
        else:
            geojson_file = "egypt-conquest.geojson"
            out_filename = "egypt-folium.html"
            line_color = "#f39c12"

        geojson_data = self.load_geojson(geojson_file)
        features = geojson_data.get("features", [])
        if not features:
            return None

        # Başlangıç noktası
        start_coord = features[0]["geometry"]["coordinates"]
        m = folium.Map(
            location=[start_coord[1], start_coord[0]],
            zoom_start=6,
            tiles="CartoDB dark_matter"
        )

        points = []
        for feat in features:
            props = feat.get("properties", {})
            coords = feat["geometry"]["coordinates"]
            lat, lon = coords[1], coords[0]
            points.append([lat, lon])

            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px; width: 220px;">
                <b style="color: #b78103;">#{props.get('step_order')} {props.get('name')}</b><br>
                <i>{props.get('historical_name', '')}</i><hr style="margin: 4px 0;">
                <b>Tarih:</b> {props.get('date_reached', '-')}<br>
                <b>Su Durumu:</b> {props.get('water_supply_status', '-')}<br>
                <b>Lojistik:</b> {props.get('logistics_note', '')}<br>
                <small style="color: #666;">{props.get('primary_source_ref', '')}</small>
            </div>
            """
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                popup=folium.Popup(popup_html, max_width=250),
                color=line_color,
                fill=True,
                fill_color="#ffffff",
                fill_opacity=0.9
            ).add_to(m)

        # Çizgi ekle
        folium.PolyLine(
            locations=points,
            color=line_color,
            weight=3.5,
            opacity=0.8,
            dash_array="5, 10"
        ).add_to(m)

        out_path = self.output_dir / out_filename
        m.save(str(out_path))
        print(f"  ✓ Folium Haritası Üretildi: {out_path.resolve()}")
        return out_path

    def generate_portal_index(self):
        """Tüm haritaları, seferleri ve birincil kaynak alıntılarını sunan zengin index.html portalı üretir."""
        quotes_path = self.root_dir / "data" / "quotes" / "historical-quotes.json"
        quotes_data = []
        if quotes_path.exists():
            try:
                with open(quotes_path, "r", encoding="utf-8") as f:
                    q_json = json.load(f)
                    quotes_data = q_json.get("quotes", [])
            except Exception:
                pass

        quotes_json_str = json.dumps(quotes_data, ensure_ascii=False)

        index_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>hadimul-harameyn :: I. Selim Devri Dijital Tarih & Sefer Portalı</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Amiri:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --gold-primary: #d4af37;
      --gold-light: #f3e5ab;
      --gold-dark: #997f24;
      --ruby-red: #c0392b;
      --bg-dark: #0a0e17;
      --card-bg: #131926;
      --card-hover: #182234;
      --border-color: #243147;
      --text-main: #e2e8f0;
      --text-muted: #94a3b8;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(212, 175, 55, 0.08) 0%, transparent 60%),
        radial-gradient(circle at 80% 80%, rgba(192, 57, 43, 0.05) 0%, transparent 50%);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 50px 20px 80px 20px;
    }}
    .container {{
      max-width: 1140px;
      width: 100%;
    }}
    .header-badge {{
      display: inline-block;
      text-align: center;
      margin-bottom: 16px;
      padding: 6px 18px;
      border-radius: 30px;
      border: 1px solid rgba(212, 175, 55, 0.35);
      background: rgba(212, 175, 55, 0.08);
      color: var(--gold-primary);
      font-size: 0.8rem;
      letter-spacing: 2px;
      text-transform: uppercase;
      font-weight: 600;
    }}
    .header {{
      text-align: center;
      margin-bottom: 48px;
    }}
    h1.main-title {{
      font-family: 'Cinzel', serif;
      color: #ffffff;
      font-size: 2.8rem;
      font-weight: 900;
      letter-spacing: 1px;
      margin-bottom: 12px;
      text-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
    }}
    h1.main-title span {{
      color: var(--gold-primary);
    }}
    .arabic-epigraph {{
      font-family: 'Amiri', serif;
      font-size: 1.6rem;
      color: var(--gold-light);
      direction: rtl;
      margin-bottom: 8px;
    }}
    .subtitle {{
      color: var(--text-muted);
      font-size: 1.05rem;
      max-width: 760px;
      margin: 0 auto;
      line-height: 1.7;
    }}
    
    /* Stats Bar */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 48px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      transition: all 0.25s ease;
    }}
    .stat-card:hover {{
      border-color: var(--gold-primary);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }}
    .stat-num {{
      font-family: 'Cinzel', serif;
      font-size: 1.9rem;
      font-weight: 700;
      color: var(--gold-primary);
      margin-bottom: 4px;
    }}
    .stat-label {{
      font-size: 0.78rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      font-weight: 600;
    }}

    /* Quotes Showcase Section */
    .quote-section {{
      background: linear-gradient(145deg, #121927 0%, #0d131e 100%);
      border: 1px solid rgba(212, 175, 55, 0.3);
      border-radius: 12px;
      padding: 36px 40px;
      margin-bottom: 48px;
      position: relative;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    .quote-badge {{
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 20px;
      background: rgba(192, 57, 43, 0.2);
      color: #ff7675;
      border: 1px solid rgba(192, 57, 43, 0.4);
      margin-bottom: 16px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .quote-original {{
      font-family: 'Amiri', serif;
      font-size: 1.4rem;
      color: var(--gold-light);
      margin-bottom: 14px;
      line-height: 1.8;
    }}
    .quote-turkish {{
      font-size: 1.15rem;
      font-style: italic;
      color: #ffffff;
      line-height: 1.7;
      margin-bottom: 18px;
      font-weight: 400;
    }}
    .quote-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      border-top: 1px solid var(--border-color);
      padding-top: 16px;
    }}
    .quote-speaker {{
      font-size: 0.92rem;
      font-weight: 700;
      color: var(--gold-primary);
    }}
    .quote-source {{
      font-size: 0.82rem;
      color: var(--text-muted);
    }}
    .quote-nav {{
      display: flex;
      gap: 10px;
    }}
    .quote-btn {{
      background: #1a2334;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.2s;
    }}
    .quote-btn:hover {{
      background: var(--gold-primary);
      color: #000;
      border-color: var(--gold-primary);
    }}

    /* Campaign Cards */
    .section-title {{
      font-family: 'Cinzel', serif;
      font-size: 1.6rem;
      color: #ffffff;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .section-title::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border-color);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 24px;
      margin-bottom: 48px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 30px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}
    .card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--gold-primary), transparent);
    }}
    .card.egypt::before {{
      background: linear-gradient(90deg, var(--ruby-red), var(--gold-primary));
    }}
    .card:hover {{
      border-color: var(--gold-primary);
      transform: translateY(-4px);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
    }}
    .card-tag {{
      display: inline-block;
      font-size: 0.72rem;
      color: var(--gold-primary);
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }}
    .card h2 {{
      font-family: 'Cinzel', serif;
      color: #fff;
      font-size: 1.45rem;
      margin-bottom: 12px;
      line-height: 1.3;
    }}
    .card p {{
      color: var(--text-muted);
      font-size: 0.9rem;
      line-height: 1.7;
      margin-bottom: 24px;
    }}
    .card-footer {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .btn {{
      display: inline-block;
      text-align: center;
      background: var(--gold-primary);
      color: #0b0f17;
      text-decoration: none;
      padding: 11px 20px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.88rem;
      transition: all 0.2s;
    }}
    .btn:hover {{
      background: var(--gold-light);
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.35);
    }}
    .btn-secondary {{
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-main);
    }}
    .btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.06);
      border-color: var(--gold-primary);
      color: var(--gold-primary);
    }}

    /* Battles Table */
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      overflow-x: auto;
      margin-bottom: 48px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      text-align: left;
    }}
    th {{
      background: #182234;
      color: var(--gold-primary);
      font-family: 'Cinzel', serif;
      font-weight: 700;
      padding: 14px 18px;
      border-bottom: 1px solid var(--border-color);
      letter-spacing: 0.5px;
    }}
    td {{
      padding: 14px 18px;
      border-bottom: 1px solid rgba(36, 49, 71, 0.6);
      color: var(--text-main);
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover td {{
      background: rgba(212, 175, 55, 0.03);
    }}
    .badge-year {{
      background: rgba(212, 175, 55, 0.15);
      color: var(--gold-primary);
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.78rem;
    }}

    /* Footer */
    footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: 0.82rem;
      padding-top: 30px;
      border-top: 1px solid var(--border-color);
    }}
    footer a {{
      color: var(--gold-primary);
      text-decoration: none;
    }}
    footer a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="container">
    
    <div class="header">
      <div class="header-badge">Açık Kaynak Dijital Tarih & GIS Arşivi</div>
      <div class="arabic-epigraph">خادم الحرمين الشريفين السلطان سليم خان الأول</div>
      <h1 class="main-title">hadimul-<span>harameyn</span></h1>
      <p class="subtitle">
        I. Selim (Yavuz) dönemine (1512–1520) ait askeri sefer lojistiğini, WGS84 menzil koordinatlarını, 
        dönüm noktası meydan muharebelerini ve birincil kaynak vakayinâmelerini buluşturan akademik araştırma arşivi.
      </p>
    </div>

    <!-- Stats Dashboard -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-num">60</div>
        <div class="stat-label">Doğrulanmış Menzil (WGS84)</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">6</div>
        <div class="stat-label">Kayıtlı Meydan Muharebesi</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">18</div>
        <div class="stat-label">Çağdaş Vakayinâme & Vesika</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">50</div>
        <div class="stat-label">Birincil Tarihsel Alıntı</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">5.800+</div>
        <div class="stat-label">Kilometre Lojistik Güzergâh</div>
      </div>
    </div>

    <!-- Quotes Showcase -->
    <div class="quote-section" id="quoteSection">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="quote-badge" id="quoteCategory">HADİMÜ'L-HAREMEYN & HİLAFET</span>
        <div class="quote-nav">
          <button class="quote-btn" onclick="prevQuote()">← Önceki</button>
          <button class="quote-btn" onclick="nextQuote()">Sonraki →</button>
        </div>
      </div>
      <div class="quote-original" id="quoteOriginal">
        لا تقل حاكم الحرمين الشريفين، بل خادم الحرمين الشريفين
      </div>
      <div class="quote-turkish" id="quoteTurkish">
        "Bana Mekke ve Medine'nin Hâkimi demeyiniz; bilakis o iki mübarek mukaddes beldenin Hizmetkârı deyiniz!"
      </div>
      <div class="quote-meta">
        <div>
          <span class="quote-speaker" id="quoteSpeaker">I. Selim (Yavuz Sultan Selim)</span>
          <span style="color:#64748b; margin: 0 8px;">•</span>
          <span class="quote-source" id="quoteContext">Şam Emeviyye Camii Hutbesi (1516)</span>
        </div>
        <div class="quote-source" id="quoteSourceWork">
          Kaynak: Hoca Sâdeddin Efendi, Tâcü't-Tevârih
        </div>
      </div>
    </div>

    <!-- Maps Cards -->
    <div class="section-title">İnteraktif Coğrafi Sefer Haritaları</div>
    <div class="grid">
      <div class="card">
        <div>
          <img src="../assets/images/caldiran-battle-1514.jpg" alt="Çaldıran Seferi (1514)" style="width:100%; height:180px; object-fit:cover; border-radius:8px; margin-bottom:16px; border:1px solid #243147;" />
          <div class="card-tag">DOĞU SEFERİ • 1514 (21 MENZİL • 2.831 KM)</div>
          <h2>Çaldıran Seferi ve Tebriz Menzil Hattı</h2>
          <p>
            Üsküdar ordugâhından Sivas büyük teftiş merkezine, Erzurum ve Çaldıran sahrasından Safevî payitahtı Tebriz'e 
            uzanan 21 menzillik devasa lojistik intikal. Tabur cengi, topçu tahkimatı ve Trabzon ikmal hattı.
          </p>
        </div>
        <div class="card-footer">
          <a href="caldiran-campaign-map.html" class="btn">İnteraktif Haritayı Aç →</a>
          <a href="caldiran-folium.html" class="btn btn-secondary">Folium Katmanı</a>
        </div>
      </div>

      <div class="card">
        <div>
          <div class="card-tag" style="color: #e67e22;">ANADOLU SEFERİ • 1515 (10 MENZİL • 497 KM)</div>
          <h2>Turnadağı Seferi & Dulkadir İntikali</h2>
          <p>
            Kayseri'den Develi, Pınarbaşı ve Göksun geçitlerine; sarp Turnadağı yamaçlarından Elbistan ve Maraş'a 
            uzanan 10 menzillik dağ harekâtı. Anadolu Türk siyasi birliğinin kesinleştiği stratejik intikal.
          </p>
        </div>
        <div class="card-footer">
          <a href="turnadagi-campaign-map.html" class="btn" style="background: #e67e22;">İnteraktif Haritayı Aç →</a>
          <a href="turnadagi-folium.html" class="btn btn-secondary">Folium Katmanı</a>
        </div>
      </div>

      <div class="card">
        <div>
          <div class="card-tag" style="color: #3498db;">GÜNEYDOĞU SEFERİ • 1516 (10 MENZİL • 395 KM)</div>
          <h2>Koçhisar Seferi & Mardin/Cezire Hattı</h2>
          <p>
            Diyarbakır İçkale'den Mazıdağı ve Derik geçitlerine, Koçhisar (Hanik) zafer sahasından Mardin, Nusaybin 
            ve Urfa kalelerine uzanan 10 menzillik Güneydoğu feth-i mübîni.
          </p>
        </div>
        <div class="card-footer">
          <a href="kochisir-campaign-map.html" class="btn" style="background: #2980b9;">İnteraktif Haritayı Aç →</a>
          <a href="kochisir-folium.html" class="btn btn-secondary">Folium Katmanı</a>
        </div>
      </div>

      <div class="card egypt">
        <div>
          <img src="../assets/images/sinai-desert-crossing-1517.jpg" alt="Mısır Seferi (1516-1517)" style="width:100%; height:180px; object-fit:cover; border-radius:8px; margin-bottom:16px; border:1px solid #243147;" />
          <div class="card-tag">GÜNEY & MISIR SEFERİ • 1516-1517 (19 MENZİL • 2.155 KM)</div>
          <h2>Mısır ve Suriye Fethi Güzergâhı</h2>
          <p>
            Mercidâbık zaferiyle açılan Suriye kapılarından Şam'a, su kervanlarıyla zayiatsız geçilen 10 günlük 
            efsanevi Sina Çölü intikalinden Ridâniye ve Kahire'ye uzanan 19 menzillik feth-i mübîn.
          </p>
        </div>
        <div class="card-footer">
          <a href="egypt-campaign-map.html" class="btn">İnteraktif Haritayı Aç →</a>
          <a href="egypt-folium.html" class="btn btn-secondary">Folium Katmanı</a>
        </div>
      </div>
    </div>

    <!-- Battles Table -->
    <div class="section-title">I. Selim Devri Seferleri & Meydan Muharebeleri Külliyatı</div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Yıl</th>
            <th>Muharebe / Sefer</th>
            <th>Bölge</th>
            <th>Komutanlar</th>
            <th>Taktik Dönüm Noktası</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="badge-year">1514</span></td>
            <td><strong>Çaldıran Meydan Muharebesi</strong></td>
            <td>Çaldıran Ovası, Doğu Anadolu</td>
            <td>Yavuz Sultan Selim vs Şah I. İsmail</td>
            <td>Top arabalarının zincirlenmesi (Tabur Cengi), salvo tüfek ateşi</td>
          </tr>
          <tr>
            <td><span class="badge-year">1515</span></td>
            <td><strong>Kemah Kalesi Fethi</strong></td>
            <td>Kemah, Fırat Boyu</td>
            <td>Bıyıklı Mehmed Paşa</td>
            <td>Sarp burçların kuşatılması, Doğu Anadolu lojistiğinin güvenceye alınması</td>
          </tr>
          <tr>
            <td><span class="badge-year">1515</span></td>
            <td><strong>Turnadağı Muharebesi</strong></td>
            <td>Turnadağı / Göksun, Maraş</td>
            <td>Hadım Sinan Paşa vs Alâüddevle Bozkurt</td>
            <td>Sarp dağ geçidi çevirmesi, Anadolu Türk siyasi birliğinin kesinleşmesi</td>
          </tr>
          <tr>
            <td><span class="badge-year">1516</span></td>
            <td><strong>Koçhisar (Hanik) Muharebesi</strong></td>
            <td>Kızıltepe / Mardin Civarı</td>
            <td>Bıyıklı Mehmed Paşa & İdris-i Bitlisî vs Karahan</td>
            <td>Tüfek pususu ve Kürt aşiret süvari kıskacı, Güneydoğu'nun nihai fethi</td>
          </tr>
          <tr>
            <td><span class="badge-year">1516</span></td>
            <td><strong>Mercidâbık Meydan Muharebesi</strong></td>
            <td>Mercidâbık Ovası, Halep Kuzeyi</td>
            <td>Yavuz Sultan Selim vs Sultan Kansu Gavri</td>
            <td>Hafif sahra topları salvosu, Suriye ve Filistin'in fethi</td>
          </tr>
          <tr>
            <td><span class="badge-year">1516</span></td>
            <td><strong>Han Yûnus (Gazze) Muharebesi</strong></td>
            <td>Han Yûnus, Güney Filistin</td>
            <td>Hadım Sinan Paşa vs Canbirdi Gazâlî</td>
            <td>Çöl eşiğinde öncü pusu kırma manevrası, Sina ikmal kapısının açılması</td>
          </tr>
          <tr>
            <td><span class="badge-year">1517</span></td>
            <td><strong>Ridâniye Meydan Muharebesi</strong></td>
            <td>El-Mukattam & Ridâniye, Kahire</td>
            <td>Yavuz Sultan Selim vs Sultan Tomanbay</td>
            <td>Mukattam Dağı çevirmesiyle Memlûk sabit top bataryalarının arkalanması</td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer>
      <p>
        <strong>hadimul-harameyn</strong> • Dijital Tarih & Tarihsel GIS Mühendisliği Projesi • MIT Lisansı<br>
        <a href="https://github.com/bahattinyunus/hadimul-harameyn" target="_blank">GitHub Deposu</a> • 
        Kemalpaşazâde, Celâlzâde Mustafa, İdrîs-i Bitlisî, Hoca Sâdeddin, İbn İyâs ve Marino Sanuto kaynaklarıyla doğrulanmıştır.
      </p>
    </footer>

  </div>

  <script>
    const quotes = {quotes_json_str};
    let currentIndex = 0;

    function renderQuote(idx) {{
      if (!quotes || quotes.length === 0) return;
      const q = quotes[idx];
      document.getElementById('quoteCategory').textContent = (q.category || 'TARİHSEL KELÂM').replace(/_/g, ' ').toUpperCase();
      document.getElementById('quoteOriginal').textContent = q.original_text || q.transcription || '';
      document.getElementById('quoteTurkish').textContent = '"' + (q.modern_turkish || '') + '"';
      document.getElementById('quoteSpeaker').textContent = q.speaker + (q.speaker_title ? ' (' + q.speaker_title + ')' : '');
      document.getElementById('quoteContext').textContent = q.event_or_context || (q.year ? q.year.toString() : '');
      document.getElementById('quoteSourceWork').textContent = 'Kaynak: ' + (q.source_work || '') + (q.author ? ' (' + q.author + ')' : '');
    }}

    function nextQuote() {{
      if (!quotes || quotes.length === 0) return;
      currentIndex = (currentIndex + 1) % quotes.length;
      renderQuote(currentIndex);
    }}

    function prevQuote() {{
      if (!quotes || quotes.length === 0) return;
      currentIndex = (currentIndex - 1 + quotes.length) % quotes.length;
      renderQuote(currentIndex);
    }}

    if (quotes && quotes.length > 0) {{
      renderQuote(0);
      setInterval(nextQuote, 12000); // 12 saniyede bir otomatik geçiş
    }}
  </script>
</body>
</html>
"""
        index_path = self.output_dir / "index.html"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_html)
        print(f"  ✓ Portal Ana Sayfası Üretildi: {index_path.resolve()}")



def main():
    parser = argparse.ArgumentParser(description="hadimul-harameyn Harita Üretici")
    parser.add_argument(
        "--campaign",
        type=str,
        default="all",
        choices=[
            "caldiran-1514", "turnadagi-1515", "kochisir-1516", "egypt-1517",
            "all", "caldiran", "turnadagi", "kochisir", "egypt"
        ],
        help="Üretilecek sefer haritası"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="build",
        help="Çıktı klasörü (varsayılan: build)"
    )

    args = parser.parse_args()
    generator = RouteMapGenerator(output_dir=Path(args.output_dir))

    print("\n🗺️  hadimul-harameyn :: Harita Üretim Motoru Başlatıldı...")
    if args.campaign in ("caldiran-1514", "caldiran", "all"):
        generator.generate_interactive_html("caldiran")
        generator.generate_folium_map("caldiran")

    if args.campaign in ("turnadagi-1515", "turnadagi", "all"):
        generator.generate_interactive_html("turnadagi")
        generator.generate_folium_map("turnadagi")

    if args.campaign in ("kochisir-1516", "kochisir", "all"):
        generator.generate_interactive_html("kochisir")
        generator.generate_folium_map("kochisir")

    if args.campaign in ("egypt-1517", "egypt", "all"):
        generator.generate_interactive_html("egypt")
        generator.generate_folium_map("egypt")

    generator.generate_portal_index()
    print("\n✨ Tüm harita çıktıları başarıyla hazırlandı!\n")


if __name__ == "__main__":
    main()
