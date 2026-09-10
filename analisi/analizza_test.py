"""
Analisi delle metriche di rilevamento dai CSV prodotti da acquire.py (repo del professore).

Calcola per ogni file e aggrega per scenario:
- tasso di rilevamento radar e PIR vs ground truth (accuratezza per campione)
- falsi positivi (scenari con ground_truth_presence=0) e falsi negativi (=1)
- latenza di rilevamento (scenari di ingresso, con --event-time)
- latenza di RILASCIO (scenari di uscita, con --release-time)
- statistiche di distanza ed energia del radar

Uso:
    python analizza_test.py data/*.csv
    python analizza_test.py data/ingresso_*.csv --event-time 10
    python analizza_test.py data/uscita_*.csv --release-time 10
    python analizza_test.py data/*.csv --out riepilogo.csv
    python analizza_test.py data/stanza_vuota_*.csv --salta-inizio 60

Requisiti: nessuno oltre la libreria standard (opzionale: nessun numpy necessario).
"""

import argparse
import csv
import glob
import re
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252
from collections import defaultdict
from pathlib import Path


def leggi_csv(path):
    """Legge un CSV di acquire.py e restituisce la lista di righe (dict)."""
    righe = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            try:
                righe.append({
                    "t_ms": int(r["timestamp_ms"]),
                    "radar": int(r["radar_presence"]),
                    "moving": int(r["moving_target"]),
                    "stationary": int(r["stationary_target"]),
                    "mdist": int(r["moving_distance_cm"]),
                    "sdist": int(r["stationary_distance_cm"]),
                    "menergy": int(r["moving_energy"]),
                    "senergy": int(r["stationary_energy"]),
                    "pir": int(r["pir_presence"]),
                    "scenario": r.get("scenario", "?"),
                    "trial": r.get("trial_id", "?"),
                    "gt": int(r.get("ground_truth_presence", -1)),
                    "gt_state": r.get("ground_truth_state", "?"),
                })
            except (KeyError, ValueError, TypeError):
                continue  # riga malformata o troncata (TypeError: colonne mancanti -> None)
    return righe


def latenza_s(righe, event_time_s, colonna):
    """Prima rilevazione (colonna=1) dopo event_time_s dall'inizio del file. None se mai."""
    if not righe:
        return None
    t0 = righe[0]["t_ms"]
    for r in righe:
        t_rel = (r["t_ms"] - t0) / 1000.0
        if t_rel >= event_time_s and r[colonna] == 1:
            return t_rel - event_time_s
    return None


def rilascio_s(righe, event_time_s, colonna):
    """
    Latenza di RILASCIO (Test 2.2): secondi tra l'uscita del soggetto (a event_time_s
    dall'inizio del file) e il momento in cui il sensore dichiara la stanza vuota.

    Restituisce (valore, riaccensioni, nota):
      valore       secondi dal momento dell'uscita, oppure None se non misurabile
      riaccensioni quante volte il sensore e' tornato a 1 DOPO essere andato a 0
                   (nel Test 0.2 il radar ha tenuto un target fantasma in decadimento:
                   se lampeggia, un solo numero non descrive il comportamento)
      nota         "" se la misura e' valida, altrimenti il motivo:
                   "MAI"   il sensore era ancora a 1 alla fine del file: il rilascio
                           e' piu' lungo della durata acquisita, il file e' troppo corto
                   "PRIMA" il sensore era gia' a 0 al momento dell'uscita. Per il PIR e'
                           normale e atteso: la ritenuta (3.4-3.8 s misurati) puo' scadere
                           mentre il soggetto e' ancora presente e in movimento. Non e'
                           un rilascio, e' il monostabile che si e' esaurito prima
                   "VUOTO" nessun campione dopo l'evento

    L'istante restituito e' quello del PRIMO campione a 0 dopo l'ultimo campione a 1,
    cioe' il momento in cui l'assenza viene effettivamente osservata. A 5 Hz
    l'incertezza intrinseca e' +/- 0.2 s: va dichiarata, e rende inutile riportare
    piu' di un decimale.
    """
    if not righe:
        return None, 0, "VUOTO"

    t0 = righe[0]["t_ms"]
    dopo = [((r["t_ms"] - t0) / 1000.0 - event_time_s, r[colonna])
            for r in righe if (r["t_ms"] - t0) / 1000.0 >= event_time_s]
    if not dopo:
        return None, 0, "VUOTO"

    # Riaccensioni: fronti 0->1 nella coda dopo l'uscita
    riaccensioni = sum(1 for a, b in zip(dopo, dopo[1:]) if a[1] == 0 and b[1] == 1)

    if not any(v == 1 for _, v in dopo):
        return None, riaccensioni, "PRIMA"
    if dopo[-1][1] == 1:
        return None, riaccensioni, "MAI"

    # Ultimo campione a 1, poi il primo a 0 che lo segue
    idx_ultimo_uno = max(i for i, (_, v) in enumerate(dopo) if v == 1)
    return dopo[idx_ultimo_uno + 1][0], riaccensioni, ""


