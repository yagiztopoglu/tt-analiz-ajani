"""2022 Dünya Kupası finali için Gemini tabanlı futbol analiz ajanı.

Kullanım:  python ajan.py
.env dosyasında GEMINI_API_KEY olmalı. İsteğe bağlı: GEMINI_MODEL (varsayılan gemini-2.5-flash).
"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_TURU = 10  # modelin tek soruda sonsuz tool döngüsüne girmesini engeller

SISTEM_TALIMATI = """Sen 2022 FIFA Dünya Kupası finali (Arjantin–Fransa, 18 Aralık 2022) üzerine çalışan bir futbol analiz asistanısın.
Veri kaynağın StatsBomb açık verisi; elindeki araçlar sadece bu maçı kapsar.
- Oyuncu istatistikleri için oyuncu_istatistik, şut haritası için sut_haritasi aracını kullan. Sayıları asla tahmin etme.
- Oyuncu adını kullanıcının yazdığı gibi (kısmi) gönder; araç tam adı kendisi bulur.
- Araç birden fazla oyuncu eşleştiğini söylerse kullanıcıya hangisini kastettiğini sor.
- Varsayılan olarak penaltı atışları dahil edilmez; kullanıcı penaltıları isterse penalti_atislari=true ver.
- Bir takımda en çok top kazananlar için en_cok_top_kapan aracını kullan. Takım adını İngilizce gönder (Argentina, France).
- Şut haritası üretince kaydedilen dosya yolunu kullanıcıya söyle.
- Kullanıcıya Türkçe yanıt ver."""

# Model adına göre çağrılacak Python fonksiyonları
ARACLAR = {
    "oyuncu_istatistik": tools.oyuncu_istatistik,
    "sut_haritasi": tools.sut_haritasi,
    "en_cok_top_kapan": tools.en_cok_top_kapan,
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
    print(f"[TOOL] -> {sonuc}")
    return sonuc


def soru_sor(sohbet, soru: str) -> str:
    """Soruyu gönderir; model araç istedikçe çalıştırıp sonucu geri yollar, son metni döndürür."""
    yanit = sohbet.send_message(soru)
    for _ in range(MAX_TOOL_TURU):
        if not yanit.function_calls:
            return yanit.text or ""
        sonuclar = [
            types.Part.from_function_response(name=c.name, response=arac_calistir(c))
            for c in yanit.function_calls
        ]
        yanit = sohbet.send_message(sonuclar)
    return "(Araç çağrısı sınırına ulaşıldı, yanıt tamamlanamadı.)"


def main() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit(".env dosyasında GEMINI_API_KEY bulunamadı.")

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

    print(f"Futbol analiz ajanı ({MODEL}) — 2022 DK finali. Çıkmak için 'q' yazın.\n")
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
