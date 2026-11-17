# Doğrulama — cikti/senaryo.md (Kylian Mbappé, 2022 DK finali, match_id 3869685)

Doğrulayan: dogrulayici subagent (tt MCP tool'ları)

| # | İddia | Senaryodaki değer | Tool değeri | Kullanılan tool | Sonuç |
|---|---|---|---|---|---|
| 1 | Maç yılı (Metin 3, grafik) | 2022 | 2022 (tarih 2022-12-18, sezon 2022) | mac_yukle | DOĞRU |
| 2 | Maç: Arjantin – Fransa, Dünya Kupası finali (başlık, grafik) | Arjantin – Fransa, Final | Argentina–France, FIFA World Cup 2022 Final | mac_yukle | DOĞRU |
| 3 | Mbappé finali kazanamadı / kupa Messi'de (Metin 1, 13) | Fransa kaybetti | 3-3 (pen. 4-2), ev sahibi Argentina | mac_yukle | DOĞRU |
| 4 | Mbappé şut sayısı (Metin 6, grafik) | 6 | 6 | oyuncu_istatistik | DOĞRU |
| 5 | Mbappé gol sayısı / hat-trick (Metin 8, 14, grafik) | 3 | 3 | oyuncu_istatistik | DOĞRU |
| 6 | "Yarısı" (6 şutun yarısı gol, Metin 8) | 3/6 | 3/6 | oyuncu_istatistik | DOĞRU |
| 7 | Mbappé top kazanma (Metin 10, grafik) | 7 | 7 | en_cok_top_kapan | DOĞRU |
| 8 | Mbappé toplam pas (Metin 11, grafik) | 27 | 27 | oyuncu_istatistik | DOĞRU |
| 9 | Top kazanma Fransa 1. Tchouaméni | 15 | 15 | en_cok_top_kapan | DOĞRU |
| 10 | Top kazanma Fransa 2. Rabiot | 7 | 7 | en_cok_top_kapan | DOĞRU |
| 11 | Top kazanma sıralaması (Tchouaméni 1., Rabiot ve Mbappé ortak 2.) | 1 / 2 / 2 | Tchouaméni 15, Rabiot 7, Mbappé 7 | en_cok_top_kapan | DOĞRU |
| 12 | Penaltı atışları dahil şut (dipnot) | 7 | 7 | oyuncu_istatistik (penalti_atislari=true) | DOĞRU |
| 13 | Penaltı atışları dahil gol (dipnot) | 4 | 4 | oyuncu_istatistik (penalti_atislari=true) | DOĞRU |
| 14 | Uzatmalarda da gol/katkı (Metin 9, "Uzatmalarda bile") | uzatmada etkinlik | — | — | KONTROL EDİLEMEDİ |
| 15 | Şut haritası: goller dolu sarı, nokta boyutu xG (grafik) | xG gösterimi | — | — | KONTROL EDİLEMEDİ |

**Toplam: 13 DOĞRU, 0 YANLIŞ, 2 KONTROL EDİLEMEDİ**

Not: 14 ve 15 rakam içermiyor; 15 sut_haritasi tool açıklamasıyla uyumlu. Senaryodan çıkarma gerekmiyor.
