#!/usr/bin/env python3
"""
Esporta i dati della campagna sperimentale in un unico file Excel.

    python analisi/esporta_excel.py

Produce `analisi/dati_tesi.xlsx` con:
  - un foglio "tutti_i_trial" con una riga per ogni trial e tutte le metriche
    calcolate da analizza_test.py (e' il foglio da cui costruire tabelle pivot
    e grafici a mano in Excel);
  - un foglio per ciascuna figura della tesi, con i soli dati aggregati che quella
    figura mostra e un grafico Excel nativo gia' inserito, modificabile a mano.

I numeri sono identici a quelli di analisi/grafici_tesi.py: entrambi gli script
chiamano le stesse funzioni di analizza_test.py con le stesse convenzioni di
scarto del transitorio (20 s ordinari, 40 s sotto il banco, 120 s selettivita',
60 s stanza vuota).
"""
import sys
import statistics
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, ScatterChart, LineChart, Reference, Series
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent
DATI = RADICE / "HLK-LD2410x" / "data"
OUT = QUI / "dati_tesi.xlsx"

sys.path.insert(0, str(QUI))
from analizza_test import leggi_csv, analizza_file, impulsi_pir  # noqa: E402

INTESTAZIONE = Font(bold=True, color="FFFFFF")
SFONDO = PatternFill("solid", fgColor="1B6CA8")


def skip_per(scenario):
    """Transitorio da scartare, per nome di scenario. Riproduce le convenzioni del registro:
    20 s ordinari, 40 s sotto il banco (LD2410B), 120 s selettivita', 60 s a stanza vuota;
    per la campagna LD2420 (rilascio ~55 s) i trial da fermo usano 90 s (registro 06-09/09)."""
    s = scenario.lower()
    if s.startswith("sel_") or s.startswith("sel2420_"):
        return 120.0
    if s.startswith("sotto_banco"):
        return 40.0
    if s.startswith(("fermo2420", "banco2420", "micromovimenti2420")):
        return 90.0
    if s.startswith(("stanza_vuota", "vuoto2420", "notturna2420", "corridoio_vuoto")):
        return 60.0
    return 20.0


# File presenti in data/ che NON sono trial validi: senza questa lista finivano nel foglio
# maestro come misure (13/09/2026). Ogni voce e' (criterio sul nome, motivo). Il primo che
# combacia vince. I file restano nel repo e compaiono nel foglio "file_esclusi" con il motivo.
ESCLUSIONI = [
    (lambda n: "nonvalido" in n,                      "marcato NON VALIDO nel registro"),
    (lambda n: "congelato" in n,                      "radar muto: frame identici ripetuti (registro 10/09)"),
    (lambda n: n.startswith("ingresso2420_rumore"),   "modulo LD2420 in stato anomalo (registro 07/09)"),
    (lambda n: n.startswith("check2420"),             "controllo del fondo prima di acquisire, non un trial"),
    (lambda n: n.startswith("prova") or n.endswith("_prova") or "_prova_" in n,
                                                      "prova tecnica (parser, seriale, web UI), non un trial"),
    (lambda n: n.startswith("20260818_"),             "pilota/verifica del logger del 18/08, senza ground truth"),
    (lambda n: n[:1].isupper(),                       "sessione web UI (demo dell'indice a bordo): stimolo non controllato"),
    (lambda n: n.startswith("stanza_vuota_2420"),     "presenza ASCII inutilizzabile (registro 02/09)"),
    (lambda n: n.startswith("portata2420_altrazona"), "setup non confermato, prova non interpretata (registro 05/09)"),
    (lambda n: n.startswith("pir_jumper") or n.startswith("pir_verifica"),
                                                      "verifica del jumper H/L, non un trial"),
    (lambda n: "cartone_lastra" in n,                 "pannello flessibile: escluso dai risultati (registro 30/08)"),
]


def motivo_esclusione(stem):
    """None se il file e' un trial valido, altrimenti il motivo dell'esclusione."""
    for crit, motivo in ESCLUSIONI:
        if crit(stem):
            return motivo
    return None


