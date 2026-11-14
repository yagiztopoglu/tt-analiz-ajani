"""2022 Dünya Kupası finali için Gemini tabanlı futbol analiz ajanı.

Kullanım:  python ajan.py
.env dosyasında GEMINI_API_KEY ve GEMINI_MODEL olmalı.
"""
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import rag
import tools

load_dotenv(override=True)  # .env, kabukta kalmış eski değişkenleri ezsin

MODEL = os.getenv("GEMINI_MODEL", "").strip()
MAX_TOOL_TURU = 10  # modelin tek soruda sonsuz tool döngüsüne girmesini engeller

SISTEM_TALIMATI = """Sen TT. futbol kanalı için çalışan bir analiz ve senaryo asistanısın.
İki bilgi kaynağın var:
1) Maç araçları (oyuncu_istatistik, sut_haritasi, en_cok_top_kapan): StatsBomb açık verisiyle sadece 2022 FIFA Dünya Kupası finalini (Arjantin–Fransa, 18 Aralık 2022) kapsar.
2) bilgi_ara: kanalın video metinleri, anlatım tarzı (tt_tarz.txt) ve taktik sözlüğü.
Herhangi bir oyuncu veya konu hakkında senaryo yazabilirsin; finalde oynamamış oyuncular için maç araçlarını kullanma,
elinde kaynak olmayan rakamları uydurma (gerekirse rakamı [kontrol et] diye işaretle).
- Oyuncu istatistikleri için oyuncu_istatistik, şut haritası için sut_haritasi aracını kullan. Sayıları asla tahmin etme.
- Oyuncu adını kullanıcının yazdığı gibi (kısmi) gönder; araç tam adı kendisi bulur.
- Araç birden fazla oyuncu eşleştiğini söylerse kullanıcıya hangisini kastettiğini sor.
- Varsayılan olarak penaltı atışları dahil edilmez; kullanıcı penaltıları isterse penalti_atislari=true ver.
- Bir takımda en çok top kazananlar için en_cok_top_kapan aracını kullan. Takım adını İngilizce gönder (Argentina, France).
- Şut haritası üretince kaydedilen dosya yolunu kullanıcıya söyle.
- TT. kanalı, videoları, anlatım tarzı veya futbol terimleri hakkındaki sorularda bilgi_ara aracıyla bilgi/ klasöründe ara; bulduğun bilgiye dayan, uydurma.
- Senaryo/video metni istenirse yazmaya başlamadan önce MUTLAKA iki ayrı bilgi_ara çağrısı yap:
  1) "TT. kanalı anlatım tarzı" -> tt_tarz.txt'yi bul (sonuçlarda yoksa farklı kelimelerle tekrar ara).
  2) Konuya özgü bir arama (örn. "genç oyuncunun büyük kulübe yükselişi", "oyuncu istatistik karşılaştırması") -> benzer video_XX.txt dosyalarını bul.
  Metni tt_tarz.txt'deki kurallara (kanca, isim 2.-3. cümlede, kısa cümleler, rakamla final) ve benzer videoların ritmine uygun yaz;
  videolardaki cümleleri kopyalama.
  Gerekiyorsa sayıları maç araçlarından al, rakam uydurma.
- bilgi_ara kullandıysan cevabın en sonuna "Kullanılan dosyalar:" başlığıyla gerçekten yararlandığın dosya adlarını madde madde listele.
- Kullanıcıya Türkçe yanıt ver."""

# Model adına göre çağrılacak Python fonksiyonları
ARACLAR = {
    "oyuncu_istatistik": tools.oyuncu_istatistik,
    "sut_haritasi": tools.sut_haritasi,
    "en_cok_top_kapan": tools.en_cok_top_kapan,
    "bilgi_ara": rag.bilgi_ara,
}

