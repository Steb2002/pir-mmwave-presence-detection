"""
Prototipo dell'indice di vitalita' (obiettivo 6) — versione v2 di ANALISI_VITALITA.md §3.1.

Calcola la serie vitality(t) sui CSV del logger, la classifica nelle 4 classi di
triage e produce quello che serve alla taratura (distribuzioni per scenario) e alla
validazione (matrice di confusione su trial tenuti fuori dalla taratura).

⚠️ Perche' la v1 e' stata abbandonata: costruiva la componente di micro-vitalita' sulla
variazione dell'energia STAZIONARIA, che nei nostri dati e' satura a 100 con deviazione
standard 0.0 in ogni scenario occupato — quel termine sarebbe identicamente nullo.
La v2 usa i canali MOVING per entrambe le componenti (vedi ANALISI_VITALITA.md §3.0).

Uso tipico:
  # panoramica su tutti gli scenari della fase 6
  python vitalita_proto.py ..\\HLK-LD2410x\\data\\*.csv

  # taratura: solo i trial T01-T03, con i parametri da provare
  python vitalita_proto.py ..\\HLK-LD2410x\\data\\*.csv --trials T01,T02,T03 --k 0.5

  # validazione: i trial mai visti in taratura
  python vitalita_proto.py ..\\HLK-LD2410x\\data\\*.csv --trials T04,T05 --soglie 10,40,70

  # serie temporale di un trial, per il grafico in Excel o in tesi
  python vitalita_proto.py ..\\HLK-LD2410x\\data\\fermo_1m_H_T01.csv --serie-out serie.csv

Requisiti: nessuno oltre la libreria standard.
"""

import argparse
import csv
import glob
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252

MGATE = [f"menergy_gate{i}" for i in range(9)]
SGATE = [f"senergy_gate{i}" for i in range(9)]
BASE = [
    "timestamp_ms", "radar_presence", "moving_target", "stationary_target",
    "moving_distance_cm", "stationary_distance_cm", "moving_energy",
    "stationary_energy", "pir_presence",
]
INTESTAZIONE = BASE + MGATE + SGATE + ["light_level", "out_level"]

RISOLUZIONE_GATE_CM = 75          # risoluzione di fabbrica del nostro esemplare
# TRE classi di vitalita' (decisione del professore, incontro del 29/08/2026), piu'
# lo stato "assente" che NON e' una classe di vitalita': e' il gate di presenza a monte.
# Se non c'e' nessuno non c'e' vitalita' da classificare, e chiamare "vitalita' bassa"
# una stanza vuota sarebbe l'errore piu' pericoloso possibile in un contesto di triage.
CLASSI = ["assente", "vitalita_bassa", "vitalita_moderata", "vitalita_alta"]
CLASSI_VITALI = CLASSI[1:]

# Classe attesa per gli scenari gia' acquisiti. Serve alla matrice di confusione; gli
# scenari non elencati vengono comunque riassunti, ma restano fuori dalla matrice.
ATTESE = {
    "stanza_vuota": "assente",
    "stanza_vuota_notte": "assente",
    "fermo_1m_H": "vitalita_bassa",
    "fermo_seduto": "vitalita_bassa",
    "sotto_banco_immobile_H": "vitalita_bassa",
    "micromovimenti_1m_H": "vitalita_moderata",
    "sotto_banco_movimenti_H": "vitalita_moderata",
    "movimento_1m_H": "vitalita_alta",
}

# Convenzioni di scarto del transitorio gia' usate in tutta la campagna (CLAUDE.md):
# 20 s negli scenari ordinari, 40 s sotto il banco (il soggetto deve posizionarsi),
# 120 s negli scenari di selettivita' (la coda del radar dal posizionamento e' lunga).
def transitorio_atteso(scenario):
    s = (scenario or "").lower()
    if s.startswith("sel_"):
        return 120.0
    if "banco" in s:
        return 40.0
    return 20.0


