"""bilgi/ klasöründeki .txt dosyaları üzerinde RAG: parçala -> Gemini embedding -> ChromaDB.

Kullanım:
    python rag.py                 # indeksi (gerekirse) kurar
    python rag.py "Arda Güler"    # indeksi kurar ve arama yapar
    python rag.py --yeniden       # indeksi sıfırdan kurar
İndeks proje içindeki chroma/ klasörüne kalıcı olarak kaydedilir.
"""
import hashlib
import os
import sys
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)  # .env, kabukta kalmış eski değişkenleri ezsin

KOK = Path(__file__).parent
BILGI_DIR = KOK / "bilgi"
CHROMA_DIR = KOK / "chroma"
KOLEKSIYON = "bilgi"
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
PARCA_KELIME = 400
SONUC_SAYISI = 4
EMBED_BATCH = 50  # tek istekte gönderilecek metin sayısı

_client: genai.Client | None = None
_koleksiyon = None


def _gemini() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _embed_istek(parti: list[str], gorev: str, deneme: int = 3):
    """Ara sıra görülen SSL/bağlantı hatalarında istemciyi yenileyip tekrar dener."""
    global _client
    for k in range(deneme):
        try:
            return _gemini().models.embed_content(
                model=EMBED_MODEL, contents=parti,
                config=types.EmbedContentConfig(task_type=gorev),
            )
        except Exception as e:
            if "Connect" not in type(e).__name__ or k == deneme - 1:
                raise
            print(f"[RAG] bağlantı hatası ({e}), tekrar deneniyor...")
            _client = None
            time.sleep(1 + k)


def _embed(metinler: list[str], gorev: str) -> list[list[float]]:
    vektorler = []
    for i in range(0, len(metinler), EMBED_BATCH):
        yanit = _embed_istek(metinler[i:i + EMBED_BATCH], gorev)
        vektorler.extend(e.values for e in yanit.embeddings)
    return vektorler


def _video_mu(dosya: Path) -> bool:
    return dosya.stem.lower().startswith("video")


def _kelimelere_bol(metin: str, boyut: int) -> list[str]:
    kelimeler = metin.split()
    return [" ".join(kelimeler[i:i + boyut]) for i in range(0, len(kelimeler), boyut)]


def parcala(metin: str, boyut: int = PARCA_KELIME) -> list[str]:
    """Metni paragraf sınırlarını koruyarak ~boyut kelimelik parçalara ayırır."""
    parcalar, mevcut, sayac = [], [], 0
    for paragraf in (p.strip() for p in metin.split("\n\n")):
        if not paragraf:
            continue
        n = len(paragraf.split())
        if n > boyut:  # tek başına çok uzun paragraf: kelimeden böl
            if mevcut:
                parcalar.append("\n\n".join(mevcut))
                mevcut, sayac = [], 0
            parcalar.extend(_kelimelere_bol(paragraf, boyut))
            continue
        if sayac + n > boyut and mevcut:
            parcalar.append("\n\n".join(mevcut))
            mevcut, sayac = [], 0
        mevcut.append(paragraf)
        sayac += n
    if mevcut:
        parcalar.append("\n\n".join(mevcut))
    return parcalar


def _dosyalar() -> list[Path]:
    return sorted(BILGI_DIR.glob("*.txt"))


def _parmak_izi(dosyalar: list[Path]) -> str:
    """Dosya adları + içerikleri değişince değişen özet; indeksi ne zaman yenileyeceğimizi söyler."""
    h = hashlib.sha256(f"{EMBED_MODEL}|{PARCA_KELIME}".encode())
    for d in dosyalar:
        h.update(d.name.encode())
        h.update(d.read_bytes())
    return h.hexdigest()


def indeksle(yeniden: bool = False):
    """bilgi/ değiştiyse (ya da yeniden=True) ChromaDB koleksiyonunu baştan kurar."""
    global _koleksiyon
    dosyalar = _dosyalar()
    iz = _parmak_izi(dosyalar)
    db = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if not yeniden:
        try:
            kol = db.get_collection(KOLEKSIYON)
            if (kol.metadata or {}).get("parmak_izi") == iz:
                _koleksiyon = kol
                return kol
        except Exception:
            pass  # koleksiyon yok

    ids, belgeler, metalar = [], [], []
    for d in dosyalar:
        metin = d.read_text(encoding="utf-8").strip()
        if not metin:
            continue
        parcalar = [metin] if _video_mu(d) else parcala(metin)
        for i, p in enumerate(parcalar):
            ids.append(f"{d.name}#{i}")
            belgeler.append(p)
            metalar.append({"dosya": d.name, "parca": i})

    # Önce embedding'leri al: API hata verirse eski indeks bozulmadan kalır,
    # boş koleksiyon "güncel" parmak iziyle kaydedilmez.
    vektorler = _embed(belgeler, "RETRIEVAL_DOCUMENT") if belgeler else []

    try:
        db.delete_collection(KOLEKSIYON)
    except Exception:
        pass
    kol = db.create_collection(KOLEKSIYON, metadata={"parmak_izi": iz, "hnsw:space": "cosine"})
    if belgeler:
        kol.add(ids=ids, documents=belgeler, metadatas=metalar, embeddings=vektorler)
    print(f"[RAG] {len(dosyalar)} dosya, {len(belgeler)} parça indekslendi -> {CHROMA_DIR}")
    _koleksiyon = kol
    return kol


def bilgi_ara(soru: str, sonuc_sayisi: int = SONUC_SAYISI) -> dict:
    """Soruya en alakalı parçaları dosya adlarıyla döndürür."""
    kol = _koleksiyon or indeksle()
    n = min(sonuc_sayisi, kol.count())
    if n == 0:
        return {"sonuclar": []}
    yanit = kol.query(query_embeddings=_embed([soru], "RETRIEVAL_QUERY"), n_results=n)
    return {"sonuclar": [
        {"dosya": m["dosya"], "parca": m["parca"], "benzerlik": round(1 - mesafe, 3), "metin": belge}
        for belge, m, mesafe in zip(yanit["documents"][0], yanit["metadatas"][0], yanit["distances"][0])
    ]}


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit(".env dosyasında GEMINI_API_KEY bulunamadı.")
    argumanlar = [a for a in sys.argv[1:] if a != "--yeniden"]
    indeksle(yeniden="--yeniden" in sys.argv)
    if argumanlar:
        for s in bilgi_ara(" ".join(argumanlar))["sonuclar"]:
            print(f"\n--- {s['dosya']} #{s['parca']} (benzerlik {s['benzerlik']}) ---\n{s['metin'][:300]}")
