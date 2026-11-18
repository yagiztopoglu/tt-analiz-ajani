"""Kurulum A (TEK MODEL): eval/sorular.csv'deki her soruyu `gemini --yolo -p` ile sorar.

Cevap ve süre eval/gemini_ham.json'a yazılır. Gemini CLI tt MCP sunucusunu
~/.gemini/settings.json üzerinden kullanır.
"""
import csv
import json
import shutil
import subprocess
import time
from pathlib import Path

EVAL = Path(__file__).parent
ISTEM = ("Bu soruyu tt MCP araçlarını kullanarak cevapla. "
         "2022 Dünya Kupası finali match_id 3869685, Euro 2024 finali match_id 3943043. "
         "Kısa cevap ver (tek cümle). Soru: {soru}")
# Not: istem tek satır olmalı. Windows'ta gemini.cmd üzerinden geçen argüman ilk satır sonunda
# kesiliyor; ilk denemede soru Gemini'ye hiç ulaşmadı.

gemini = shutil.which("gemini") or shutil.which("gemini.cmd")
sonuclar = []
with open(EVAL / "sorular.csv", encoding="utf-8") as f:
    for i, satir in enumerate(csv.DictReader(f), 1):
        bas = time.perf_counter()
        try:
            p = subprocess.run([gemini, "--yolo", "-p", ISTEM.format(soru=satir["soru"])],
                               capture_output=True, text=True, encoding="utf-8", timeout=300,
                               cwd=EVAL.parent)
            cevap, hata = p.stdout.strip(), (p.stderr.strip()[-500:] if p.returncode else "")
        except subprocess.TimeoutExpired:
            cevap, hata = "", "zaman aşımı (300 sn)"
        sure = round(time.perf_counter() - bas, 1)
        sonuclar.append({"no": i, "soru": satir["soru"], "cevap": cevap, "hata": hata, "sure_sn": sure})
        print(f"[{i}] {sure} sn | {cevap[:150]!r} {hata[:150]}", flush=True)
        (EVAL / "gemini_ham.json").write_text(json.dumps(sonuclar, ensure_ascii=False, indent=2), encoding="utf-8")