def leggi(path):
    """Legge un CSV del logger. Ricostruisce l'intestazione se manca (Serial Monitor
    aperto a sketch gia' avviato) e ignora le colonne testuali aggiunte da acquire.py."""
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        prima = f.readline()
        f.seek(0)
        if prima.split(",")[0].strip().isdigit():
            lettore = csv.DictReader(f, fieldnames=INTESTAZIONE)
        else:
            lettore = csv.DictReader(f)
        righe = []
        for r in lettore:
            try:
                riga = {c: int(r[c]) for c in BASE + MGATE}
            except (KeyError, TypeError, ValueError):
                continue      # riga troncata, oppure file senza engineering mode
            riga["scenario"] = r.get("scenario", "?")
            riga["trial"] = r.get("trial_id", "?")
            righe.append(riga)
    return righe


def scegli_gate(riga, criterio):
    """Gate attivo secondo il criterio scelto (ANALISI_VITALITA.md §3.2)."""
    if isinstance(criterio, int):
        return criterio
    if criterio == "distanza":
        # La distanza del bersaglio fermo e' piu' stabile di quella del moving; si usa
        # quella quando c'e', altrimenti la moving. Se non c'e' nessun bersaglio la
        # distanza vale 0 per convenzione del logger: si ripiega sull'energia.
        d = riga["stationary_distance_cm"] or riga["moving_distance_cm"]
        if d > 0:
            return min(8, d // RISOLUZIONE_GATE_CM)
        criterio = "energia"
    return max(range(9), key=lambda i: riga[MGATE[i]])


def fondo_per_gate(path):
    """Rumore di fondo per-gate, misurato su un file a stanza vuota.

    Senza questa correzione l'indice a stanza vuota vale ~19 — praticamente lo stesso
    di una persona immobile a 2.3 m (~21) — perche' i gate 0-1 hanno un rumore di fondo
    di 13-18 unita' che entra tal quale nella componente 1. Il gate di presenza lo
    nasconde, ma solo perche' decide lui al posto dell'indice (ANALISI_VITALITA.md §5.3).

    Si usano i soli campioni con radar_presence = 0, cioe' quelli in cui il radar stesso
    dichiara il campo libero.
    """
    righe = leggi(path)
    if not righe:
        sys.exit(f"--fondo-da: nessuna riga valida in {path}")
    vuoti = [r for r in righe if r["radar_presence"] == 0] or righe
    return [statistics.mean(r[MGATE[i]] for r in vuoti) for i in range(9)]


def netta(valore, fondo_gate):
    """Energia al netto del rumore, riportata sulla scala 0-100: cosi' il fondoscala
    resta 100 e cambia solo l'origine."""
    if fondo_gate is None or fondo_gate >= 99:
        return float(valore)
    return max(0.0, (valore - fondo_gate) * 100.0 / (100.0 - fondo_gate))


def calcola(righe, alpha_m, alpha_v, k, criterio_gate, fondo=None, sorgente="gate"):
    """Applica la v2 a tutta la serie. Le EWMA partono dal PRIMO campione del file,
    anche quando poi si scarta il transitorio: cosi' all'inizio della finestra utile
    sono gia' a regime, invece di partire da zero e simulare un finto 'nessun segno'."""
    out = []
    mov_ewma = None
    var_ewma = 0.0
    prec_gate_energia = None
    t0 = righe[0]["timestamp_ms"]

    for r in righe:
        g = scegli_gate(r, criterio_gate)
        e_gate = netta(r[MGATE[g]], fondo[g] if fondo else None)
        # v3 (31/08/2026): si usa la SOLA energia del gate attivo.
        # La v2 faceva max(moving_energy, e_gate), e questo era la causa del fallimento
        # di trasferibilita' fra geometrie: `moving_energy` e' l'energia aggregata del
        # bersaglio e a distanza ravvicinata satura a 100, vincendo il max qualunque
        # gate si scelga. Sotto il banco l'indice risultava pinnato al fondoscala
        # (97 % dei campioni) e un soggetto immobile leggeva 50,2 invece di ~25.
        # Con la sola energia di gate gli scenari a 1 m restano invariati e quello
        # sotto il banco rientra in scala: 22,1 contro i 25,8 di `fermo_1m_H`.
        mov_raw = e_gate if sorgente == "gate" else max(float(r["moving_energy"]), e_gate)

        if mov_ewma is None:
            mov_ewma = float(mov_raw)
        else:
            mov_ewma = alpha_m * mov_raw + (1 - alpha_m) * mov_ewma

        var_raw = 0.0 if prec_gate_energia is None else abs(e_gate - prec_gate_energia)
        prec_gate_energia = e_gate
        var_ewma = alpha_v * var_raw + (1 - alpha_v) * var_ewma

        grezzo = max(0.0, min(100.0, mov_ewma + k * var_ewma))
        out.append({
            "t_s": (r["timestamp_ms"] - t0) / 1000.0,
            "gate": g,
            "mov_ewma": mov_ewma,
            "var_ewma": var_ewma,
            "vitality": 0.0 if r["radar_presence"] == 0 else grezzo,
            "vitality_no_gate": grezzo,     # senza il gate di presenza: vedi §5.3
            "presenza": r["radar_presence"],
        })
    return out


def classifica(v, soglie, presente=True):
    """Due soglie fra le tre classi di vitalita'. L'assenza NON e' decisa da una soglia
    sull'indice ma dal gate di presenza del radar: e' una condizione qualitativamente
    diversa, non il gradino piu' basso della stessa scala."""
    if not presente:
        return "assente"
    for i, s in enumerate(soglie):
        if v < s:
            return CLASSI_VITALI[i]
    return CLASSI_VITALI[-1]


def istogramma(valori, larghezza=40):
    """Istogramma testuale a decili: e' lo strumento con cui si scelgono le soglie
    (si cercano i 'vuoti' fra le distribuzioni dei diversi scenari)."""
    conte = [0] * 10
    for v in valori:
        conte[min(9, int(v // 10))] += 1
    massimo = max(conte) or 1
    righe = []
    for i, c in enumerate(conte):
        barra = "#" * round(larghezza * c / massimo)
        righe.append(f"    {i*10:3d}-{i*10+9:3d} |{barra:<{larghezza}} {100*c/len(valori):5.1f}%")
    return "\n".join(righe)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="CSV del logger (glob ok)")
    ap.add_argument("--alpha-mov", type=float, default=0.10,
                    help="EWMA della componente movimento (default 0.10 = ~2 s a 5 Hz)")
    ap.add_argument("--alpha-var", type=float, default=0.02,
                    help="EWMA della componente variabilita' (default 0.02 = ~10 s)")
    ap.add_argument("--k", type=float, default=0.5,
                    help="peso della componente variabilita' (default 0.5, DA TARARE)")
    ap.add_argument("--soglie", default="33,66",
                    help="DUE soglie fra le tre classi di vitalita' (default 33,66). "
                         "L'assenza non ha soglia: la decide il gate di presenza")
    ap.add_argument("--sorgente", default="gate", choices=("gate", "max"),
                    help="da dove viene la componente 1: 'gate' (v3, default) usa la sola "
                         "energia del gate attivo; 'max' riproduce la v2, che prendeva il "
                         "massimo fra questa e moving_energy e saturava a corta distanza")
    ap.add_argument("--gate", default="energia",
                    help="criterio per il gate attivo: energia | distanza | un numero 0-8")
    ap.add_argument("--salta-inizio", default="auto",
                    help="secondi di transitorio da scartare: un numero, oppure 'auto' "
                         "(20 s ordinari, 40 s sotto il banco, 120 s selettivita')")
    ap.add_argument("--trials", default=None,
                    help="considera solo questi trial, es. T01,T02,T03 (taratura) "
                         "oppure T04,T05 (validazione)")
    ap.add_argument("--fondo-da", default=None, metavar="CSV",
                    help="sottrae il rumore di fondo per-gate misurato su un file a "
                         "stanza vuota e riscala su 0-100. Senza questa correzione il "
                         "rumore dei gate 0-1 (13-18 unita') tiene l'indice a ~19 anche "
                         "a stanza vuota")
    ap.add_argument("--senza-gate-presenza", action="store_true",
                    help="usa l'indice SENZA la forzatura a 0 su radar_presence=0: "
                         "risponde alla domanda 'l'indice da solo distinguerebbe una "
                         "stanza vuota da una persona immobile?'")
    ap.add_argument("--istogrammi", action="store_true",
                    help="stampa la distribuzione per scenario (serve alla taratura)")
    ap.add_argument("--serie-out", default=None,
                    help="salva la serie vitality(t) del PRIMO file in un CSV")
    ap.add_argument("--out", default=None, help="salva il riepilogo per file in un CSV")
    args = ap.parse_args()

    soglie = [float(x) for x in args.soglie.split(",")]
    if len(soglie) != 2 or soglie != sorted(soglie):
        sys.exit("--soglie vuole due valori crescenti, es. 33,66")

    criterio = args.gate
    if criterio.isdigit():
        criterio = int(criterio)
        if not 0 <= criterio <= 8:
            sys.exit("--gate numerico deve stare fra 0 e 8")
    elif criterio not in ("energia", "distanza"):
        sys.exit("--gate: usare 'energia', 'distanza' oppure un numero 0-8")

    filtro_trial = set(args.trials.split(",")) if args.trials else None
    campo = "vitality_no_gate" if args.senza_gate_presenza else "vitality"

    percorsi = []
    for p in args.files:
        percorsi.extend(glob.glob(p))
    if not percorsi:
        sys.exit("Nessun file trovato.")

    fondo = fondo_per_gate(args.fondo_da) if args.fondo_da else None

    print(f"Parametri: alpha_mov={args.alpha_mov}  alpha_var={args.alpha_var}  "
          f"k={args.k}  soglie={soglie}  gate={args.gate}")
    print(f"Indice usato: {campo}"
          f"{'  (senza gate di presenza)' if args.senza_gate_presenza else ''}")
    if fondo:
        print(f"Fondo sottratto (da {Path(args.fondo_da).name}): "
              + " ".join(f"g{i}={v:.0f}" for i, v in enumerate(fondo)))
    if filtro_trial:
        print(f"Solo trial: {', '.join(sorted(filtro_trial))}")

    risultati = []
    per_scenario = defaultdict(list)      # scenario -> lista di valori (tutti i campioni)
    saltati = []

    for path in sorted(percorsi):
        righe = leggi(path)
        if len(righe) < 50:
            saltati.append((Path(path).name, "meno di 50 righe valide o niente per-gate"))
            continue
        scenario = righe[0]["scenario"]
        trial = righe[0]["trial"]
        if filtro_trial and trial not in filtro_trial:
            continue

        salta = (transitorio_atteso(scenario) if args.salta_inizio == "auto"
                 else float(args.salta_inizio))
        serie = calcola(righe, args.alpha_mov, args.alpha_var, args.k, criterio, fondo,
                        args.sorgente)
        utili = [s for s in serie if s["t_s"] >= salta]
        if len(utili) < 25:
            saltati.append((Path(path).name, f"nulla oltre il transitorio di {salta:.0f} s"))
            continue

        valori = [s[campo] for s in utili]
        valori_ord = sorted(valori)
        classi = [classifica(s_["vitality"], soglie, s_["presenza"] != 0)
                  for s_ in utili]
        conteggio = {c: classi.count(c) for c in CLASSI}
        modale = max(CLASSI, key=lambda c: conteggio[c])

        ris = {
            "file": Path(path).name,
            "scenario": scenario,
            "trial": trial,
            "n": len(valori),
            "salta_s": salta,
            "media": round(statistics.mean(valori), 1),
            "mediana": round(statistics.median(valori), 1),
            "p5": round(valori_ord[len(valori_ord) // 20], 1),
            "p95": round(valori_ord[len(valori_ord) * 19 // 20], 1),
            "classe_modale": modale,
            "attesa": ATTESE.get(scenario, ""),
        }
        for c in CLASSI:
            ris[f"%{c}"] = round(100 * conteggio[c] / len(valori), 1)
        risultati.append(ris)
        per_scenario[scenario].extend(valori)

        if args.serie_out and path == sorted(percorsi)[0]:
            with open(args.serie_out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["t_s", "gate", "mov_ewma", "var_ewma", "vitality",
                            "vitality_no_gate", "presenza", "classe"])
                for s in serie:
                    w.writerow([round(s["t_s"], 2), s["gate"], round(s["mov_ewma"], 2),
                                round(s["var_ewma"], 2), round(s["vitality"], 2),
                                round(s["vitality_no_gate"], 2), s["presenza"],
                                classifica(s[campo], soglie, s["presenza"] != 0)])
            print(f"\nSerie temporale di {Path(path).name} salvata in {args.serie_out}")

    if not risultati:
        sys.exit("Nessun file utilizzabile (servono le colonne di engineering mode).")

    print("\n=== PER TRIAL ===")
    print(f"{'file':34s}{'media':>7}{'mediana':>9}{'p5':>6}{'p95':>6}  "
          f"{'classe modale':<15}{'attesa':<15}")
    for r in sorted(risultati, key=lambda x: (x["scenario"], x["trial"])):
        segno = ""
        if r["attesa"]:
            segno = "  OK" if r["classe_modale"] == r["attesa"] else "  <-- DIVERSA"
        print(f"{r['file']:34s}{r['media']:7.1f}{r['mediana']:9.1f}{r['p5']:6.1f}"
              f"{r['p95']:6.1f}  {r['classe_modale']:<15}{r['attesa'] or '-':<15}{segno}")

    print("\n=== AGGREGATO PER SCENARIO (media fra trial) ===")
    per_sc_trial = defaultdict(list)
    for r in risultati:
        per_sc_trial[r["scenario"]].append(r)
    for sc in sorted(per_sc_trial):
        rs = per_sc_trial[sc]
        medie = [r["media"] for r in rs]
        m = statistics.mean(medie)
        s = statistics.stdev(medie) if len(medie) > 1 else 0.0
        attesa = ATTESE.get(sc, "-")
        print(f"\n[{sc}]  {len(rs)} trial   attesa: {attesa}")
        print(f"  indice medio: {m:.1f} ± {s:.1f}   "
              f"(min trial {min(medie):.1f}, max trial {max(medie):.1f})")
        quote = {c: statistics.mean(r[f'%{c}'] for r in rs) for c in CLASSI}
        print("  campioni per classe: " +
              "  ".join(f"{c}={quote[c]:.1f}%" for c in CLASSI if quote[c] > 0.05))
        if args.istogrammi:
            print(istogramma(per_scenario[sc]))

    # Matrice di confusione sui soli scenari con classe attesa nota
    noti = [r for r in risultati if r["attesa"]]
    if noti:
        print("\n=== MATRICE DI CONFUSIONE (per campione, %) ===")
        print("righe = classe attesa, colonne = classe assegnata dall'indice\n")
        print(f"{'attesa':<16}" + "".join(f"{c:>16}" for c in CLASSI) + f"{'campioni':>12}")
        tot_ok = tot_n = 0
        recall = []
        for atteso in CLASSI:
            rs = [r for r in noti if r["attesa"] == atteso]
            if not rs:
                continue
            n = sum(r["n"] for r in rs)
            riga = []
            for c in CLASSI:
                k = sum(r["n"] * r[f"%{c}"] / 100 for r in rs)
                riga.append(f"{100*k/n:15.1f}%")
                if c == atteso:
                    tot_ok += k
                    recall.append(100 * k / n)
            tot_n += n
            print(f"{atteso:<16}" + "".join(riga) + f"{n:12d}")
        # Le classi hanno numeri di campioni molto diversi (la notte a stanza vuota da
        # sola vale piu' di tutti gli altri scenari messi insieme): l'accuratezza pesata
        # sui campioni premia la classe piu' numerosa. La media delle recall e' la cifra
        # da riportare in tesi; l'altra si tiene solo per confronto.
        print(f"\nAccuratezza per campione (pesata):  {100*tot_ok/tot_n:.1f}% "
              f"su {tot_n} campioni")
        print(f"Media delle recall per classe:      {statistics.mean(recall):.1f}%   "
              f"<-- la cifra corretta se le classi hanno numerosita' diverse")
        giusti = sum(1 for r in noti if r["classe_modale"] == r["attesa"])
        print(f"Trial la cui classe MODALE e' quella attesa: {giusti}/{len(noti)}")
        print("\nNB: queste cifre valgono per i parametri stampati in testa. Finche' si")
        print("usano gli stessi trial per scegliere i parametri e per misurare "
              "l'accuratezza,\nil numero e' ottimistico: la cifra da mettere in tesi e' "
              "quella ottenuta con\n--trials T04,T05 dopo aver tarato su T01-T03.")

    if saltati:
        print("\nFile saltati:")
        for nome, motivo in saltati:
            print(f"  {nome}: {motivo}")

    if args.out:
        chiavi = list(risultati[0].keys())
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=chiavi)
            w.writeheader()
            w.writerows(risultati)
        print(f"\nRiepilogo salvato in {args.out}")


if __name__ == "__main__":
    main()
