| İddia | Senaryodaki değer | Tool değeri | Kullanılan tool | Sonuç (DOĞRU/YANLIŞ/DOĞRULANAMADI) |
|---|---:|---:|---|---|
| Final maçının tarihi ve aşaması | 2022 Dünya Kupası finali | 18.12.2022, Final | `mac_bul`, `mac_yukle` | DOĞRU |
| Rakip | Fransa | Argentina–France | `mac_bul`, `mac_yukle` | DOĞRU |
| Maç skoru | 3-3 | Argentina 3-3 France | `mac_bul`, `mac_yukle` | DOĞRU |
| Maçın penaltılarla sonuçlanması | Penaltılar | Penaltı atışları 4-2 | `mac_yukle` | DOĞRU |
| Messi’nin pası | 60 | 60 | `oyuncu_istatistik` | DOĞRU |
| Messi’nin şutu (maç istatistiği, penaltı atışları hariç) | 5 | 5 | `oyuncu_istatistik` | DOĞRU |
| Messi’nin top kazanması | 7 | 7 | `en_cok_top_kapan` | DOĞRU |
| Messi’nin golü (maç istatistiği, penaltı atışları hariç) | 2 | 2 | `oyuncu_istatistik` | DOĞRU |
| Messi’nin şutu (penaltı atışları dahil sorgu) | Senaryoda ayrıca belirtilmiyor | 6 | `oyuncu_istatistik` (`penalti_atislari=true`) | DOĞRULANAMADI |
| Messi’nin golü (penaltı atışları dahil sorgu) | Senaryoda ayrıca belirtilmiyor | 3 | `oyuncu_istatistik` (`penalti_atislari=true`) | DOĞRULANAMADI |
| Messi’nin açılış golünü penaltıdan atması | Penaltıdan açılış golü | Oyuncu istatistik aracı yalnızca toplam pas, şut ve gol sayılarını veriyor | `oyuncu_istatistik` | DOĞRULANAMADI |
| Mbappé’nin peş peşe karşılık vermesi | İki golle karşılık | 3 gol | `oyuncu_istatistik` | DOĞRULANAMADI |
| Uzatmada Messi’nin ribaundu gole çevirmesi | Gol | Oyuncu istatistik aracı golün nasıl atıldığını veya zamanını vermiyor | `oyuncu_istatistik` | DOĞRULANAMADI |
| Kupayı kaldıran kaptanın Messi olması | Messi | Maç araçları kaptanlık veya kupa kaldırma bilgisini vermiyor | — | DOĞRULANAMADI |
| Görseldeki yer bilgisi | LUSAIL | Maç araçları stat/şehir bilgisi döndürmedi | `mac_bul`, `mac_yukle` | DOĞRULANAMADI |

**Özet:** Senaryodaki maç skoru ve Messi’nin standart maç istatistikleri araç çıktılarıyla uyuşuyor. Messi için penaltı atışları da dahil edilince şut ve gol toplamları 6 ve 3 oluyor; senaryonun istatistik satırı, penaltı atışları hariç sorguyla eşleşiyor. Gol olaylarının sırası, oluş biçimi ve kupa/kaptanlık bilgileri TT araçlarının döndürdüğü verilerle doğrulanamadı.