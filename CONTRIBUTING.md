# `hadimul-harameyn` Katkı Sağlama Rehberi (Contributing Guidelines)

Bu depo, Yavuz Sultan Selim devri (1512–1520) askeri menzillerini, diplomatik yazışmalarını ve birincil kaynak verilerini yapılandırılmış dijital formatlarda yaşatmayı hedefler. Katkılarınızın akademik muteberliği ve veri bütünlüğü için aşağıdaki standartlara titizlikle uyulmalıdır.

---

## 🏛️ 1. Akademik Doğrulama Standartları

Bu projeye eklenecek her sefer, muharebe, menzil veya kronolojik hadise, en az birincil (dönem kaynağı) veya rüştünü ispatlamış akademik tetkikle teyit edilmelidir:

### Birincil Kaynaklar:
* **Kemalpaşazâde (İbn Kemal):** *Tevârih-i Âl-i Osmân, IX. Defter* (Haz. Şerafettin Turan, TTK).
* **Celâlzâde Mustafa Çelebi:** *Selimnâme* (Haz. Ahmet Uğur - Mustafa Çuhadar, MEB).
* **İdris-i Bitlisî:** *Selimnâme* (Farsça nüshalar / Çev. Hicabi Kırlangıç).
* **Hoca Sâdeddin Efendi:** *Tâcü't-Tevârih*, Cilt IV (Kültür Bakanlığı).
* **İbn İyâs:** *Bedâi'u'z-Zuhûr fî Vekâi'i'd-Duhûr* (Kahire'nin çağdaş Memlûk vakayinamesi).
* **Feridun Ahmed Bey:** *Münşeâtü's-Selâtîn* (Dönemin ferman ve fetihnâmeleri).
* **Haydar Çelebi:** *Ruznâme* (Sefer günlükleri ve menzil kayıtları).

### İkincil / Akademik Tetkikler:
* Feridun Emecen, *Yavuz Sultan Selim*, Kapı Yayınları.
* Halil İnalcık, *Osmanlı İmparatorluğu: Klasik Çağ (1300-1600)*.
* Şerafettin Turan, *Yavuz Sultan Selim Dönemi*, TTK.

---

## 🧭 2. Coğrafi Veri ve Menzil Standartları (`data/routes/*.geojson`)

Menzil eklerken aşağıdaki kurallar esastır:

1. **Koordinat Formatı:** WGS84 standardı `[boylam (longitude), enlem (latitude)]` sıralamasıyla (GeoJSON standardı) kaydedilmelidir.
2. **Yer İsimleri:**
   * `name`: Güncel Türkçe isim (örn. *Han Yûnus*, *Mercidabık*, *Sivas*).
   * `historical_name`: Osmanlıca/Arapça tarihsel transkripsiyonlu imlası (örn. *Hân-ı Yûnus*, *Merg-i Dâbık*).
3. **Kronolojik Sıra:** `node_id` menzilin sefer kronolojisindeki sırasını temsil etmelidir (`MNZ-001`, `MNZ-002` gibi).
4. **Lojistik & Topoğrafik Notlar:** Varsa su kuyusu durumu, aşiret geçitleri, zahire depoları ve ordunun menzilde konakladığı gün sayısı `logistics_note` alanında belirtilmelidir.

---

## 📐 3. JSON Şema Doğrulaması

Her JSON dosyası, `schemas/` klasöründeki ilgili şema ile %100 uyumlu olmalıdır. PR göndermeden önce mutlaka doğrulama scriptini çalıştırınız:

```bash
python tools/validate_data.py
```

Tüm kontroller geçmeden (Exit code: 0) PR'lar kabul edilmez.

---

## 🧪 4. Testler

Test paketini çalıştırmak için:

```bash
pytest tests/ -v
```

---

## 🔄 5. Katkı Süreci (Git Workflow)

1. Projeyi çatallayın (`Fork`).
2. Yeni özellik dalı açın:
   ```bash
   git checkout -b feature/yeni-menzil-verisi
   ```
3. Verilerinizi ve kaynakçanızı ekleyin.
4. Doğrulama ve testleri koşun:
   ```bash
   python tools/validate_data.py
   pytest tests/ -v
   ```
5. Commit mesajınızda kaynağı net şekilde belirtin:
   ```text
   feat(routes): 1514 Seferi Erzincan-Tercan menzilleri eklendi (Kaynak: Haydar Çelebi Ruznamesi s. 68-72)
   ```
6. PR açın ve incelemeye sunun.
