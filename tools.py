"""StatsBomb açık verisindeki maçlar için oyuncu analiz araçları.

Varsayılan aktif maç 2022 Dünya Kupası finalidir (Arjantin–Fransa);
mac_bul ile başka maç aranıp mac_yukle ile aktif maç değiştirilebilir.
"""
import unicodedata
import warnings
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ekran açmadan PNG üret
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import VerticalPitch
from statsbombpy import sb

warnings.filterwarnings("ignore")  # statsbombpy'nin "credentials" uyarısını gizle

FINAL_MATCH_ID = 3869685  # 2022 Dünya Kupası finali, Arjantin–Fransa
PENALTI_PERIYODU = 5      # StatsBomb'da penaltı atışları 5. periyot
CIKTI_DIR = Path(__file__).parent / "cikti"


MAC_BUL_MAKS_SEZON = 15   # mac_bul'un tek aramada tarayacağı en fazla turnuva-sezon
MAC_BUL_MAKS_SONUC = 25

_aktif_mac_id = FINAL_MATCH_ID
_mac_bilgileri: dict[int, dict] = {
    FINAL_MATCH_ID: {"match_id": FINAL_MATCH_ID, "tarih": "2022-12-18", "ev": "Argentina", "deplasman": "France",
                     "skor": "3-3 (pen. 4-2)", "asama": "Final", "turnuva": "FIFA World Cup", "sezon": "2022"},
}


@lru_cache(maxsize=8)
def _mac_olaylari(match_id: int) -> pd.DataFrame:
    """Maç olaylarını bir kez indirir, sonraki çağrılarda önbellekten döner."""
    return sb.events(match_id=match_id)


def _olaylar() -> pd.DataFrame:
    """Aktif maçın olayları."""
    return _mac_olaylari(_aktif_mac_id)


def _mac_etiketi() -> str:
    b = _mac_bilgileri.get(_aktif_mac_id)
    if not b:
        return f"maç {_aktif_mac_id}"
    return f"{b['ev']}–{b['deplasman']}, {b['turnuva']} {b['sezon']} {b['asama']}".strip()


def mac_bul(takim: str = "", turnuva: str = "", sezon: str = "") -> dict:
    """StatsBomb açık verisinde maç arar. En az turnuva ya da sezon verilmeli; takım ile daraltılabilir."""
    if not (turnuva or sezon):
        raise ValueError("En az 'turnuva' veya 'sezon' verin (örn. turnuva='World Cup', sezon='2022').")
    comps = sb.competitions()
    secili = comps[
        comps["competition_name"].map(lambda t: _sadelestir(turnuva) in _sadelestir(t))
        & comps["season_name"].map(lambda t: _sadelestir(sezon) in _sadelestir(t))
    ]
    if secili.empty:
        raise ValueError("Bu turnuva/sezon için açık veri yok. Örnek turnuvalar: "
                         + ", ".join(sorted(comps["competition_name"].unique())))
    if len(secili) > MAC_BUL_MAKS_SEZON:
        raise ValueError(f"{len(secili)} turnuva-sezon eşleşti; turnuva veya sezonu daha açık yazın.")

    maclar = []
    aranan = _sadelestir(takim)
    for _, c in secili.iterrows():
        df = sb.matches(competition_id=c["competition_id"], season_id=c["season_id"])
        if takim:
            df = df[df["home_team"].map(lambda t: aranan in _sadelestir(t))
                    | df["away_team"].map(lambda t: aranan in _sadelestir(t))]
        for _, m in df.iterrows():
            bilgi = {"match_id": int(m["match_id"]), "tarih": str(m["match_date"]),
                     "ev": m["home_team"], "deplasman": m["away_team"],
                     "skor": f"{m['home_score']}-{m['away_score']}", "asama": str(m.get("competition_stage", "")),
                     "turnuva": c["competition_name"], "sezon": c["season_name"]}
            _mac_bilgileri.setdefault(bilgi["match_id"], bilgi)
            maclar.append(bilgi)
    maclar.sort(key=lambda b: b["tarih"])
    return {"toplam": len(maclar), "maclar": maclar[:MAC_BUL_MAKS_SONUC],
            "not": "İlk sonuçlar gösteriliyor, aramayı daraltın." if len(maclar) > MAC_BUL_MAKS_SONUC else ""}