def scrivi(ws, righe, titolo=None, nota=None):
    """Scrive un blocco di righe (la prima e' l'intestazione) e ritorna la riga finale."""
    r = 1
    if titolo:
        ws.cell(1, 1, titolo).font = Font(bold=True, size=12)
        r = 3
    r0 = r
    for i, riga in enumerate(righe):
        for j, v in enumerate(riga, start=1):
            c = ws.cell(r, j, v)
            if i == 0:
                c.font = INTESTAZIONE
                c.fill = SFONDO
                c.alignment = Alignment(horizontal="center", wrap_text=True)
        r += 1
    for j in range(1, len(righe[0]) + 1):
        larg = max(len(str(riga[j - 1])) for riga in righe) + 3
        ws.column_dimensions[get_column_letter(j)].width = min(max(larg, 10), 34)
    if nota:
        ws.cell(r + 1, 1, nota).font = Font(italic=True, size=9)
    return r0, r - 1


def media_dev(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return None, None
    return (round(statistics.mean(vals), 2),
            round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0)


def trial(pattern, skip=None):
    fs = sorted(DATI.glob(pattern))
    out = []
    for f in fs:
        sk = skip if skip is not None else skip_per(f.stem)
        r = analizza_file(str(f), salta_inizio_s=sk)
        if r:
            r["_skip_s"] = sk
            out.append(r)
    return out


# =============================================================== foglio maestro
COLONNE = ["file", "scenario", "trial", "gt", "gt_state", "_skip_s", "n_campioni",
           "durata_s", "radar_rate_%", "pir_rate_%", "radar_acc_%", "pir_acc_%",
           "fn_radar_%", "fn_pir_%", "fp_radar_eventi_h", "fp_pir_eventi_h",
           "mdist_media_cm", "mdist_dev_cm", "sdist_media_cm", "sdist_dev_cm",
           "menergy_media", "senergy_media", "dist_nominale_cm", "errore_cm",
           # "NON COLLEGATO" nei trial in cui il PIR non era cablato (logger LD2420):
           # in quelle righe tutte le colonne del PIR restano VUOTE di proposito.
           "pir_stato"]


def foglio_tutti(wb):
    ws = wb.create_sheet("tutti_i_trial")
    righe = [COLONNE]
    esclusi = []
    for f in sorted(DATI.glob("*.csv")):
        motivo = motivo_esclusione(f.stem)
        if motivo:
            esclusi.append([f.name, motivo])
            continue
        r = analizza_file(str(f), salta_inizio_s=skip_per(f.stem))
        if r:
            righe.append([r.get(c, "") for c in COLONNE])
    scrivi(ws, righe, None,
           "Una riga per trial VALIDO (i file esclusi, con il motivo, sono nel foglio "
           "'file_esclusi'). '_skip_s' e' il transitorio scartato: 20 s ordinari, "
           "40 s sotto il banco, 120 s selettivita', 60 s stanza vuota, 90 s trial da "
           "fermo del LD2420. "
           "I file con evento (ingresso_*, uscita_*) hanno tassi privi di senso qui: "
           "la ground truth cambia a meta' file. Vedi il foglio 06_latenze. "
           "Se 'pir_stato' dice NON COLLEGATO le colonne del PIR sono vuote perche' il "
           "sensore non era cablato: NON sono zeri misurati.")
    ws.freeze_panes = "A2"
    ws2 = wb.create_sheet("file_esclusi")
    scrivi(ws2, [["file", "motivo"]] + esclusi, None,
           "CSV presenti in data/ che NON sono trial validi e restano fuori dal foglio "
           "maestro. Il criterio e' nel codice (ESCLUSIONI in esporta_excel.py): un dato "
           "escluso va motivato alla sorgente, non in una nota a parte.")
    return len(righe) - 1


# =============================================================== fogli figura
def foglio_dose(wb):
    ws = wb.create_sheet("01_dose_risposta")
    cond = [("stanza vuota (nessuno)", "stanza_vuota_T01.csv", 60.0),
            ("persona immobile", "fermo_1m_H_T*.csv", 20.0),
            ("micro-movimenti", "micromovimenti_1m_H_T*.csv", 20.0),
            ("cammino sul posto", "movimento_1m_H_T*.csv", 20.0)]
    righe = [["condizione", "mmWave rilevato [%]", "PIR rilevato [%]",
              "dev.std PIR", "n trial"]]
    for nome, pat, sk in cond:
        ts = trial(pat, sk)
        mr, _ = media_dev([t["radar_rate_%"] for t in ts])
        mp, dp = media_dev([t["pir_rate_%"] for t in ts])
        righe.append([nome, mr, mp, dp, len(ts)])
    r0, r1 = scrivi(ws, righe, "Fig. 1 - Rilevamento in funzione della quantita' di movimento",
                    "Soggetto a 1 m, jumper H, stessa postura e stesso setup: fra le righe "
                    "cambia solo la quantita' di movimento.")
    ch = BarChart()
    ch.type = "col"
    ch.title = "Rilevamento vs quantita' di movimento (1 m, jumper H)"
    ch.y_axis.title = "tempo con presenza rilevata [%]"
    ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1))
    ch.height, ch.width = 9, 18
    ws.add_chart(ch, "G3")