def impulsi_pir(righe, salta_inizio_s=0.0):
    """Estrae gli impulsi del PIR. Ritorna (durate_complete, durate_troncate).

    Serve a caratterizzare l'uscita dell'HC-SR501, che NON e' un segnale di presenza ma
    un monostabile: ogni evento di movimento alza l'uscita per il tempo di ritenuta.
    In modalita' H (repeat trigger) un nuovo evento durante l'impulso lo fa ripartire,
    quindi con movimento continuo l'uscita resta alta a lungo.

    ⚠️ Gli impulsi TRONCATI (gia' alti a inizio finestra, o ancora alti a fine file) vanno
    riportati a parte e non scartati: un impulso molto lungo e' proprio quello che ha piu'
    probabilita' di essere tagliato, ed e' la prova che il ritrigger funziona. Scartarli
    faceva concludere "nessun impulso" su un file che conteneva un impulso da 9.2 s
    (verificato il 22/08/2026).
    """
    if not righe or any(r["pir"] < 0 for r in righe):
        return [], []          # -1 = PIR non cablato, vedi analizza_file
    t0 = righe[0]["t_ms"]
    sel = [r for r in righe if (r["t_ms"] - t0) / 1000.0 >= salta_inizio_s]
    if not sel:
        return [], []
    t_fine = (sel[-1]["t_ms"] - t0) / 1000.0
    complete, troncate = [], []
    inizio = None if sel[0]["pir"] == 0 else (sel[0]["t_ms"] - t0) / 1000.0
    parziale_iniziale = sel[0]["pir"] == 1
    for a, b in zip(sel, sel[1:]):
        ta = (a["t_ms"] - t0) / 1000.0
        if a["pir"] == 0 and b["pir"] == 1:
            inizio = (b["t_ms"] - t0) / 1000.0
        elif a["pir"] == 1 and b["pir"] == 0 and inizio is not None:
            d = ta - inizio + 0.2
            (troncate if parziale_iniziale else complete).append(d)
            parziale_iniziale = False
            inizio = None
    if inizio is not None:                      # ancora alto a fine file
        troncate.append(t_fine - inizio + 0.2)
    return complete, troncate


