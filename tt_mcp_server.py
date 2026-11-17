"""TT. analiz araçlarını (tools.py + rag.py) MCP server olarak sunar.

Çalıştırma (stdio):
    C:\\Users\\asi10\\tt-analiz-ajani\\.venv\\Scripts\\python.exe C:\\Users\\asi10\\tt-analiz-ajani\\tt_mcp_server.py
"""
import contextlib
import os
import sys
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field

KOK = Path(__file__).resolve().parent
os.chdir(KOK)                   # istemci server'ı hangi klasörden başlatırsa başlatsın
sys.path.insert(0, str(KOK))
load_dotenv(KOK / ".env", override=True)

from fastmcp import FastMCP  # noqa: E402

# tools/rag (pandas, matplotlib, chromadb, genai) ağır; ilk tool çağrısında yüklensin ki
# server istemcilerin başlangıç süre sınırına (Codex: 10 sn) takılmadan hemen açılsın.


def _tools():
    import tools
    return tools


def _rag():
    import rag
    return rag

mcp = FastMCP(
    "tt",
    instructions=(
        "TT. futbol kanalı analiz araçları. Maç araçları StatsBomb açık verisini kullanır; varsayılan aktif maç "
        "2022 Dünya Kupası finalidir (Arjantin–Fransa, 18 Aralık 2022). Başka maç için önce mac_bul, sonra mac_yukle. "
        "Kanalın video metinleri, anlatım tarzı ve taktik sözlüğü için bilgi_ara. Sayıları tahmin etme, araçlardan al."
    ),
)


@contextlib.contextmanager
def _stdout_korumasi():
    """stdio MCP'de stdout protokol kanalıdır; kütüphanelerin print'leri stderr'e gitsin."""
    with contextlib.redirect_stdout(sys.stderr):
        yield


Oyuncu = Annotated[str, Field(description="Oyuncu adı ya da adının bir kısmı, aksansız yazılabilir. Örn. 'Messi', 'Mbappe'.")]
Penalti = Annotated[bool, Field(description="Maç sonu penaltı atışlarını (5. periyot) dahil et. Varsayılan false: resmi maç istatistiği gibi.")]


@mcp.tool
def mac_bul(
    turnuva: Annotated[str, Field(description="Turnuva adı veya bir kısmı (İngilizce), örn. 'World Cup', 'Champions League', 'La Liga'.")] = "",
    sezon: Annotated[str, Field(description="Sezon, örn. '2022' veya '2015/2016'.")] = "",
    takim: Annotated[str, Field(description="Sonuçları bu takımın maçlarıyla sınırla (İngilizce ad veya bir kısmı), örn. 'Argentina'.")] = "",
) -> dict:
    """StatsBomb açık verisinde maç arar ve match_id, tarih, takımlar, skor, aşama bilgilerini döndürür.

    En az turnuva ya da sezon verilmelidir; takım ile daraltılabilir. En fazla 25 maç listelenir.
    Bulunan bir maçı analiz etmek için match_id'yi mac_yukle aracına ver.
    """
    with _stdout_korumasi():
        return _tools().mac_bul(takim=takim, turnuva=turnuva, sezon=sezon)


@mcp.tool
def mac_yukle(
    match_id: Annotated[int, Field(description="mac_bul'dan gelen StatsBomb maç numarası. 2022 DK finali: 3869685.")],
) -> dict:
    """Verilen maçın olaylarını indirir ve onu aktif maç yapar.

    Bundan sonra oyuncu_istatistik, sut_haritasi ve en_cok_top_kapan bu maç üzerinde çalışır.
    Takımları, penaltı atışları hariç gol sayılarını, olay ve oyuncu sayısını döndürür.
    Server açıldığında aktif maç 2022 Dünya Kupası finalidir.
    """
    with _stdout_korumasi():
        return _tools().mac_yukle(match_id)


@mcp.tool
def oyuncu_istatistik(oyuncu: Oyuncu, penalti_atislari: Penalti = False) -> dict:
    """Oyuncunun aktif maçtaki pas, şut ve gol sayısını döndürür.

    Oyuncu adı kısmi yazılabilir; birden fazla oyuncu eşleşirse hata mesajı adayları listeler.
    """
    with _stdout_korumasi():
        return _tools().oyuncu_istatistik(oyuncu, penalti_atislari)


@mcp.tool
def sut_haritasi(oyuncu: Oyuncu, penalti_atislari: Penalti = False) -> dict:
    """Oyuncunun aktif maçtaki şutlarını yarı saha üzerinde çizip PNG olarak kaydeder ve dosya yolunu döndürür.

    Nokta büyüklüğü xG'ye göre ölçeklenir; goller dolu sarı, diğer şutlar boş çizilir.
    Dosya proje içindeki cikti/ klasörüne yazılır.
    """
    with _stdout_korumasi():
        yol = _tools().sut_haritasi(oyuncu, penalti_atislari)
    return {"dosya": str(Path(yol).resolve())}


@mcp.tool
def en_cok_top_kapan(
    takim: Annotated[str, Field(description="Aktif maçtaki takımın İngilizce adı veya bir kısmı, örn. 'Argentina', 'Fran'.")],
) -> dict:
    """Takımda aktif maçta en çok top kazanan 5 oyuncuyu sayılarıyla döndürür (Ball Recovery + Interception olayları)."""
    with _stdout_korumasi():
        return _tools().en_cok_top_kapan(takim)


@mcp.tool
def bilgi_ara(
    soru: Annotated[str, Field(description="Aranacak konu veya soru, örn. 'TT. kanalı anlatım tarzı', 'gegenpress nedir'.")],
    sonuc_sayisi: Annotated[int, Field(description="Döndürülecek parça sayısı (1-10).", ge=1, le=10)] = 4,
) -> dict:
    """TT. kanalının belgelerinde (video metinleri, anlatım tarzı tt_tarz.txt, taktik sözlüğü) anlamsal arama yapar.

    En alakalı metin parçalarını dosya adı, parça numarası ve benzerlik puanıyla döndürür.
    Senaryo yazmadan önce hem anlatım tarzını hem konuya benzer videoları aramak için kullan.
    """
    with _stdout_korumasi():
        return _rag().bilgi_ara(soru, sonuc_sayisi)


if __name__ == "__main__":
    mcp.run(show_banner=False)