def foglio_sotto_banco(wb):
    ws = wb.create_sheet("03_sotto_banco")
    righe = [["condizione", "mmWave rilevato [%]", "PIR rilevato [%]", "dev.std PIR", "n trial"]]
    for nome, pat in (("con micro-movimenti", "sotto_banco_movimenti_H_T*.csv"),
                      ("immobile", "sotto_banco_immobile_H_T*.csv")):
        ts = trial(pat, 40.0)
        mr, _ = media_dev([t["radar_rate_%"] for t in ts])
        mp, dp = media_dev([t["pir_rate_%"] for t in ts])
        righe.append([nome, mr, mp, dp, len(ts)])
    r0, r1 = scrivi(ws, righe, "Fig. 3 - Scenario DIPME: persona sotto il banco (~60 cm)",
                    "5 trial per condizione, jumper H, scartati i primi 40 s.")
    ch = BarChart()
    ch.type = "col"
    ch.title = "Sotto il banco: cio' che cambia e' solo il movimento"
    ch.y_axis.title = "tempo con presenza rilevata [%]"
    ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1))
    ch.height, ch.width = 9, 16
    ws.add_chart(ch, "G3")


def foglio_distanza(wb):
    ws = wb.create_sheet("04_distanza")
    righe = [["distanza reale [cm]", "misurata media [cm]", "dev.std fra trial [cm]",
              "dispersione entro trial [cm]", "errore [cm]", "errore relativo [%]"]]
    for d in (1, 2, 3, 4, 5):
        ts = trial(f"movimento_{d}m_T*.csv", 20.0)
        m, dv = media_dev([t["mdist_media_cm"] for t in ts])
        disp, _ = media_dev([t["mdist_dev_cm"] for t in ts])
        righe.append([d * 100, m, dv, disp, round(m - d * 100, 2),
                      round(100 * (m - d * 100) / (d * 100), 2)])
    r0, r1 = scrivi(ws, righe, "Fig. 4 - Accuratezza della distanza (canale moving)",
                    "5 trial per distanza. La retta di regressione sulle 5 medie e' "
                    "y = 1,0381 x - 1,32 cm con R2 = 0,99965: errore di scala +3,81 %, "
                    "offset ~0. L'errore RELATIVO non e' monotono: il massimo e' a 2 m.")
    ch = ScatterChart()
    ch.title = "Distanza misurata vs distanza reale"
    ch.x_axis.title = "distanza reale [cm]"
    ch.y_axis.title = "distanza misurata [cm]"
    ch.style = 13
    xs = Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1)
    ser = Series(Reference(ws, min_col=2, min_row=r0, max_row=r1), xs, title_from_data=True)
    ser.marker.symbol = "circle"
    ser.graphicalProperties.line.noFill = True
    ch.series.append(ser)
    ch.height, ch.width = 9, 16
    ws.add_chart(ch, "H3")


