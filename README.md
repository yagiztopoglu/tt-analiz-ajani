# TT. Analiz Ajanı

**Tek bir istekten veri analizi, grafik, 30 saniyelik video senaryosu ve doğrulama raporu üreten çok modelli (multi-LLM) içerik ajanı.**

"Messi'nin 2022 finalindeki performansını anlatan 30 saniyelik video hazırla" gibi bir isteği alır. Maç verisini sorgular, istatistik ve şut haritası çıkarır, senaryoyu benim kanal tarzımda yazar, senaryodaki her rakamı ikinci bir modele veriden kontrol ettirir.

Proje, LLM ajanlarının temel parçalarını (tool calling, RAG, MCP, çoklu model, eval) tek bir çalışan sistemde bir araya getirmek için yapıldı.

> Yeni bir model eğitilmedi. Hazır modeller (Gemini, Claude, Codex) kendi yazdığım araçlar, bilgi tabanı ve doğrulama adımıyla birleştirildi.

## Ne yapıyor?

```
İstek: "Messi 2022 final, 30 sn video"
   │
   ▼
1. ANALİZ      Gemini CLI  ──► tt MCP araçları: maçı bul, yükle, istatistik, şut haritası
   │
   ▼
2. SENARYO     Claude Code ──► bilgi_ara (RAG): tarz kuralları + örnek video metinleri
   │
   ▼
3. DOĞRULAMA   Codex / doğrulayıcı ajan ──► senaryodaki her rakamı veriden kontrol eder
   │
   ▼
4. ÇIKTI       cikti/  analiz.md · senaryo.md · dogrulama.md · kapak.png
```

Claude Code **şef** gibi çalışır: işi böler, `gemini -p` ve `codex exec` komutlarıyla diğer ajanlara iş verir, sonucu kontrol eder.

## Bileşenler

| Bileşen | Dosya | Ne yapar |
|---|---|---|
| Tool calling ajanı | `ajan.py` | Gemini API. Model soruya göre hangi aracı çağıracağına kendisi karar verir; çağrılar terminalde `[TOOL]` olarak görünür |
| Araçlar | `tools.py` | `mac_bul`, `mac_yukle`, `oyuncu_istatistik`, `sut_haritasi`, `en_cok_top_kapan` |
| RAG | `rag.py`, `bilgi/` | Video metinleri, tarz kuralları ve sözlük ChromaDB'de; `bilgi_ara` en ilgili parçaları kaynak dosyasıyla döndürür |
| MCP server | `tt_mcp_server.py` | 6 aracı FastMCP ile paketler; Claude Code, Gemini CLI ve Codex aynı server'a bağlanır |
| Proje kuralları | `CLAUDE.md` | Claude Code'un her oturumda okuduğu kurallar (anahtar koda yazılmaz, model `.env`'den okunur vb.) |
| Skill'ler | `.claude/skills/` | `/mac-analiz` ve `/senaryo`: tüm akışı tek komutla çalıştırır |
| Doğrulayıcı | `.claude/agents/dogrulayici.md` | Tek görevi rakam kontrolü; veride yoksa "kontrol edilemedi" der |
| Eval | `eval/` | Soru seti ve sonuçlar |

## Sonuçlar (eval)

12 soru: 6 kolay (şut, pas, gol), 3 iki adımlı, 3 tuzak (cevabı veride olmayan). Doğru cevaplar veriden hesaplandı.

| Kurulum | Doğruluk | Tuzak sorularda doğru | Ortalama süre |
|---|---|---|---|
| A) Tek model (Gemini CLI) | %92 (11/12) | %67 (2/3) | 17,2 sn |
| B) Gemini + doğrulayıcı ajan | %100 (12/12) | %100 (3/3) | 31,4 sn |

- Tek model, tuzak sorulardan birinde veride olmayan bir cevabı emin bir dille uydurdu; doğrulayıcı bunu yakaladı.
- Bedeli: yanıt süresi yaklaşık iki katına çıktı.
- **Test küçüktür (12 soru).** Fark tek bir soruya dayanıyor; sonuç "doğrulayıcı uydurmayı yakalayabiliyor" diye okunmalı, genel bir doğruluk iddiası olarak değil.

## Kurulum (Windows)

1. Python 3.11+ ve Node.js (LTS) kurun.
2. Sanal ortam ve paketler:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install google-genai statsbombpy pandas mplsoccer python-dotenv chromadb fastmcp
   ```
3. `.env` dosyası oluşturun (GitHub'a gönderilmez):
   ```
   GEMINI_API_KEY=anahtarınız
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```
   Anahtar: aistudio.google.com → Get API key.
4. Tek ajanı deneyin: `python ajan.py` → `Messi finalde kaç şut attı, haritasını da çiz`
5. Çoklu ajan akışı için Claude Code, Gemini CLI ve Codex CLI kurulu olmalı; `tt` MCP server'ı üçüne de eklenir (komutlar `CLAUDE.md` içinde). Sonra Claude Code'da: `/senaryo Mbappe 2022 final`

## Klasör yapısı

```
tt-analiz-ajani/
├── ajan.py                 Gemini API ile tool calling ajanı
├── tools.py                Maç verisi araçları
├── rag.py                  Bilgi tabanı (ChromaDB + embedding)
├── tt_mcp_server.py        Araçları paylaşan MCP server
├── bilgi/                  Video metinleri, tarz kuralları, sözlük
├── workflows/              Şef–taşeron akışının adımları
├── eval/                   Soru seti ve sonuçlar
├── cikti/                  Üretilen senaryo, rapor ve grafikler
├── CLAUDE.md               Ajan için proje kuralları
├── .claude/skills/         /mac-analiz, /senaryo
├── .claude/agents/         dogrulayici
└── OGRENDIKLERIM.md        Her adımda öğrendiklerim ve karşılaştığım sorunlar
```

## Karşılaşılan sorunlar ve çözümler

- **Ağ engeli:** Ev ağı Gemini API'ye giden bağlantıyı kesiyordu (`SSL` / `connection reset`). Windows `curl` ile testte sorunun kodda değil ağda olduğu bulundu; mobil bağlantı ve tünel (WARP) ile aşıldı.
- **Ücretsiz katman limiti:** Model başına günde 20 istek. Ajan bir soru için ortalama 3 istek atıyor. Model adı `.env`'den okunur hale getirildi; eval ve çoklu ajan akışı, abonelikle çalışan CLI araçlarına taşındı.
- **Eskiyen model adı:** Bir model yeni kullanıcılara kapatıldı; hata mesajındaki öneriyle güncellendi.
- **Ortam değişkeni çakışması:** Terminalde kalan eski bir değişken `.env`'i eziyordu; `load_dotenv(override=True)` ile çözüldü.

## Veri ve lisans

- Maç verisi: **StatsBomb Open Data** (github.com/statsbomb/open-data), `statsbombpy` ile çekilir. Kullanım ve atıf koşulları için StatsBomb'un açık veri sayfasına bakın.
- `bilgi/` klasöründeki video metinleri ve tarz kuralları bana aittir.

## Sınırlılıklar

- Eval küçük (12 soru); sonuçlar başka sorularda farklı çıkabilir.
- Açık veri bir arşivdir: güncel sezonlar ve Süper Lig yoktur.
- Ücretsiz API limiti nedeniyle `ajan.py` günde sınırlı sayıda soru cevaplayabilir.
- Doğrulayıcı yalnızca rakamları kontrol eder; senaryonun yorumunu ve üslubunu doğrulamaz.
- Resim üretimi (görsel model) ücretsiz katmanda olmadığı için kapak görseli veri grafiğinden üretilir.
