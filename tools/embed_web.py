#!/usr/bin/env python3
"""
embed_web.py — incorpora la pagina web nel firmware dell'ESP32.

Prende ogni file di `firmware/ld2410b_web/web/`, lo comprime in gzip e scrive
`firmware/ld2410b_web/web_assets.h`: un array PROGMEM per file più una tabella
(percorso, MIME, puntatore, lunghezza) che `web_server.h` registra come rotte HTTP.
Il server risponde con `Content-Encoding: gzip`, il browser decomprime da solo.

Perché così e non LittleFS: il plugin di upload del file system non esiste per
l'Arduino IDE 2.x. Con questo script basta un upload solo, nessuno strumento in più
(decisione del 05/09/2026, ANALISI_WEB_UI.md §4).

Uso (dalla radice del repo, con qualunque Python 3.8+, solo libreria standard):
    python tools/embed_web.py

⚠️ Da rilanciare a OGNI modifica di un file in web/, prima di compilare. Se te ne
dimentichi l'ESP32 serve la pagina vecchia: l'hash stampato qui compare anche in
`/info`, così si può controllare quale versione sta girando.
"""
import datetime
import gzip
import hashlib
import pathlib
import sys

RADICE = pathlib.Path(__file__).resolve().parents[1]
CARTELLA_WEB = RADICE / "firmware" / "ld2410b_web" / "web"
USCITA = RADICE / "firmware" / "ld2410b_web" / "web_assets.h"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}


def nome_c(percorso_rel: str) -> str:
    """'/chart.umd.min.js' -> 'ASSET_chart_umd_min_js'"""
    return "ASSET_" + "".join(c if c.isalnum() else "_" for c in percorso_rel.strip("/"))


def main() -> int:
    if not CARTELLA_WEB.is_dir():
        sys.exit(f"cartella non trovata: {CARTELLA_WEB}")

    file_web = sorted(p for p in CARTELLA_WEB.rglob("*") if p.is_file())
    if not file_web:
        sys.exit(f"nessun file in {CARTELLA_WEB}")

    righe = []
    tabella = []
    sha = hashlib.sha1()
    tot_chiaro = tot_gzip = 0

    righe.append("// GENERATO da tools/embed_web.py — NON modificare a mano, modificare i file in web/")
    righe.append(f"// {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    righe.append("#pragma once")
    righe.append("#include <Arduino.h>")
    righe.append("")
    righe.append("struct WebAsset {")
    righe.append("  const char*    path;   // rotta HTTP, es. \"/index.html\"")
    righe.append("  const char*    mime;   // Content-Type")
    righe.append("  const uint8_t* data;   // contenuto gzip, in flash")
    righe.append("  size_t         len;    // byte del gzip")
    righe.append("};")
    righe.append("")

    for p in file_web:
        rel = "/" + p.relative_to(CARTELLA_WEB).as_posix()
        mime = MIME.get(p.suffix.lower())
        if mime is None:
            sys.exit(f"estensione non prevista: {rel} (aggiungerla a MIME)")
        chiaro = p.read_bytes()
        sha.update(rel.encode())
        sha.update(chiaro)
        # mtime=0: stesso input -> stesso gzip -> header identico -> niente ricompilazioni inutili
        gz = gzip.compress(chiaro, compresslevel=9, mtime=0)
        tot_chiaro += len(chiaro)
        tot_gzip += len(gz)

        nome = nome_c(rel)
        righe.append(f"// {rel}: {len(chiaro)} byte in chiaro, {len(gz)} gzip")
        righe.append(f"static const uint8_t {nome}[] PROGMEM = {{")
        for i in range(0, len(gz), 16):
            righe.append("  " + ", ".join(f"0x{b:02x}" for b in gz[i:i + 16]) + ",")
        righe.append("};")
        righe.append("")
        tabella.append((rel, mime, nome, len(gz)))

    hash8 = sha.hexdigest()[:8]
    righe.append("static const WebAsset WEB_ASSETS[] = {")
    for rel, mime, nome, n in tabella:
        righe.append(f'  {{"{rel}", "{mime}", {nome}, {n}}},')
    righe.append("};")
    righe.append(f"static const size_t WEB_ASSETS_N = {len(tabella)};")
    righe.append(f'static const char WEB_ASSETS_HASH[] = "{hash8}";')
    righe.append("")

    nuovo = "\n".join(righe)
    # riscrive solo se il contenuto (esclusa la riga con la data) e' cambiato
    if USCITA.exists():
        vecchio = USCITA.read_text(encoding="utf-8").splitlines()
        if vecchio[2:] == righe[2:]:
            print(f"web_assets.h gia' aggiornato (hash {hash8}), nessuna modifica")
            return 0
    USCITA.write_text(nuovo, encoding="utf-8")

    print(f"{'file':28s} {'chiaro':>8s} {'gzip':>8s}")
    for rel, _, _, n in tabella:
        chiaro = (CARTELLA_WEB / rel.lstrip("/")).stat().st_size
        print(f"{rel:28s} {chiaro:8d} {n:8d}")
    print(f"{'totale':28s} {tot_chiaro:8d} {tot_gzip:8d}")
    print(f"scritto {USCITA.relative_to(RADICE)}  hash {hash8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
