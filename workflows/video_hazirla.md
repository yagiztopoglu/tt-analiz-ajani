# Video Hazırlama Akışı (3 model + tt MCP)

Bir oyuncunun maç performansından TT. tarzında kısa video senaryosu ve kapak üretir.
Her adımın çıktısı `cikti/` klasörüne kaydedilir. Örnek: Messi – 2022 Dünya Kupası finali.

| Adım | İş | Model / araç | Çıktı |
|---|---|---|---|
| 1. Analiz | Oyuncunun maç performansı | **Gemini** (gemini-cli) + tt MCP | `cikti/analiz.md` |
| 2. Senaryo | `tt_tarz.txt` kurallarına göre metin | **Claude** (Claude Code) + tt `bilgi_ara` | `cikti/senaryo.md` |
| 3. Doğrulama | Her rakamı tool'larla kontrol | **Codex** (`codex exec`) + tt MCP | `cikti/dogrulama.md` |
| 4. Düzeltme | Yanlış rakam varsa senaryoyu düzelt | **Claude** | `cikti/senaryo.md` |
| 5. Kapak | Şut haritası | **Claude** → tt `sut_haritasi` | `cikti/kapak.png` |

## Ön koşullar

- `tt` MCP sunucusu üç istemcide de kayıtlı olmalı (`tt_mcp_server.py`, `.venv` Python'u ile):
  - Claude Code: `claude mcp list`
  - Gemini: `gemini mcp list`
  - Codex: `codex mcp list`
- Aktif maç varsayılan olarak 2022 finalidir. Başka maç için önce `mac_bul`, sonra `mac_yukle`.
- `mkdir -p cikti workflows`

## 1. ANALİZ — Gemini

`--yolo` bayrağı tool çağrılarını onay beklemeden çalıştırır.

```bash
gemini --yolo -p "tt MCP tool'larını kullanarak Lionel Messi'nin 2022 Dünya Kupası finalindeki (Arjantin-Fransa) performansını analiz et: goller, şutlar, paslar, kilit anlar ve istatistikler. Sayıları tahmin etme, sadece tool çıktılarından al. Markdown olarak yaz." \
  > cikti/analiz.md 2> gemini_err.txt
```

- Ara sıra `503 UNAVAILABLE` (yoğunluk) hatası olur; Gemini kendi kendine tekrar dener.
- Dikkat: Gemini "60 başarılı pas" gibi abartı yazabilir. `oyuncu_istatistik` toplam pası verir, isabeti değil.

## 2. SENARYO — Claude

1. Tarz kurallarını çek: `bilgi_ara(soru="TT. kanalı anlatım tarzı kuralları kanca kapanış")` → `tt_tarz.txt`
2. Rakamları teyit et: `oyuncu_istatistik(oyuncu="Messi")`
3. `cikti/analiz.md` + kurallara göre `cikti/senaryo.md` yaz.

Senaryo kuralları:
- En fazla 35 saniye (~12-16 cümle, cümleler 4-10 kelime).
- Kanca önce, isim sonra: isim 2. ya da 3. cümlede tek başına.
- Kısa cümleler, tek kelimelik vurgu ("2022."), "..." ile gerilim.
- Rakamla kapanış.
- Art arda iki cümle aynı kalıpla (ör. ikisi de "-dı" ile) bitmesin.
- Aynı kelime (kök dahil) tekrar etmesin.
- Türk bağlantısı / "biz" dili; sadece tool'larla doğrulanabilecek rakamlar kullan.
- Sonda EKRAN GRAFİKLERİ ve sabit CTA bölümü.

## 3. DOĞRULAMA — Codex

`--approve-for-me` gerekli: `-s read-only` ile `en_cok_top_kapan` gibi bazı MCP çağrıları
"requires approval, but approval policy is never" hatasıyla düşer. (`--full-auto` bu sürümde yok.)

```bash
codex exec --approve-for-me --skip-git-repo-check -o cikti/dogrulama.md \
  "cikti/senaryo.md dosyasını oku. Senaryodaki (metin ve ekran grafikleri) her maç rakamını tt MCP tool'larıyla (oyuncu_istatistik, en_cok_top_kapan, mac_bul vb.; aktif maç 2022 Dünya Kupası finali) kontrol et. Tahmin etme, sadece tool çıktısına dayan. Süre/cümle sayısı gibi senaryo meta bilgilerini atla. Sonucu Türkçe markdown olarak ver: | İddia | Senaryodaki değer | Tool değeri | Kullanılan tool | Sonuç (DOĞRU/YANLIŞ/DOĞRULANAMADI) | tablosu ve altında kısa özet. Hiçbir dosyayı değiştirme." \
  < /dev/null > codex_log.txt 2>&1
```

- `-o` son mesajı dosyaya yazar. `< /dev/null` stdin beklemesini engeller.
- Hangi tool'ların çağrıldığını görmek için: `grep -E "^mcp" codex_log.txt`
- "DOĞRULANAMADI" çıkanlar (gol şekli, kaptanlık, stat adı) tool kapsamı dışında; yanlış sayılmaz.

## 4. DÜZELTME — Claude

`cikti/dogrulama.md` içinde **YANLIŞ** satır varsa ilgili rakamı tool değeriyle değiştir,
senaryo kurallarını (tekrar, kalıp, rakamla kapanış) yeniden kontrol et, sonra 3. adımı tekrar çalıştır.

Not: Penaltı atışları istatistiğe varsayılan olarak dahil değil (`penalti_atislari=false`).
Messi için dahil edilirse şut 6, gol 3 olur; senaryo resmi maç istatistiğini (5 şut, 2 gol) kullanır.

## 5. KAPAK — Claude + tt

```text
sut_haritasi(oyuncu="Messi")
→ cikti/lionel_andres_messi_cuccittini_sut_haritasi.png
```

```bash
cp cikti/lionel_andres_messi_cuccittini_sut_haritasi.png cikti/kapak.png
```

## Çıktılar

```
cikti/
├── analiz.md       # Gemini
├── senaryo.md      # Claude
├── dogrulama.md    # Codex
└── kapak.png       # tt sut_haritasi
```