def foglio_energia(wb):
    ws = wb.create_sheet("05_energia_portata")
    righe = [["distanza reale [m]", "energia media canale moving [0-100]",
              "mmWave rilevato [%]", "PIR rilevato [%]", "dev.std PIR"]]
    for d in (1, 2, 3, 4, 5):
        ts = trial(f"movimento_{d}m_T*.csv", 20.0)
        en, _ = media_dev([t.get("menergy_media") for t in ts])
        mr, _ = media_dev([t["radar_rate_%"] for t in ts])
        mp, dp = media_dev([t["pir_rate_%"] for t in ts])
        righe.append([d, en, mr, mp, dp])
    r0, r1 = scrivi(ws, righe, "Fig. 5 - Energia del bersaglio e portata utile del PIR",
                    "Soggetto che cammina sul posto. Il decadimento dell'energia e' molto "
                    "piu' lento di 1/D^4: e' un valore normalizzato 0-100 con elaborazione "
                    "interna, non va letto con l'equazione del radar.")
    ch = LineChart()
    ch.title = "Energia del bersaglio e rilevamento PIR in funzione della distanza"
    ch.y_axis.title = "energia [0-100] / rilevamento [%]"
    ch.x_axis.title = "distanza reale [m]"
    ch.add_data(Reference(ws, min_col=2, max_col=4, min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1))
    ch.height, ch.width = 9, 17
    ws.add_chart(ch, "G3")


def foglio_latenze(wb):
    ws = wb.create_sheet("06_latenze")
    righe = [["trial", "latenza mmWave [s]", "latenza PIR [s]", "differenza radar-PIR [s]"]]
    lr, lp = [], []
    for f in sorted(DATI.glob("ingresso_T*.csv")):
        r = analizza_file(str(f), event_time_s=30.0)
        if r and isinstance(r.get("latenza_radar_s"), float) and isinstance(r.get("latenza_pir_s"), float):
            lr.append(r["latenza_radar_s"])
            lp.append(r["latenza_pir_s"])
            righe.append([r["trial"], r["latenza_radar_s"], r["latenza_pir_s"],
                          r["latenza_delta_s"]])
    mr, dr = media_dev(lr)
    mp, dp = media_dev(lp)
    md, dd = media_dev([a - b for a, b in zip(lr, lp)])
    righe.append(["MEDIA", mr, mp, md])
    righe.append(["DEV.STD", dr, dp, dd])
    r0, r1 = scrivi(ws, righe, "Fig. 6a - Latenza di rilevamento all'ingresso (evento a 30 s)",
                    "Le latenze ASSOLUTE (~5-6 s) contengono il tragitto di rientro e il tempo "
                    "di reazione all'annuncio: sono una latenza OPERATIVA, limite superiore di "
                    "quella del sensore. La grandezza pulita e' la differenza appaiata, dove "
                    "tragitto e reazione si cancellano.")
    ch = BarChart()
    ch.type = "col"
    ch.title = "Latenza di rilevamento, trial per trial"
    ch.y_axis.title = "latenza [s]"
    ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=r0, max_row=r1 - 2), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1 - 2))
    ch.height, ch.width = 9, 17
    ws.add_chart(ch, "G3")

    # blocco rilascio, sotto
    r = r1 + 4
    ws.cell(r, 1, "Fig. 6b - Latenza di rilascio all'uscita (evento a 30 s)").font = Font(bold=True, size=12)
    rr, rp = [], []
    intest = ["trial", "rilascio mmWave [s]", "rilascio PIR [s]",
              "riaccensioni mmWave", "riaccensioni PIR"]
    for j, v in enumerate(intest, start=1):
        c = ws.cell(r + 2, j, v)
        c.font = INTESTAZIONE
        c.fill = SFONDO
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    k = r + 3
    for f in sorted(DATI.glob("uscita_T*.csv")):
        res = analizza_file(str(f), release_time_s=30.0)
        if not res:
            continue
        ws.cell(k, 1, res["trial"])
        ws.cell(k, 2, res.get("rilascio_radar_s"))
        ws.cell(k, 3, res.get("rilascio_pir_s"))
        ws.cell(k, 4, res.get("riaccensioni_radar"))
        ws.cell(k, 5, res.get("riaccensioni_pir"))
        if isinstance(res.get("rilascio_radar_s"), float):
            rr.append(res["rilascio_radar_s"])
        if isinstance(res.get("rilascio_pir_s"), float):
            rp.append(res["rilascio_pir_s"])
        k += 1
    m1, d1 = media_dev(rr)
    m2, d2 = media_dev(rp)
    ws.cell(k, 1, "MEDIA").font = Font(bold=True)
    ws.cell(k, 2, m1)
    ws.cell(k, 3, m2)
    ws.cell(k + 1, 1, "DEV.STD").font = Font(bold=True)
    ws.cell(k + 1, 2, d1)
    ws.cell(k + 1, 3, d2)
    ws.cell(k + 3, 1, "Il timeout di presenza letto via UART e' 5 s, ma il radar ne impiega "
                      "~18 dall'uscita. Stimando ~9,5 s per uscire dal campo (il PIR si spegne "
                      "3,5 s dopo l'ultimo trigger), la coda propria del radar e' ~8,9 s.").font = Font(italic=True, size=9)