def mac_yukle(match_id: int) -> dict:
    """Maçın olaylarını indirir ve aktif maç yapar; diğer maç araçları artık bu maçı kullanır."""
    global _aktif_mac_id
    try:
        df = _mac_olaylari(int(match_id))
    except Exception as e:
        raise ValueError(f"{match_id} numaralı maçın olayları yüklenemedi: {e}") from e
    _aktif_mac_id = int(match_id)
    takimlar = sorted(df["team"].dropna().unique())
    goller = {t: 0 for t in takimlar}
    normal = df[df["period"] != PENALTI_PERIYODU]
    for t in normal.loc[(normal["type"] == "Shot") & (normal["shot_outcome"] == "Goal"), "team"]:
        goller[t] += 1
    for t in normal.loc[normal["type"] == "Own Goal For", "team"]:
        goller[t] += 1
    return {"match_id": _aktif_mac_id, "mac": _mac_etiketi(), "takimlar": takimlar,
            "gol_sayilari": goller, "olay_sayisi": len(df), "oyuncu_sayisi": int(df["player"].nunique()),
            "bilgi": _mac_bilgileri.get(_aktif_mac_id)}


def _sadelestir(metin: str) -> str:
    """Küçük harfe çevirir ve aksanları atar ('Mbappé' -> 'mbappe')."""
    ayrik = unicodedata.normalize("NFKD", metin)
    return "".join(c for c in ayrik if not unicodedata.combining(c)).casefold()


def _oyuncu_bul(oyuncu: str) -> str:
    """Kısmi isimden oyuncunun tam adını bulur. Bulamazsa ya da birden çok eşleşme varsa hata verir."""
    oyuncular = _olaylar()["player"].dropna().unique()
    aranan = _sadelestir(oyuncu)
    eslesen = sorted(p for p in oyuncular if aranan in _sadelestir(p))
    if not eslesen:
        raise ValueError(f"'{oyuncu}' adında aktif maçta ({_mac_etiketi()}) oynayan oyuncu bulunamadı.")
    if len(eslesen) > 1:
        raise ValueError(f"'{oyuncu}' birden fazla oyuncuyla eşleşti, daha açık yazın: {', '.join(eslesen)}")
    return eslesen[0]


def _takim_bul(takim: str) -> str:
    """Kısmi isimden takımın tam adını bulur. Bulamazsa ya da birden çok eşleşme varsa hata verir."""
    takimlar = _olaylar()["team"].dropna().unique()
    aranan = _sadelestir(takim)
    eslesen = sorted(t for t in takimlar if aranan in _sadelestir(t))
    if not eslesen:
        raise ValueError(f"'{takim}' adında aktif maçta oynayan takım bulunamadı. Takımlar: {', '.join(sorted(takimlar))}")
    if len(eslesen) > 1:
        raise ValueError(f"'{takim}' birden fazla takımla eşleşti, daha açık yazın: {', '.join(eslesen)}")
    return eslesen[0]


def en_cok_top_kapan(takim: str) -> dict:
    """Takımda en çok top kazanan 5 oyuncuyu döndürür (Ball Recovery + Interception olayları)."""
    ad = _takim_bul(takim)
    df = _olaylar()
    df = df[(df["team"] == ad) & df["type"].isin(["Ball Recovery", "Interception"])]
    sayilar = df.groupby("player").size().reset_index(name="sayi")
    sayilar = sayilar.sort_values(["sayi", "player"], ascending=[False, True]).head(5)
    return {
        "mac": _mac_etiketi(),
        "takim": ad,
        "oyuncular": [{"oyuncu": p, "top_kazanma": int(n)} for p, n in zip(sayilar["player"], sayilar["sayi"])],
    }


