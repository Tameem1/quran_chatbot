#!/usr/bin/env python3
"""
Stage 1 – **Data ingestion & cleaning** for the Quranic Chatbot – **JSONL output**

Datasets handled
----------------
1. **Quran Morphology** text file (Buckwalter TSV).
2. **root_analysis.xlsx** (roots + nuances).
3. **Lisān al‑ʿArab** dump – **plain‑text** file(s) from the OSINTAI GitHub repo (`*.txt`).

Output: three newline‑delimited JSON files under `./clean_data` (change with `--outdir`).
• `quran_morphology.jsonl`
• `root_analysis.jsonl`
• `lisan_alarab.jsonl`
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import pandas as pd

# ───────────────────────────────── helpers ──────────────────────────────────
ARABIC_LETTERS = "\u0621-\u064A"
DIACRITICS_RGX = re.compile(r"[\u064B-\u0652]")  # short vowels


def strip_diacritics(text: str) -> str:
    """Remove short vowels for normalised keys."""
    return DIACRITICS_RGX.sub("", text or "")

# ───────────────────────────── Quran Morphology ─────────────────────────────

def parse_morphology(file_path: Path) -> pd.DataFrame:
    """Convert Buckwalter‑style TSV into a tidy DataFrame."""
    records: list[dict] = []
    with file_path.open(encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln:
                continue
            ref, token, pos, feats = ln.split("\t", 3)
            s, a, w, t = map(int, ref.split(":"))
            records.append(
                {
                    "surah": s,
                    "ayah": a,
                    "word_index": w,
                    "token_index": t,
                    "token": token,
                    "pos": pos,
                    "features": feats,
                    "root": (m := re.search(r"ROOT:([^|]+)", feats)) and m.group(1),
                    "lemma": (m := re.search(r"LEM:([^|]+)", feats)) and m.group(1),
                }
            )
    return pd.DataFrame(records)

# ───────────────────────────── root_analysis.xlsx ───────────────────────────

def parse_root_analysis(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    df.rename(columns=lambda c: c.strip(), inplace=True)
    if "root" not in df.columns:
        raise ValueError("Expected a 'root' column in root_analysis.xlsx")
    df["root_stripped"] = df["root"].astype(str).apply(strip_diacritics)
    return df

# ─────────────────────────── Lisān al‑ʿArab (txt) ───────────────────────────
ROOT_HEADER_RGX = re.compile(fr"^([{ARABIC_LETTERS}\u064B-\u0652]{{1,10}})[:\u061B]$")


def parse_lisan_txt(txt_paths: list[Path]) -> pd.DataFrame:
    """Parse Lisān al‑ʿArab plain‑text dumps.

    Assumptions
    ===========
    • Each lexical root starts on a **line that ends with a colon (:)** and contains only the root word.
      e.g. "أَبَأَ:" or "أتأ:" etc.
    • Content continues until the next such header line or EOF.
    • Non‑lexical headings like "الجزء الأول" or "فصل الهمزة" lack the trailing colon → ignored.
    """
    entries: list[dict] = []
    for txt_path in txt_paths:
        with txt_path.open(encoding="utf-8") as f:
            current_root: str | None = None
            buffer: list[str] = []
            for line in f:
                stripped = line.rstrip("\n")
                # header detection
                if (m := ROOT_HEADER_RGX.match(stripped)):
                    # flush previous entry
                    if current_root and buffer:
                        entries.append(
                            {
                                "root": strip_diacritics(current_root),
                                "root_raw": current_root,
                                "entry": "\n".join(buffer).strip(),
                                "source_file": txt_path.name,
                            }
                        )
                    current_root = m.group(1)
                    buffer = []
                else:
                    if current_root:  # inside an entry
                        buffer.append(stripped)
            # flush last entry of the file
            if current_root and buffer:
                entries.append(
                    {
                        "root": strip_diacritics(current_root),
                        "root_raw": current_root,
                        "entry": "\n".join(buffer).strip(),
                        "source_file": txt_path.name,
                    }
                )
    return pd.DataFrame(entries)

# ────────────────────────────── I/O helpers ────────────────────────────────

def save_jsonl(df: pd.DataFrame, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(out_path, orient="records", lines=True, force_ascii=False)

# ──────────────────────────────── main CLI ─────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Stage 1 – data ingestion & cleaning (JSONL output)")
    p.add_argument("--morphology", required=True, type=Path, help="path to quran_morphology.txt")
    p.add_argument("--roots", required=True, type=Path, help="path to root_analysis.xlsx")
    p.add_argument(
        "--lisan_txt",
        required=True,
        type=Path,
        nargs="+",
        help="one or more Lisān al‑ʿArab *.txt files from the OSINTAI repo",
    )
    p.add_argument(
        "--outdir", default=Path("clean_data"), type=Path, help="directory for the generated *.jsonl files"
    )
    args = p.parse_args()

    print("⏳ Parsing Quran morphology …")
    morph_df = parse_morphology(args.morphology)
    save_jsonl(morph_df, args.outdir / "quran_morphology.jsonl")

    print("⏳ Parsing root_analysis.xlsx …")
    roots_df = parse_root_analysis(args.roots)
    save_jsonl(roots_df, args.outdir / "root_analysis.jsonl")

    print("⏳ Parsing Lisān al‑ʿArab dumps …")
    lisan_df = parse_lisan_txt(args.lisan_txt)
    save_jsonl(lisan_df, args.outdir / "lisan_alarab.jsonl")

    print("✅ Done. Rows saved:")
    print(
        f" • morphology: {morph_df.shape[0]}\n"
        f" • root_analysis: {roots_df.shape[0]}\n"
        f" • lisān al‑ʿarab entries: {lisan_df.shape[0]}"
    )


if __name__ == "__main__":
    main()