def foglio_impulsi(wb):
    ws = wb.create_sheet("07_impulsi_pir")

    def raccogli(patterns):
        comp, tron = [], []
        for pat in patterns:
            for f in sorted(DATI.glob(pat)):
                c, t = impulsi_pir(leggi_csv(str(f)), 20.0)
                comp += c
                tron += t
        return comp, tron

    L_c, _ = raccogli(["movimento_1m_T*.csv", "sotto_banco_movimenti_T*.csv"])
    H_c, H_t = raccogli(["movimento_1m_H_T*.csv", "sotto_banco_movimenti_H_T*.csv"])
    mL, dL = media_dev(L_c)
    mH, dH = media_dev(H_c)
    righe = [["modalita' jumper", "n impulsi completi", "durata media [s]", "dev.std [s]",
              "durata max [s]", "n troncati", "troncato piu' lungo [s]"],
             ["L (non ripetibile)", len(L_c), mL, dL, round(max(L_c), 2), 0, ""],
             ["H (repeat trigger)", len(H_c), mH, dH, round(max(H_c), 2), len(H_t),
              round(max(H_t), 1) if H_t else ""]]
    scrivi(ws, righe, "Fig. 7 - Struttura degli impulsi del PIR",
           "In L la durata e' fissa: 181 impulsi tutti fra 3,4 e 3,8 s, nessuno oltre 5 s. "
           "L'uscita e' un monostabile a durata fissa, non una misura di presenza: il PIR "
           "conta eventi. In H il ritrigger concatena gli impulsi, e i piu' lunghi vengono "
           "troncati dalla fine del trial (durata reale >= valore riportato).")
    # elenco completo delle durate, per chi vuole rifare l'istogramma in Excel
    c0 = 9
    ws.cell(1, c0, "durate L [s]").font = INTESTAZIONE
    ws.cell(1, c0).fill = SFONDO
    ws.cell(1, c0 + 1, "durate H complete [s]").font = INTESTAZIONE
    ws.cell(1, c0 + 1).fill = SFONDO
    ws.cell(1, c0 + 2, "durate H troncate [s]").font = INTESTAZIONE
    ws.cell(1, c0 + 2).fill = SFONDO
    for i, v in enumerate(sorted(L_c), start=2):
        ws.cell(i, c0, round(v, 2))
    for i, v in enumerate(sorted(H_c), start=2):
        ws.cell(i, c0 + 1, round(v, 2))
    for i, v in enumerate(sorted(H_t), start=2):
        ws.cell(i, c0 + 2, round(v, 2))
    for j in range(c0, c0 + 3):
        ws.column_dimensions[get_column_letter(j)].width = 20


