---
name: mac-analiz
description: Bir maç ve oyuncu adı alıp tt MCP tool'larıyla oyuncunun istatistiklerini ve şut haritasını çıkarır, sonucu cikti/ klasörüne kaydeder. "X maçında Y'yi analiz et", "Y'nin istatistikleri ve şut haritası" gibi isteklerde kullan.
argument-hint: "<maç> <oyuncu>  örn. \"2022 Dünya Kupası finali\" Messi"
---

# Maç Analizi

Girdi: `$ARGUMENTS` → bir **maç** (turnuva/sezon/takımlar ya da match_id) ve bir **oyuncu adı**.
Eksikse kullanıcıya sor. Sayıları asla tahmin etme; her rakam bir tool çıktısından gelmeli.

## Adımlar

1. **Maçı aktif yap**
   - match_id verildiyse doğrudan `mac_yukle(match_id)`.
   - Maç 2022 Dünya Kupası finaliyse (3869685) yine `mac_yukle(3869685)` çağır; başka maç aktif kalmış olabilir.
   - Aksi halde `mac_bul(turnuva, sezon, takim)` → doğru maçı seç (birden fazla aday varsa kullanıcıya sor) → `mac_yukle(match_id)`.
   - Turnuva/takım adlarını İngilizce gönder (World Cup, Argentina, France).

2. **İstatistik**: `oyuncu_istatistik(oyuncu)`.
   - Birden fazla oyuncu eşleşirse adayları kullanıcıya göster, seçmesini iste.
   - Kullanıcı penaltı atışlarını isterse `penalti_atislari=true`; varsayılan false (resmi istatistik).

3. **Şut haritası**: `sut_haritasi(oyuncu)` → dönen PNG yolunu not et (dosya zaten `cikti/` altına yazılır).

4. **Bağlam (isteğe bağlı)**: oyuncunun takımı için `en_cok_top_kapan(takim)`; oyuncu listede varsa top kazanma sayısını ekle.

5. **Kaydet**: `cikti/<oyuncu_slug>_analiz.md` dosyasına yaz (slug: küçük harf, aksansız, boşluk yerine `_`). Şablon:

   ```markdown
   # <Oyuncu tam adı> — <Ev> <skor> <Deplasman> (<tarih>, <turnuva/aşama>)

   | İstatistik | Değer | Kaynak tool |
   |---|---|---|
   | Pas | … | oyuncu_istatistik |
   | Şut | … | oyuncu_istatistik |
   | Gol | … | oyuncu_istatistik |
   | Top kazanma | … / "listede yok" | en_cok_top_kapan |

   ![Şut haritası](<png dosya adı>)

   Notlar: penaltı atışları dahil/hariç; pas = toplam pas (isabet değil).
   ```

6. Kullanıcıya kısa özet + iki dosya yolunu (analiz .md ve şut haritası .png) ver.

## Yapma
- Tool'da olmayan rakam (isabetli pas, xG toplamı, dakika vb.) yazma; gerekiyorsa "veride yok" de.
- Mevcut `cikti/analiz.md`'nin üzerine yazma; o dosya `senaryo` akışına ait.