# Araç şemaları: açık yazıyoruz ki Path gibi dönüş tipleri şema üretimini bozmasın
_OYUNCU = types.Schema(type="STRING", description="Oyuncu adı veya adının bir kısmı, örn. 'Messi', 'Mbappe'.")
_PENALTI = types.Schema(type="BOOLEAN", description="Penaltı atışlarını (5. periyot) dahil et. Varsayılan false.")
ARAC_TANIMLARI = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="oyuncu_istatistik",
        description="Oyuncunun 2022 Dünya Kupası finalindeki pas, şut ve gol sayısını döndürür.",
        parameters=types.Schema(type="OBJECT", properties={"oyuncu": _OYUNCU, "penalti_atislari": _PENALTI},
                                required=["oyuncu"]),
    ),
    types.FunctionDeclaration(
        name="sut_haritasi",
        description="Oyuncunun finaldeki şutlarını saha üzerinde çizer, PNG olarak cikti/ klasörüne kaydeder ve dosya yolunu döndürür.",
        parameters=types.Schema(type="OBJECT", properties={"oyuncu": _OYUNCU, "penalti_atislari": _PENALTI},
                                required=["oyuncu"]),
    ),
    types.FunctionDeclaration(
        name="en_cok_top_kapan",
        description="Takımda finalde en çok top kazanan (Ball Recovery + Interception) 5 oyuncuyu sayılarıyla döndürür.",
        parameters=types.Schema(type="OBJECT", properties={
            "takim": types.Schema(type="STRING", description="İngilizce takım adı veya bir kısmı, örn. 'Argentina', 'Fran'."),
        }, required=["takim"]),
    ),
    types.FunctionDeclaration(
        name="bilgi_ara",
        description="bilgi/ klasöründeki TT. kanalı belgelerinde (video metinleri, anlatım tarzı, taktik sözlüğü) "
                    "anlamsal arama yapar; en alakalı 4 parçayı dosya adlarıyla döndürür.",
        parameters=types.Schema(type="OBJECT", properties={
            "soru": types.Schema(type="STRING", description="Aranacak konu veya soru, örn. 'Arda Güler istatistik videosu'."),
        }, required=["soru"]),
    ),
])


def arac_calistir(cagri: types.FunctionCall) -> dict:
    """Modelin istediği aracı çalıştırır; hatayı da modele sonuç olarak geri verir."""
    args = dict(cagri.args or {})
    parametreler = ", ".join(f"{k}={v!r}" for k, v in args.items())
    print(f"[TOOL] {cagri.name}({parametreler})")

    fonksiyon = ARACLAR.get(cagri.name)
    if fonksiyon is None:
        return {"hata": f"Bilinmeyen araç: {cagri.name}"}
    try:
        sonuc = fonksiyon(**args)
    except Exception as e:  # ör. oyuncu bulunamadı / birden fazla eşleşme
        print(f"[TOOL] -> hata: {e}")
        return {"hata": str(e)}
    sonuc = sonuc if isinstance(sonuc, dict) else {"sonuc": str(sonuc)}
    if cagri.name == "bilgi_ara":  # metinleri basma, sadece hangi parçalar geldi
        print("[TOOL] -> " + ", ".join(f"{r['dosya']}#{r['parca']} ({r['benzerlik']})" for r in sonuc["sonuclar"]))
    else:
        print(f"[TOOL] -> {sonuc}")
    return sonuc


def gonder(sohbet, icerik, deneme: int = 3):
    """Ara sıra görülen SSL/bağlantı hatalarında mesajı tekrar gönderir (geçmiş sadece başarıda eklenir)."""
    for k in range(deneme):
        try:
            return sohbet.send_message(icerik)
        except Exception as e:
            if "Connect" not in type(e).__name__ or k == deneme - 1:
                raise
            print(f"[AĞ] bağlantı hatası, tekrar deneniyor ({k + 1}/{deneme - 1})...")
            time.sleep(1 + k)


def soru_sor(sohbet, soru: str) -> str:
    """Soruyu gönderir; model araç istedikçe çalıştırıp sonucu geri yollar, son metni döndürür."""
    yanit = gonder(sohbet, soru)
    for _ in range(MAX_TOOL_TURU):
        if not yanit.function_calls:
            return yanit.text or ""
        sonuclar = [
            types.Part.from_function_response(name=c.name, response=arac_calistir(c))
            for c in yanit.function_calls
        ]
        yanit = gonder(sohbet, sonuclar)
    return "(Araç çağrısı sınırına ulaşıldı, yanıt tamamlanamadı.)"


def main() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit(".env dosyasında GEMINI_API_KEY bulunamadı.")
    if not MODEL:
        sys.exit(".env dosyasında GEMINI_MODEL bulunamadı.")

    # google-genai 3.x varsayılan olarak v1 kullanıyor; function calling sadece v1beta'da açık
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                          http_options=types.HttpOptions(api_version="v1beta"))
    sohbet = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SISTEM_TALIMATI,
            tools=[ARAC_TANIMLARI],
            # Araçları kendimiz çalıştırıyoruz ki her çağrıyı terminalde görebilelim
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    try:
        rag.indeksle()  # bilgi/ değiştiyse indeksi günceller
    except Exception as e:  # indeks kurulamazsa diğer araçlar yine çalışsın
        print(f"[RAG] indeks hazırlanamadı: {type(e).__name__}: {e}")

    print(f"TT. analiz ajanı ({MODEL}) — 2022 DK finali + kanal bilgisi. Çıkmak için 'q' yazın.\n")
    while True:
        try:
            soru = input("Soru> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if soru.lower() in {"q", "quit", "exit", "çık", "cik"}:
            break
        if not soru:
            continue
        try:
            print(f"\nAjan> {soru_sor(sohbet, soru)}\n")
        except Exception as e:  # ağ / API hataları döngüyü öldürmesin
            print(f"\n[HATA] {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()