def foglio_due_persone(wb):
    ws = wb.create_sheet("08_due_persone")
    righe = [["scenario", "mmWave presenza [%]", "distanza moving [cm]",
              "distanza stazionaria [cm]", "dispersione moving [cm]",
              "energia moving", "n trial"]]
    for nome, pat in (("sfalsate di lato (A ferma 2 m, B cammina 4 m)", "due_persone_T*.csv"),
                      ("in fila (B dietro A)", "due_persone_infila_T*.csv"),
                      ("entrambe ferme, sfalsate", "due_ferme_T*.csv"),
                      ("controllo: solo B, ferma a 4 m", "controllo_B_ferma_4m_T*.csv")):
        ts = trial(pat, 20.0)
        if not ts:
            continue
        righe.append([nome,
                      media_dev([t["radar_rate_%"] for t in ts])[0],
                      media_dev([t.get("mdist_media_cm") for t in ts])[0],
                      media_dev([t.get("sdist_media_cm") for t in ts])[0],
                      media_dev([t.get("mdist_dev_cm") for t in ts])[0],
                      media_dev([t.get("menergy_media") for t in ts])[0],
                      len(ts)])
    scrivi(ws, righe, "Fig. 8 - Due persone: il LD2410B riporta un bersaglio per canale",
           "Sfalsate di lato i due canali riportano due bersagli distinti (177 cm di "
           "separazione). In fila riportano lo STESSO bersaglio (3 cm di differenza): chi "
           "sta dietro e' invisibile. In tutti i casi la PRESENZA resta al 100 %: si perde "
           "il conteggio, mai il rilevamento.")


def foglio_selettivita(wb):
    ws = wb.create_sheet("09_selettivita")
    righe = [["scenario (gate massimo 2 = 150 cm)", "presenza, finestra std 20 s [%]",
              "dev.std", "presenza a regime, scarto 120 s [%]", "dev.std", "n trial"]]
    for nome, pat in (("occupante a 1 m sull'asse", "sel_dentro_1m_T*.csv"),
                      ("persona a 3 m (oltre il taglio)", "sel_fuori_3m_T*.csv"),
                      ("persona a 1 m a 90 gradi", "sel_laterale_1m_T*.csv"),
                      ("occupante + vicino a 90 gradi", "sel_con_vicino_T*.csv")):
        a = trial(pat, 20.0)
        b = trial(pat, 120.0)
        m20, d20 = media_dev([t["radar_rate_%"] for t in a])
        m120, d120 = media_dev([t["radar_rate_%"] for t in b])
        righe.append([nome, m20, d20, m120, d120, len(b)])
    r0, r1 = scrivi(ws, righe, "Fig. 9 - Selettivita' spaziale con gate massimo 2",
                    "Il 24,8 % del vicino a 90 gradi nella finestra standard NON e' un "
                    "rilevamento: e' la coda di presenza residua dalla fase di "
                    "posizionamento, che dura 29-101 s. A regime e' 0 %. Negli scenari di "
                    "selettivita' va scartato il transitorio a 120 s, non a 20.")
    ch = BarChart()
    ch.type = "col"
    ch.title = "Selettivita' spaziale: finestra standard vs regime"
    ch.y_axis.title = "presenza rilevata [%]"
    ch.add_data(Reference(ws, min_col=2, min_row=r0, max_row=r1), titles_from_data=True)
    ch.add_data(Reference(ws, min_col=4, min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1))
    ch.height, ch.width = 9, 18
    ws.add_chart(ch, "H3")


