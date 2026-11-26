# Öğrendiklerim

## Gün 1 – Tool calling
**Ne kurdum:** Gemini'ye 3 tool verdim (oyuncu_istatistik, sut_haritasi, en_cok_top_kapan). Model hangi tool'u çağıracağına kendisi karar veriyor.
**Bitti testi – Tool calling nedir?:** 
**Yaşadığım sorun:** Ev ağım Gemini API'yi kesiyordu (SSL / connection reset). Windows curl ile test ettim, hotspot'ta çalıştı, sorunun ağda olduğunu buldum.

## Gün 2 – RAG
**Ne kurdum:** 8 videomun transkriptini, tarz kurallarımı ve sözlüğümü ChromaDB'ye koydum. Ajan senaryoyu benim tarzımda yazıyor ve kaynak gösteriyor.
**Bitti testi – Neden fine-tuning değil RAG?:** 
**Yaşadığım sorunlar:**
- Ücretsiz katman günde 20 istek. Ajan soru başına ~3 istek atıyor. Modeli .env'den okunur yaptım.
- Terminalde kalan eski bir ortam değişkeni .env'i eziyordu. Çözüm: load_dotenv(override=True).
## Gün 3 – MCP
**Ne kurdum:** tools.py ve rag.py'deki 6 tool'u (mac_bul, mac_yukle, oyuncu_istatistik, sut_haritasi, en_cok_top_kapan, bilgi_ara) FastMCP ile tek bir MCP server'a (tt_mcp_server.py) çevirdim. Bu server'ı "tt" adıyla Claude Code, Gemini CLI ve Codex CLI'a bağladım. Üç ajan da aynı soruda benim tool'larımı çağırıp aynı veriden cevap verdi.
**Bitti testi – MCP nedir, normal tool'dan farkı ne?:** Normal tool sadece yazıldığı programın içinde çalışır. MCP, tool'ları standart bir formatta paketliyor; bir kere server yazıyorum, farklı şirketlerin ajanları (Anthropic, Google, OpenAI) aynı server'a bağlanıp aynı tool'ları kullanıyor. Her ajan için ayrı entegrasyon yazmak gerekmiyor.
**Öğrendiğim ek şey:** Bu sefer beyin Gemini API değil, aboneliklerle çalışan CLI ajanları. Yani tool'larımı API limitine takılmadan kullanabiliyorum. Sadece bilgi_ara embedding için Gemini API'ye bağlanıyor.
## Gün 4 – Multi-LLM (şef–taşeron)
**Ne kurdum:** Claude Code'u şef yaptım. İşi bölüp terminal komutlarıyla diğer ajanlara dağıttı: analizi Gemini CLI (gemini -p), senaryoyu kendisi, rakam doğrulamasını Codex (codex exec) yaptı. Hepsi aynı tt MCP server'ındaki veriyi kullandı. Akışı workflows/video_hazirla.md'ye kaydettim.
**Bitti testi – Neden tek model yerine birden fazla model?:** Biri yazıp diğeri kontrol edince uydurma rakamlar yakalanıyor. Ayrıca her işi ona uygun ve limiti uygun modele verebiliyorum (Codex'in limiti düşük olduğu için sadece kısa doğrulama işi yaptı).
**Öğrendiğim ek şey:** PowerShell komut çalıştırır, Claude Code Türkçe talimat alır; ikisini karıştırmamak lazım.
## Gün 5 – CLAUDE.md, skills, subagent
**Ne kurdum:**
- CLAUDE.md: Claude Code'un her oturumda otomatik okuduğu proje kuralları (amaç, klasörler, tt tool'ları, "key koda yazılmaz", "model .env'den okunur" gibi kurallar).
- 2 skill: /mac-analiz (istatistik + şut haritası) ve /senaryo (Gün 4'teki tüm şef-taşeron akışı tek komutta).
- 1 subagent: dogrulayici. Tek işi senaryodaki rakamları tt tool'larıyla kontrol etmek, veride yoksa "kontrol edilemedi" demek.
**Bitti testi – CLAUDE.md ile skill farkı?:** CLAUDE.md her zaman okunan genel kurallar, işe giriş dosyası gibi. Skill ise sadece o iş istendiğinde açılan tarif kartı, böylece ajanın kafası gereksiz bilgiyle dolmuyor. Subagent da kendi talimatı ve temiz hafızası olan ayrı bir uzman.
**Kazancım:** Dün uzun bir mesajla yaptırdığım akışı artık "/senaryo Mbappe 2022 final" yazarak tek satırla çalıştırıyorum. Buna context engineering deniyor: modele doğru bilgiyi doğru anda vermek.
## Gün 6 – Eval
**Ne kurdum:** 12 soruluk sınav (6 kolay, 3 iki adımlı, 3 tuzak). İki kurulumu karşılaştırdım: tek başına Gemini CLI vs Gemini + doğrulayıcı subagent.
**Sonuç:** 11/12 → 12/12. Tek model bir tuzak soruda veride olmayan bir cevap uydurdu, doğrulayıcı yakaladı. Süre 17 sn → 31 sn.
**Bitti testi – Eval neden önemli?:** "Çalışıyor gibi görünüyor" ile "ölçtüm, şu kadar doğru" farklı şeyler. Bir şeyi değiştirdiğimde (model, prompt, doğrulayıcı) sınavı tekrar çalıştırıp iyileşti mi bozuldu mu görüyorum. Doğruluk ile hız/maliyet arasında takas olduğunu da rakamla gösterebiliyorum.