def _oyuncu_olaylari(oyuncu: str, penalti_atislari: bool) -> tuple[str, pd.DataFrame]:
    ad = _oyuncu_bul(oyuncu)
    df = _olaylar()
    df = df[df["player"] == ad]
    if not penalti_atislari:
        df = df[df["period"] != PENALTI_PERIYODU]
    return ad, df


def oyuncu_istatistik(oyuncu: str, penalti_atislari: bool = False) -> dict:
    """Oyuncunun aktif maçtaki pas, şut ve gol sayısını döndürür.

    Varsayılan olarak penaltı atışları sayılmaz (resmi maç istatistiği gibi);
    dahil etmek için penalti_atislari=True verin.
    """
    ad, df = _oyuncu_olaylari(oyuncu, penalti_atislari)
    sutlar = df[df["type"] == "Shot"]
    return {
        "mac": _mac_etiketi(),
        "oyuncu": ad,
        "takim": df["team"].iloc[0] if len(df) else None,
        "pas": int((df["type"] == "Pass").sum()),
        "sut": len(sutlar),
        "gol": int((sutlar["shot_outcome"] == "Goal").sum()),
    }


def sut_haritasi(oyuncu: str, penalti_atislari: bool = False) -> Path:
    """Oyuncunun şutlarını yarı saha üzerinde çizer ve cikti/ klasörüne PNG kaydeder.

    Nokta büyüklüğü xG'ye göre ölçeklenir; goller dolu, diğer şutlar boş çizilir.
    Kaydedilen dosyanın yolunu döndürür.
    """
    ad, df = _oyuncu_olaylari(oyuncu, penalti_atislari)
    sutlar = df[df["type"] == "Shot"]
    goller = sutlar[sutlar["shot_outcome"] == "Goal"]
    digerleri = sutlar[sutlar["shot_outcome"] != "Goal"]

    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#22312b", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(8, 7))

    for grup, dolgu, etiket in ((digerleri, "none", "Şut"), (goller, "#ffd166", "Gol")):
        if grup.empty:
            continue
        x = grup["location"].str[0]
        y = grup["location"].str[1]
        pitch.scatter(x, y, s=grup["shot_statsbomb_xg"] * 1500 + 80, ax=ax,
                      facecolors=dolgu, edgecolors="#ffd166", linewidths=2, alpha=0.9, label=etiket, zorder=2)

    toplam_xg = sutlar["shot_statsbomb_xg"].sum()
    ax.set_title(f"{ad} — {_mac_etiketi()}\n{len(sutlar)} şut, {len(goller)} gol, toplam xG {toplam_xg:.2f}",
                 color="white", fontsize=13)
    fig.set_facecolor("#22312b")
    if not sutlar.empty:
        lejant = ax.legend(loc="lower left", facecolor="#22312b", edgecolor="#c7d5cc", labelcolor="white")
        for isaret in lejant.legend_handles:  # lejanttaki noktaları xG'den bağımsız sabit boyutta göster
            isaret.set_sizes([150])

    CIKTI_DIR.mkdir(exist_ok=True)
    dosya_adi = _sadelestir(ad).replace(" ", "_") + "_sut_haritasi.png"
    if _aktif_mac_id != FINAL_MATCH_ID:  # finalin eski dosya adlarını koru
        dosya_adi = f"{_aktif_mac_id}_{dosya_adi}"
    yol = CIKTI_DIR / dosya_adi
    fig.savefig(yol, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return yol


if __name__ == "__main__":
    for isim in ("Messi", "Mbappe"):
        print(oyuncu_istatistik(isim))
        print(oyuncu_istatistik(isim, penalti_atislari=True))
        print(sut_haritasi(isim))
