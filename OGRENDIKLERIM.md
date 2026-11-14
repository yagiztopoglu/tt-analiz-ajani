# Öğrendiklerim

## Gün 1 – Tool calling
**Ne kurdum:** Gemini'ye 3 tool verdim (oyuncu_istatistik, sut_haritasi, en_cok_top_kapan). Model hangi tool'u çağıracağına kendisi karar veriyor.
**Bitti testi – Tool calling nedir?:** (kendi cevabın)
**Yaşadığım sorun:** Ev ağım Gemini API'yi kesiyordu (SSL / connection reset). Windows curl ile test ettim, hotspot'ta çalıştı, sorunun ağda olduğunu buldum.

## Gün 2 – RAG
**Ne kurdum:** 8 videomun transkriptini, tarz kurallarımı ve sözlüğümü ChromaDB'ye koydum. Ajan senaryoyu benim tarzımda yazıyor ve kaynak gösteriyor.
**Bitti testi – Neden fine-tuning değil RAG?:** (kendi cevabın)
**Yaşadığım sorunlar:**
- Ücretsiz katman günde 20 istek. Ajan soru başına ~3 istek atıyor. Modeli .env'den okunur yaptım.
- Terminalde kalan eski bir ortam değişkeni .env'i eziyordu. Çözüm: load_dotenv(override=True).