def foglio_consumi(wb):
    ws = wb.create_sheet("13_consumi")
    righe = [["componente", "corrente media [mA]", "tensione [V]", "potenza [mW]", "fonte"],
             ["PIR HC-SR501", 0.05, 5.0, 0.3, "datasheet HC-SR501"],
             ["HLK-LD2420", 50.0, 3.3, 165.0, "manuale ufficiale Hi-Link V1.2, Tab. 2-1"],
             ["HLK-LD2410B", 80.0, 5.0, 400.0, "manuale ufficiale Hi-Link V1.03"],
             ["ESP32-WROOM-32 (WiFi attivo)", 100.0, 5.0, 500.0, "datasheet Espressif"]]
    r0, r1 = scrivi(ws, righe, "Fig. 13 - Consumo energetico (obiettivo 4)",
                    "Valori DICHIARATI dai produttori, non misurati: non si dispone di "
                    "strumentazione (concordato col professore).")
    r = r1 + 3
    intest = ["configurazione del nodo", "corrente media [mA]", "autonomia 18650 3000 mAh [h]",
              "autonomia leggibile"]
    for j, v in enumerate(intest, start=1):
        c = ws.cell(r, j, v)
        c.font = INTESTAZIONE
        c.fill = SFONDO
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    nodi = [("mmWave + ESP32 + WiFi sempre attivo", 200.0),
            ("mmWave senza WiFi continuo", 130.0),
            ("PIR sempre attivo (ESP32 modem-sleep)", 25.0),
            ("deep-sleep + PIR come guardiano", 0.06)]
    for i, (nome, mA) in enumerate(nodi, start=1):
        h = 3000 * 0.85 / mA
        ws.cell(r + i, 1, nome)
        ws.cell(r + i, 2, mA)
        ws.cell(r + i, 3, round(h, 1))
        ws.cell(r + i, 4, f"{h/8760:.1f} anni" if h > 8760 else
                          (f"{h/24:.0f} giorni" if h > 48 else f"{h:.0f} ore"))
    ws.cell(r + len(nodi) + 2, 1,
            "E' l'argomento a favore dell'architettura ibrida: il PIR fa la sentinella a "
            "costo quasi nullo per anni, il radar si accende solo in emergenza. "
            "Con l'autonomia di 13-20 ore il radar copre la finestra critica dei soccorsi; "
            "per le 72 ore servirebbe duty-cycling (1 min ON / 4 OFF -> ~5x) o batteria "
            "maggiorata.").font = Font(italic=True, size=9)

    ch = BarChart()
    ch.type = "bar"
    ch.title = "Corrente media dichiarata per componente"
    ch.x_axis.title = "corrente [mA]"
    ch.add_data(Reference(ws, min_col=2, min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=r1))
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, "G3")


def foglio_riepilogo(wb):
    ws = wb.create_sheet("00_riepilogo", 0)
    righe = [["obiettivo", "stato", "evidenza nei dati", "dove"],
             ["1 - Studio dei sensori (PIR e mmWave)", "completo",
              "principio di funzionamento, dati prodotti, limiti fisici",
              "cap. 2-3, ANALISI_PIR.md"],
             ["2 - Analisi dei dati prodotti", "completo",
              "mmWave: 18 canali di energia per-gate a 5 Hz + distanza su 2 canali. "
              "PIR: 1 bit monostabile da 3,45 s",
              "fig. 7, 10, 11, 12"],
             ["3 - Comparazione con testing numerico", "fasi 0-2 complete",
              "117 trial. Immobile a 1 m: mmWave 100 %, PIR 1,52 %. "
              "Sotto il banco immobile: mmWave 100 %, PIR 1,32 %",
              "fig. 1-9, cap. 4"],
             ["4 - Consumo energetico (informativo)", "completo",
              "80 mA (LD2410B) vs 0,05 mA (PIR): 3 ordini di grandezza",
              "fig. 13, ANALISI_CONSUMI.md"],
             ["5 - Web UI ed export CSV", "progettata, non implementata",
              "due architetture alternative documentate, serve una decisione",
              "ANALISI_WEB_UI.md, ANALISI_SITO_SERVER.md"],
             ["6 - Indice di vitalita'", "specificato, base misurata",
              "i due indicatori graduati esistono e sono monotoni col movimento: "
              "energia 68,6 -> 84,4 -> 99,3 e dispersione 21,3 -> 16,4 -> 10,4 cm",
              "ANALISI_VITALITA.md, fig. 1"]]
    scrivi(ws, righe, "Stato degli obiettivi della tesi",
           "I numeri di questo file sono ricalcolati dai CSV grezzi a ogni esecuzione di "
           "analisi/esporta_excel.py, con le stesse funzioni usate per le figure.")
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["A"].width = 38


def main():
    wb = Workbook()
    wb.remove(wb.active)
    foglio_riepilogo(wb)
    n = foglio_tutti(wb)
    foglio_dose(wb)
    foglio_sotto_banco(wb)
    foglio_distanza(wb)
    foglio_energia(wb)
    foglio_latenze(wb)
    foglio_impulsi(wb)
    foglio_due_persone(wb)
    foglio_selettivita(wb)
    foglio_consumi(wb)
    wb.save(OUT)
    print(f"scritto {OUT}  ({n} trial nel foglio maestro, {len(wb.sheetnames)} fogli)")
    print("fogli:", ", ".join(wb.sheetnames))


if __name__ == "__main__":
    main()
