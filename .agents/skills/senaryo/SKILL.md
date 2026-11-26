---
name: senaryo
description: workflows/video_hazirla.md'deki tüm video akışını uçtan uca çalıştırır — Gemini analiz, Codex senaryo, dogrulayici kontrol, düzeltme, kapak. Bir oyuncunun maç performansından TT. tarzında kısa video senaryosu istendiğinde kullan.
argument-hint: "<oyuncu> [maç]  örn. Messi \"2022 Dünya Kupası finali\""
---

# Video Senaryosu Akışı

Girdi: `$ARGUMENTS` → oyuncu (zorunlu) ve maç (yoksa aktif maç = 2022 DK finali).
Önce `workflows/video_hazirla.md`'yi oku; komutların güncel hali oradadır. Her adımın çıktısı `cikti/`'ya yazılır.

## 0. Hazırlık
- Maç 2022 finali değilse `mac_bul` → `mac_yukle(match_id)`. Gemini de ayrı bir tt sunucusu kullandığı için
  Gemini prompt'una maçı (match_id ile) açıkça yaz ve `mac_yukle` çağırmasını söyle.
- `mkdir -p cikti`

## 1. Analiz — Gemini
`workflows/video_hazirla.md` 1. adımdaki `gemini --yolo -p ... > cikti/analiz.md 2> gemini_err.txt` komutunu
oyuncu ve maça göre uyarlayıp Bash ile çalıştır (uzun sürebilir, timeout'u geniş tut). 503 hatasında bir kez tekrar dene.
Gemini'nin abartılarına güvenme; rakamları 2. adımda kendin teyit edeceksin.

## 2. Senaryo — Codex (sen)
1. `bilgi_ara(soru="TT. kanalı anlatım tarzı kuralları kanca kapanış")` → tt_tarz.txt kurallarını al.
2. Konuya benzer video için ikinci bir `bilgi_ara` (ritim örneği; cümle kopyalama).
3. `oyuncu_istatistik(oyuncu)` (gerekirse `en_cok_top_kapan`) ile kullanacağın her rakamı teyit et.
4. `cikti/analiz.md` + kurallarla `cikti/senaryo.md` yaz.

**Senaryo kuralları (hepsi zorunlu):**
- **En fazla 35 saniye**: ~12-16 cümle, cümle başına 4-10 kelime. Yaklaşık süreyi (≈2,5 kelime/sn) dosyaya yaz.
- **Kanca önce, isim sonra**: ilk cümlede isim yok; isim 2. ya da 3. cümlede, tek başına.
- **Art arda iki cümle aynı kalıpla bitmez** (ör. ikisi de "-dı", "-du", "-yor" ile).
- **Tekrar eden kelime yok** (kök dahil; "gol" ve "golü" tekrar sayılır). Bağlaç/edat (ve, bir, bu) hariç.
- Kısa cümleler, tek kelimelik vurgu ("2022."), "..." ile gerilim; rakamla kapanış.
- Sadece tool'la doğrulanabilecek rakamlar.
- Sonda `EKRAN GRAFİKLERİ` ve sabit CTA bölümü.

Yazdıktan sonra kendi kontrolünü yap: cümleleri tek tek say, son ekleri art arda karşılaştır,
kelime köklerini listele ve tekrarları ayıkla. Bir kural bozuksa düzelt, sonra devam et.

## 3. Doğrulama — dogrulayici subagent
Agent tool'u ile `subagent_type: "dogrulayici"` çağır; prompt: "cikti/senaryo.md'deki her rakamı kontrol et.
Aktif maç: <maç, match_id>." Dönen tabloyu `cikti/dogrulama.md`'ye kaydet.
(Codex ile hızlı ikinci kontrol isteğe bağlıdır; video_hazirla.md 3. adımdaki `codex exec` komutu. Codex başka işte kullanılmaz.)

## 4. Düzeltme — Codex
Tabloda **YANLIŞ** varsa rakamı tool değeriyle değiştir, senaryo kurallarını yeniden kontrol et,
3. adımı tekrarla. En fazla 2 tur; hâlâ YANLIŞ kalırsa kullanıcıya bildir.
"KONTROL EDİLEMEDİ" satırları yanlış sayılmaz ama rakamsa senaryodan çıkarmayı öner.

## 5. Kapak
`sut_haritasi(oyuncu)` → dönen PNG'yi `cikti/kapak.png` olarak kopyala (`cp`).

## Bitiş
Kullanıcıya: senaryo metni, tahmini süre, doğrulama özeti (kaç DOĞRU / YANLIŞ / kontrol edilemedi)
ve dosya yolları: `cikti/analiz.md`, `cikti/senaryo.md`, `cikti/dogrulama.md`, `cikti/kapak.png`.
