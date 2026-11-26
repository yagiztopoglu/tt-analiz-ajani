# TT. Analiz Ajanı

## Amaç
TT. futbol kanalı için maç verisinden (StatsBomb açık verisi) analiz, şut haritası ve kanalın
anlatım tarzında kısa video senaryosu üreten ajan. Varsayılan maç: 2022 Dünya Kupası finali
(Arjantin–Fransa, match_id 3869685). Sayılar asla tahmin edilmez, sadece tool çıktısından alınır.

## Klasör yapısı
```
ajan.py             # Gemini tabanlı etkileşimli ajan (tool calling + RAG), giriş noktası
tools.py            # oyuncu_istatistik, sut_haritasi, en_cok_top_kapan fonksiyonları
rag.py              # bilgi/ klasörünü ChromaDB'ye indeksler, bilgi_ara
tt_mcp_server.py    # tt MCP sunucusu (tools.py + rag.py'yi MCP tool'u olarak açar)
veri.py             # StatsBomb'dan 2022 finalini çeken ilk deneme betiği
bilgi/              # RAG kaynakları: video_XX.txt transkriptleri, tt_tarz.txt, taktik_sozluk.txt
chroma/             # ChromaDB indeksi (üretilen, elle düzenlenmez)
cikti/              # tüm üretilen çıktılar: analiz.md, senaryo.md, dogrulama.md, *.png
workflows/          # çok modelli akışlar (video_hazirla.md)
.Codex/skills/     # mac-analiz, senaryo skill'leri
.Codex/agents/     # dogrulayici subagent'ı
```

## tt MCP tool'ları
| Tool | Ne yapar |
|---|---|
| `mac_bul(turnuva, sezon, takim)` | StatsBomb'da maç arar, match_id döndürür |
| `mac_yukle(match_id)` | Maçı aktif maç yapar (diğer maç tool'ları bunun üzerinde çalışır) |
| `oyuncu_istatistik(oyuncu, penalti_atislari=false)` | Pas, şut, gol sayısı |
| `sut_haritasi(oyuncu, penalti_atislari=false)` | Şut haritası PNG'sini `cikti/` altına kaydeder |
| `en_cok_top_kapan(takim)` | Takımda en çok top kazanan 5 oyuncu (takım adı İngilizce) |
| `bilgi_ara(soru, sonuc_sayisi=4)` | Kanal transkriptleri, tt_tarz.txt ve sözlükte anlamsal arama |

Notlar: Penaltı atışları varsayılan olarak hariç (resmi maç istatistiği). `oyuncu_istatistik`
toplam pası verir, isabetli pası değil. Veride olmayan bir şey (gol şekli, kaptanlık vb.) "kontrol edilemedi" sayılır.

## Kurallar
- **API key asla koda yazılmaz.** Anahtarlar sadece `.env`'de durur (`GEMINI_API_KEY`); `.env` commit edilmez, içeriği çıktıya/loga basılmaz.
- **Model adı `.env`'den okunur** (`GEMINI_MODEL`, `load_dotenv(override=True)`). Kodda model adı sabit yazılmaz.
- **Her değişiklikten sonra `ajan.py` test edilir:**
  1. `.venv/Scripts/python -c "import ajan"` (import/sözdizimi kontrolü, API isteği atmaz)
  2. `printf "Messi kaç gol attı?\nq\n" | .venv/Scripts/python ajan.py` (uçtan uca duman testi; ücretsiz katman günde ~20 istek, idareli kullan)
- **Codex sadece kısa doğrulama işinde kullanılır** (`codex exec` ile rakam kontrolü gibi). Kod yazma, refactor veya senaryo üretimi Codex'e verilmez.
- Tüm üretilen dosyalar `cikti/` klasörüne yazılır.
- Senaryo kuralları ve tam video akışı: `workflows/video_hazirla.md` (skill: `senaryo`).
