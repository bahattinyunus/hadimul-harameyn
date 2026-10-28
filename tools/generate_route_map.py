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
        """Tüm haritaları ve seferleri tek bir ana sayfada sunan index.html portalı üretir."""
        index_html = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>hadimul-harameyn :: Dijital Tarih & Sefer Portalı</title>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    body {
      background: #0b0f17;
      color: #e2e8f0;
      font-family: 'Inter', sans-serif;
      margin: 0;
      padding: 40px 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .container {
      max-width: 900px;
      width: 100%;
    }
    h1 {
      font-family: 'Cinzel', serif;
      color: #d4af37;
      font-size: 2.2rem;
      text-align: center;
      margin-bottom: 8px;
    }
    .subtitle {
      text-align: center;
      color: #94a3b8;
      font-size: 1rem;
      margin-bottom: 40px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
      gap: 24px;
    }
    .card {
      background: #141c28;
      border: 1px solid #233044;
      border-radius: 8px;
      padding: 24px;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .card:hover {
      border-color: #d4af37;
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(212, 175, 55, 0.15);
    }
    .card h2 {
      font-family: 'Cinzel', serif;
      color: #fff;
      font-size: 1.25rem;
      margin-bottom: 10px;
    }
    .card p {
      color: #94a3b8;
      font-size: 0.88rem;
      line-height: 1.6;
      margin-bottom: 20px;
    }
    .btn {
      display: inline-block;
      text-align: center;
      background: #d4af37;
      color: #0b0f17;
      text-decoration: none;
      padding: 10px 18px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.85rem;
      transition: background 0.2s;
    }
    .btn:hover {
      background: #e5c158;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>`hadimul-harameyn`</h1>
    <div class="subtitle">I. Selim (Yavuz) Devri Askeri Sefer ve Lojistik Harita Portalı</div>
    <div class="grid">
      <div class="card">
        <div>
          <h2>Çaldıran Seferi (1514)</h2>
          <p>İstanbul'dan Sivas büyük ordugahına, oradan Çaldıran sahrası ve Tebriz payitahtına uzanan 21 menzillik lojistik intikal güzergahı.</p>
        </div>
        <a href="caldiran-campaign-map.html" class="btn">İnteraktif Haritayı Aç →</a>
      </div>
      <div class="card">
        <div>
          <h2>Mısır & Suriye Fethi (1516-1517)</h2>
          <p>Mercidabık'tan Şam'a, susuzluk çekilmeden geçilen 10 günlük efsanevi Sina Çölü intikalinden Ridaniye ve Kahire fethine uzanan 19 menzil.</p>
        </div>
        <a href="egypt-campaign-map.html" class="btn">İnteraktif Haritayı Aç →</a>
      </div>
    </div>
  </div>
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
        choices=["caldiran-1514", "egypt-1517", "all", "caldiran", "egypt"],
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

    if args.campaign in ("egypt-1517", "egypt", "all"):
        generator.generate_interactive_html("egypt")
        generator.generate_folium_map("egypt")

    generator.generate_portal_index()
    print("\n✨ Tüm harita çıktıları başarıyla hazırlandı!\n")


if __name__ == "__main__":
    main()
