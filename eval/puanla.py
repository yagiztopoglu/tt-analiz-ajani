"""A (Gemini tek model) ve B (Gemini + dogrulayici) cevaplarını puanlar.

Girdi: eval/sorular.csv, eval/gemini_ham.json (calistir_gemini.py çıktısı).
B cevapları ve dogrulayici süreleri Claude Code oturumunda dogrulayici subagent'ından
alındı (her soru için ayrı çağrı, `NİHAİ CEVAP` satırı ve harness'in duration_ms değeri).
Çıktı: eval/sonuclar.csv ve özet tablo (stdout).
"""
import csv
import json
import re
from pathlib import Path

EVAL = Path(__file__).parent
YOK = re.compile(r"veride yok|bilinmiyor|mevcut değil|yer almamakta|bulunmamakta", re.I)

# soru no -> (dogrulayici NİHAİ CEVAP, dogrulayici süresi sn, not)
B = {
    1: ("2", 11.1, ""),
    2: ("6", 10.6, ""),
    3: ("29", 11.1, ""),
    4: ("36", 15.9, "paralel çalışmada aktif maç 2022 finaline döndü; yeniden mac_yukle"),
    5: ("3", 15.8, "paralel çalışmada aktif maç 2022 finaline döndü; yeniden mac_yukle"),
    6: ("1", 16.4, "paralel çalışmada aktif maç 2022 finaline döndü; yeniden mac_yukle"),
    7: ("69", 12.1, ""),
    8: ("2", 16.7, "paralel çalışmada aktif maç 2022 finaline döndü; yeniden mac_yukle"),
    9: ("3", 17.7, "paralel çalışmada aktif maç 2022 finaline döndü; yeniden mac_yukle"),
    10: ("veride yok / bilinmiyor", 9.9, "A'nın kaptanlık iddiası KONTROL EDİLEMEDİ → düzeltildi"),
    11: ("veride yok / bilinmiyor", 18.6, "ilk mac_yukle çıktısı karışık (iki maç); yeniden yüklendi"),
    12: ("veride yok / bilinmiyor", 14.0, "mac_yukle çıktısı karışık (iki maç) geldi; cevap etkilenmedi"),
}


def dogru_mu(cevap: str, dogru: str, tur: str) -> bool:
    if tur == "tuzak":
        return bool(YOK.search(cevap)) and not cevap.lower().startswith("evet")
    sayi = re.match(r"\d+", dogru).group()
    return re.search(rf"(?<!\d){sayi}(?!\d)", cevap) is not None


sorular = list(csv.DictReader(open(EVAL / "sorular.csv", encoding="utf-8")))
a_ham = {r["no"]: r for r in json.load(open(EVAL / "gemini_ham.json", encoding="utf-8"))}

satirlar = []
for no, s in enumerate(sorular, 1):
    a = a_ham[no]
    b_cevap, b_dog_sure, b_not = B[no]
    satirlar.append({
        "no": no, "tur": s["tur"], "soru": s["soru"], "dogru_cevap": s["dogru_cevap"],
        "A_cevap": a["cevap"], "A_dogru": "doğru" if dogru_mu(a["cevap"], s["dogru_cevap"], s["tur"]) else "yanlış",
        "A_sure_sn": a["sure_sn"],
        "B_cevap": b_cevap, "B_dogru": "doğru" if dogru_mu(b_cevap, s["dogru_cevap"], s["tur"]) else "yanlış",
        "B_sure_sn": round(a["sure_sn"] + b_dog_sure, 1),  # B = Gemini cevabı + doğrulama
        "B_dogrulayici_sn": b_dog_sure, "not": b_not,
    })

with open(EVAL / "sonuclar.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(satirlar[0]))
    w.writeheader()
    w.writerows(satirlar)

print("| kurulum | doğruluk % | tuzak sorularda doğru % | ortalama süre (sn) |")
print("|---|---|---|---|")
for k, ad in (("A", "A) Tek model (Gemini CLI)"), ("B", "B) Gemini + dogrulayici")):
    n = len(satirlar)
    tuzak = [r for r in satirlar if r["tur"] == "tuzak"]
    dog = sum(r[f"{k}_dogru"] == "doğru" for r in satirlar)
    tdog = sum(r[f"{k}_dogru"] == "doğru" for r in tuzak)
    ort = sum(r[f"{k}_sure_sn"] for r in satirlar) / n
    print(f"| {ad} | {100*dog/n:.0f}% ({dog}/{n}) | {100*tdog/len(tuzak):.0f}% ({tdog}/{len(tuzak)}) | {ort:.1f} |")