def analizza_file(path, event_time_s=None, salta_inizio_s=0.0, release_time_s=None):
    righe = leggi_csv(path)
    if not righe:
        return None

    # Scarta i primi secondi: nei file "stanza vuota" contengono l'operatore che esce,
    # che e' presenza reale e falserebbe il conteggio dei falsi positivi. Il taglio va
    # dichiarato nella tesi insieme al valore usato (default 0 = nessun taglio).
    if salta_inizio_s > 0:
        t0 = righe[0]["t_ms"]
        righe = [r for r in righe if (r["t_ms"] - t0) / 1000.0 >= salta_inizio_s]
        if not righe:
            return None

    n = len(righe)
    durata_s = (righe[-1]["t_ms"] - righe[0]["t_ms"]) / 1000.0
    gt = righe[0]["gt"]

    # 🚨 PIR NON CABLATO. I logger scrivono -1 nella colonna `pir_presence` quando il
    # sensore non e' collegato (`#define PIR_COLLEGATO 0`). Senza quel marcatore il pin
    # con pull-down leggerebbe 0 per tutto il file e OGNI metrica del PIR uscirebbe come
    # una misura plausibile — "fn_pir_% = 100,0" con una persona davanti — invece che
    # come un dato mancante. Non e' un rischio teorico: `esporta_excel.py > foglio_tutti`
    # passa in rassegna TUTTI i CSV della cartella con una glob, quindi il numero finto
    # entrerebbe da solo nel foglio da cui si fanno le pivot.
    # Qui le metriche del PIR vengono semplicemente OMESSE: le celle restano vuote in
    # Excel (`r.get(c, "")`) e l'aggregato per scenario non le calcola.
    pir_assente = any(r["pir"] < 0 for r in righe)
    ris = {
        "file": Path(path).name,
        "scenario": righe[0]["scenario"],
        "trial": righe[0]["trial"],
        "gt": gt,
        "gt_state": righe[0]["gt_state"],
        "n_campioni": n,
        "durata_s": round(durata_s, 1),
        "radar_rate_%": round(100 * sum(r["radar"] for r in righe) / n, 1),
    }
    if pir_assente:
        ris["pir_stato"] = "NON COLLEGATO"
    else:
        ris["pir_rate_%"] = round(100 * sum(r["pir"] for r in righe) / n, 1)

    # Accuratezza per campione rispetto alla ground truth.
    # ⚠️ Nei file con un EVENTO (test 2.1 e 2.2) la ground truth scritta nel CSV e'
    # costante ma la realta' cambia a metà file: prima dell'evento il soggetto e' fuori
    # (2.1) o dentro (2.2). Calcolare accuratezza e falsi positivi su tutto il file
    # darebbe numeri privi di senso — nel 2.2 il radar risulterebbe con decine di "falsi
    # positivi/ora" che sono in realta' rilevamenti corretti. Quindi con --event-time o
    # --release-time queste metriche si saltano del tutto: di quei file interessa solo
    # il tempo di reazione, i tassi si misurano nei test 1.1/1.3 dove la ground truth
    # e' davvero costante.
    if gt in (0, 1) and release_time_s is None and event_time_s is None:
        ris["radar_acc_%"] = round(100 * sum(1 for r in righe if r["radar"] == gt) / n, 1)
        if not pir_assente:
            ris["pir_acc_%"] = round(100 * sum(1 for r in righe if r["pir"] == gt) / n, 1)
        canali = ("radar",) if pir_assente else ("radar", "pir")
        if gt == 0:
            # Falsi positivi: eventi di attivazione (fronti di salita) per ora
            for col in canali:
                fronti = sum(1 for a, b in zip(righe, righe[1:]) if a[col] == 0 and b[col] == 1)
                ore = durata_s / 3600 if durata_s > 0 else 1
                ris[f"fp_{col}_eventi_h"] = round(fronti / ore, 2)
        else:
            # Falsi negativi: % di tempo in cui il sensore perde la persona
            ris["fn_radar_%"] = round(100 - ris["radar_acc_%"], 1)
            if not pir_assente:
                ris["fn_pir_%"] = round(100 - ris["pir_acc_%"], 1)

    # Latenza (solo per scenari di ingresso, con evento a tempo noto)
    if event_time_s is not None:
        lr = latenza_s(righe, event_time_s, "radar")
        lp = None if pir_assente else latenza_s(righe, event_time_s, "pir")
        ris["latenza_radar_s"] = round(lr, 2) if lr is not None else "MAI"
        if not pir_assente:
            ris["latenza_pir_s"] = round(lp, 2) if lp is not None else "MAI"

        # Differenza appaiata radar-PIR sullo stesso trial. E' il confronto pulito: la
        # latenza assoluta contiene il tempo di reazione al beep e il tragitto verso il
        # campo, che sono uguali per i due sensori e si cancellano nella differenza.
        # Negativa = il radar ha rilevato prima.
        if lr is not None and lp is not None:
            ris["latenza_delta_s"] = round(lr - lp, 2)

        # Validita' del trial: nei 3 s PRIMA dell'ingresso entrambi i sensori devono
        # essere a zero. Se il radar sta ancora tenendo la coda di presenza dell'operatore
        # uscito (~10 s misurati nel Test 0.2), la latenza risulta ~0 per costruzione e il
        # trial va buttato, non interpretato.
        t0 = righe[0]["t_ms"]
        pre = [r for r in righe
               if event_time_s - 3.0 <= (r["t_ms"] - t0) / 1000.0 < event_time_s]
        if pre:
            ris["pre_radar_%"] = round(100 * sum(r["radar"] for r in pre) / len(pre), 1)
            if not pir_assente:
                ris["pre_pir_%"] = round(100 * sum(r["pir"] for r in pre) / len(pre), 1)

    # Latenza di rilascio (Test 2.2: soggetto che esce a tempo noto)
    if release_time_s is not None:
        for col in (("radar",) if pir_assente else ("radar", "pir")):
            nome = col
            val, riacc, nota = rilascio_s(righe, release_time_s, col)
            ris[f"rilascio_{nome}_s"] = round(val, 1) if val is not None else nota
            ris[f"riaccensioni_{nome}"] = riacc

    # Statistiche distanza/energia (solo campioni con rilevamento)
    # Distanza del bersaglio IN MOVIMENTO: e' la grandezza del Test 1.2 (accuratezza
    # della distanza con persona che cammina sul posto a distanza nota).
    mdist = [r["mdist"] for r in righe if r["moving"] == 1 and r["mdist"] > 0]
    if mdist:
        ris["mdist_media_cm"] = round(statistics.mean(mdist), 1)
        ris["mdist_dev_cm"] = round(statistics.stdev(mdist), 1) if len(mdist) > 1 else 0

    # Se il nome dello scenario contiene la distanza nominale (es. "movimento_2m" o
    # "movimento_2.5m") si calcola direttamente l'errore. La distanza nominale e' quella
    # del TORACE del soggetto: il radar riflette sul busto, non sui piedi.
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m(?![a-z])", ris["scenario"] or "")
    if m and mdist:
        nominale_cm = float(m.group(1).replace(",", ".")) * 100
        ris["dist_nominale_cm"] = round(nominale_cm, 1)
        ris["errore_cm"] = round(statistics.mean(mdist) - nominale_cm, 1)

    sdist = [r["sdist"] for r in righe if r["stationary"] == 1 and r["sdist"] > 0]
    sen = [r["senergy"] for r in righe if r["stationary"] == 1]
    men = [r["menergy"] for r in righe if r["moving"] == 1]
    if sdist:
        ris["sdist_media_cm"] = round(statistics.mean(sdist), 1)
        ris["sdist_dev_cm"] = round(statistics.stdev(sdist), 1) if len(sdist) > 1 else 0
    if sen:
        ris["senergy_media"] = round(statistics.mean(sen), 1)
    if men:
        ris["menergy_media"] = round(statistics.mean(men), 1)

    return ris


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="CSV da analizzare (glob ok)")
    ap.add_argument("--event-time", type=float, default=None,
                    help="istante (s dall'inizio) in cui avviene l'evento, per il calcolo latenza")
    ap.add_argument("--release-time", type=float, default=None, metavar="SEC",
                    help="istante (s dall'inizio) in cui il soggetto ESCE, per il calcolo "
                         "della latenza di rilascio (Test 2.2). Sospende il calcolo di "
                         "accuratezza e falsi positivi: in questi file la ground truth "
                         "non e' costante")
    ap.add_argument("--salta-inizio", type=float, default=0.0, metavar="SEC",
                    help="scarta i primi SEC secondi di ogni file (per i test 'stanza "
                         "vuota': i primi secondi contengono l'operatore che esce)")
    ap.add_argument("--impulsi", action="store_true",
                    help="analizza la struttura degli impulsi del PIR invece delle "
                         "metriche di rilevamento (per capire se il jumper H funziona)")
    ap.add_argument("--out", default=None, help="salva il riepilogo in un CSV")
    args = ap.parse_args()

    if args.salta_inizio > 0 and (args.event_time is not None or args.release_time is not None):
        sys.exit("--salta-inizio non si combina con --event-time / --release-time: il "
                 "taglio sposta l'origine dei tempi e la latenza risulterebbe sbagliata.")
    if args.event_time is not None and args.release_time is not None:
        sys.exit("--event-time e --release-time insieme: il protocollo dei test 2.1 e 2.2 "
                 "prevede un solo evento per file (ingresso OPPURE uscita). Analizzare "
                 "le due serie separatamente.")

    paths = []
    for pattern in args.files:
        paths.extend(glob.glob(pattern))
    if not paths:
        sys.exit("Nessun file trovato.")

    if args.impulsi:
        import statistics as _st
        print(f"--- impulsi del PIR (scartati i primi {args.salta_inizio:.0f} s) ---")
        print("file                                 n   media   min   max   >5s")
        tutte, tutti_tronchi = [], []
        for path in sorted(paths):
            righe = leggi_csv(path)
            d, tronchi = impulsi_pir(righe, args.salta_inizio)
            tutte += d
            tutti_tronchi += tronchi
            nota = ""
            if tronchi:
                nota = f"  + {len(tronchi)} troncati (max >={max(tronchi):.1f}s)"
            if not d:
                print(f"{Path(path).name:35s}  0   (nessun impulso completo){nota}")
                continue
            print(f"{Path(path).name:35s} {len(d):3d}  {_st.mean(d):5.2f}s "
                  f"{min(d):5.2f}s {max(d):5.2f}s  {sum(1 for x in d if x > 5)}{nota}")
        if not tutte and not tutti_tronchi:
            sys.exit("Nessun impulso: il PIR e' collegato? "
                     "(oppure e' nei ~60 s di stabilizzazione dopo l'accensione)")
        lunghi = [x for x in tutte + tutti_tronchi if x > 5]
        if tutti_tronchi:
            print(f"impulsi troncati (a cavallo dei bordi della finestra): "
                  f"{len(tutti_tronchi)}, il piu' lungo >= {max(tutti_tronchi):.1f} s")
        if not tutte:
            print("Nessun impulso COMPLETO: le statistiche sotto usano i soli troncati.")
            tutte = tutti_tronchi
        print()
        print(f"TOTALE {len(tutte)} impulsi: media {_st.mean(tutte):.2f} s, "
              f"dev.std {(_st.stdev(tutte) if len(tutte) > 1 else 0):.2f} s, "
              f"range {min(tutte):.2f}-{max(tutte):.2f} s")
        print(f"impulsi oltre 5 s: {len(lunghi)}")
        print()
        if lunghi:
            print("=> Ci sono impulsi lunghi: il RITRIGGER FUNZIONA (modalita' H attiva).")
            print("   Gli impulsi corti visti negli altri test dipendono quindi dal tipo")
            print("   di movimento, non dalla configurazione del sensore.")
        else:
            print("=> NESSUN impulso oltre 5 s nemmeno attraversando il campo:")
            print("   l'uscita si comporta da monostabile a durata fissa. Da dichiarare")
            print("   in tesi: le percentuali del PIR valgono in questa configurazione.")
        return

    if args.salta_inizio > 0:
        print(f"NB: scartati i primi {args.salta_inizio:.0f} s di ogni file")
    if args.event_time is not None:
        print(f"NB: ingresso del soggetto a t={args.event_time:.0f} s. Accuratezza e falsi "
              f"positivi NON calcolati (la ground truth cambia a metà file).")
    if args.release_time is not None:
        print(f"NB: uscita del soggetto a t={args.release_time:.0f} s. Accuratezza e falsi "
              f"positivi NON calcolati (la ground truth cambia a metà file).")
    risultati = [r for p in sorted(paths)
                 if (r := analizza_file(p, args.event_time, args.salta_inizio,
                                        args.release_time))]
    if not risultati:
        sys.exit("Nessun dato valido nei file indicati.")

    # Stampa per file
    chiavi = sorted({k for r in risultati for k in r}, key=lambda k: (k != "file", k))
    print("\n=== RISULTATI PER FILE ===")
    for r in risultati:
        print("  " + " | ".join(f"{k}={r[k]}" for k in chiavi if k in r))

    # Aggregazione per scenario (media ± dev.std sulle prove)
    print("\n=== AGGREGATO PER SCENARIO (media su trial) ===")
    per_scenario = defaultdict(list)
    for r in risultati:
        per_scenario[r["scenario"]].append(r)
    numeriche = [k for k in chiavi if k not in ("file", "scenario", "trial", "gt", "gt_state")]
    for sc, rs in per_scenario.items():
        print(f"\n[{sc}] ({len(rs)} prove, gt={rs[0]['gt']})")
        for k in numeriche:
            vals = [r[k] for r in rs if isinstance(r.get(k), (int, float))]
            if vals:
                m = statistics.mean(vals)
                s = statistics.stdev(vals) if len(vals) > 1 else 0
                print(f"  {k}: {m:.2f} ± {s:.2f}")
        mai = sum(1 for r in rs if r.get("latenza_radar_s") == "MAI")
        if mai:
            print(f"  ⚠ radar MAI rilevato in {mai}/{len(rs)} prove")

        # Trial da scartare: il sensore era gia' attivo prima dell'evento
        sporchi = [r["trial"] for r in rs if r.get("pre_radar_%", 0) > 0
                   or r.get("pre_pir_%", 0) > 0]
        if sporchi:
            print(f"  ⚠ DA SCARTARE: {', '.join(sporchi)} — un sensore era ancora attivo")
            print(f"    nei 3 s prima dell'evento (coda di presenza non esaurita): la")
            print(f"    latenza di quei trial e' ~0 per costruzione, non e' una misura")

        # Le medie sopra sono calcolate solo sui trial con rilascio misurato: i casi
        # "MAI"/"PRIMA" sono stringhe e vengono saltati. Se non li si conta a parte, una
        # media su 2 trial validi su 5 sembra un risultato solido e non lo e'.
        for nome in ("radar", "pir"):
            chiave = f"rilascio_{nome}_s"
            if not any(chiave in r for r in rs):
                continue
            validi = [r for r in rs if isinstance(r.get(chiave), (int, float))]
            never = sum(1 for r in rs if r.get(chiave) == "MAI")
            prima = sum(1 for r in rs if r.get(chiave) == "PRIMA")
            print(f"  rilascio {nome}: {len(validi)}/{len(rs)} trial misurati", end="")
            if never:
                print(f", {never} ancora attivi a fine file (allungare la durata)", end="")
            if prima:
                print(f", {prima} gia' a zero all'uscita", end="")
            print()

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=chiavi)
            w.writeheader()
            w.writerows(risultati)
        print(f"\nRiepilogo salvato in {args.out}")


if __name__ == "__main__":
    main()
