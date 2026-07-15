# Analisi — Indice di vitalità (Obiettivo 6)

> Obiettivo 6 dalle parole del professore: *"oltre a presenza sì/no, creare un indice
> di vitalità: un algoritmo che valuta quanto una persona si muove — questa persona
> si muove 50 su 100 → vivo o moderatamente vivo"*.
>
> Questo documento è la specifica di riferimento dell'algoritmo. È indipendente dalla
> web UI: l'indice si sviluppa e si valida sui CSV dei test (Fase 6 di PIANO_TEST.md);
> la visualizzazione nella dashboard (gauge) è solo uno dei suoi utilizzi.

---

## 1. Il problema in termini UPRISE

Nel contesto del progetto, la differenza tra "presenza" e "vitalità" è la differenza
tra due domande dei soccorritori:

1. *C'è qualcuno sotto il banco?* → presenza (obiettivi 1-3)
2. *In che condizioni è?* → vitalità: si muove attivamente (cosciente), fa solo
   micro-movimenti (ferito/intrappolato ma vivo), o non dà segni?

Il PIR non può nemmeno porsi la seconda domanda. Il mmWave sì, perché espone
l'**energia riflessa per gate di distanza** — una misura continua di *quanto* si
muove ciò che riflette, non solo *se* si muove. L'indice di vitalità è la sintesi
di questa informazione in un numero 0-100 leggibile da un non tecnico.

## 2. Dati di ingresso (dal firmware, 5 Hz)

| Segnale | Colonna CSV | Cosa misura |
|---|---|---|
| Energia moving del target | `moving_energy` | intensità del movimento rilevato (0-100) |
| Energia per-gate moving | `menergy_gate0..8` | dove avviene il movimento |
| Energia per-gate stationary | `senergy_gate0..8` | riflessione del corpo fermo; oscilla col respiro |
| Stato presenza | `radar_presence` | gate di guardia: se 0, vitalità forzata a 0 |

Osservazione chiave (da verificare nei test): una persona **viva ma immobile** ha
energia moving ≈ 0 ma l'energia stationary del suo gate **oscilla** con il respiro
(banda 0.1-0.5 Hz — stessa fisica del test respiro, Fase 5). Una stanza vuota ha
energia stazionaria costante (solo rumore). La *varianza* dell'energia stationary
è quindi il segnale di vita minimo, sotto il movimento.

## 3. Algoritmo v1 — specifica

Due componenti, aggiornate a ogni campione (5 Hz):

```
gate_attivo = argmax(senergy_gate[i])            # dov'è la persona

# Componente 1 — movimento (reattiva, ~2 s di memoria)
mov_raw  = max(moving_energy, menergy_gate[gate_attivo])     # 0-100
mov_ewma = α_m · mov_raw + (1-α_m) · mov_ewma                # α_m = 0.1

# Componente 2 — micro-vitalità/respiro (lenta, ~10 s di memoria)
delta    = |senergy_gate[gate_attivo] - senergy_prec|        # variazione tick-a-tick
resp_ewma= α_r · delta + (1-α_r) · resp_ewma                 # α_r = 0.02

# Fusione
vitality = clamp( mov_ewma + k · resp_ewma , 0, 100 )        # k da tarare (~5-15)
if radar_presence == 0: vitality = 0
```

Razionale delle scelte:
- **EWMA e non media mobile**: costa O(1) in RAM (2 float) — gira identica su ESP32
  e in Python; una finestra mobile richiederebbe buffer e dà risultati simili
- **Due costanti di tempo diverse**: il movimento deve reagire in ~2 s (α=0.1 a 5 Hz),
  il respiro è un segnale lento che va integrato su ~10 s (α=0.02) per emergere dal rumore
- **max(target, gate)**: l'energia target e quella per-gate a volte divergono
  (filtri interni del radar); prendere il massimo rende l'indice conservativo
  verso i falsi "nessun segno" — l'errore più grave nel dominio UPRISE
- **k amplifica il respiro**: `delta` è piccolo (unità di energia); k lo porta nella
  scala 10-30 attesa per la classe "vitalità bassa". È IL parametro da tarare

## 4. Classificazione

| vitality | classe | significato operativo (triage) |
|---|---|---|
| 0-9 | `nessun_segno` | nessuna presenza o nessuna variazione rilevabile |
| 10-39 | `vitalita_bassa` | vivo: respiro/micro-movimenti, non si muove |
| 40-69 | `moderato` | movimenti limitati ma attivi |
| 70-100 | `attivo` | movimento pieno, persona reattiva |

⚠️ Soglie **iniziali e arbitrarie**: la taratura vera si fa sui dati (sotto).
Nella tesi va detto chiaramente: le classi sono un supporto informativo al triage,
NON una diagnosi medica — "nessun_segno" significa "il sensore non rileva variazioni",
non "deceduto" (la persona può essere fuori portata, schermata, svenuta ma viva).

## 5. Sviluppo e taratura — Python prima, C++ poi

Regola: **l'algoritmo si sviluppa su PC, sui CSV, dove si può iterare in secondi.**
Il porting su ESP32 (`vitality.h`) avviene solo a soglie validate.

Percorso (usa i dati della Fase 6 di PIANO_TEST.md):

1. Raccogliere i 4 scenari: `vitalita_0` (stanza vuota), `vitalita_respiro`
   (immobile), `vitalita_micro` (micro-movimenti), `vitalita_attivo` (movimento
   pieno) — 5 trial ciascuno
2. Script `analisi/vitalita_proto.py` (da scrivere in quella fase): implementa
   l'algoritmo §3, lo esegue su tutti i CSV, produce la serie `vitality(t)` per trial
3. **Taratura**: scegliere α_m, α_r, k e le 3 soglie in modo che i 4 scenari cadano
   nelle 4 classi attese. Metodo semplice e difendibile: guardare le distribuzioni
   (boxplot dei valori di vitality per scenario) e mettere le soglie nei "vuoti"
   tra le distribuzioni
4. **Validazione**: matrice di confusione scenario→classe sui trial NON usati per
   la taratura (es. tarare su T01-T03, validare su T04-T05). Metrica di tesi:
   % di campioni classificati nella classe attesa, per scenario
5. Porting in `vitality.h` (stesse costanti) + verifica live con la web UI (step 5)

Il punto 4 dà il numero finale per la tesi: *"l'indice classifica correttamente
l'X% dei campioni su scenari mai visti in taratura"*.

## 6. Casi limite e comportamenti attesi

| Situazione | Comportamento atteso | Note |
|---|---|---|
| Persona esce dal campo | vitality → 0 entro il timeout radar (~5 s) | forzatura su presence=0 |
| Persona si addormenta | attivo → vitalita_bassa in ~30-60 s | le EWMA decadono con le loro costanti |
| Ventilatore/tenda in movimento | falso "moderato" possibile | limite da dichiarare; mitigazione: soglie per-gate del radar |
| Due persone | indice riferito al gate dominante | coerente col limite mono-target del LD2410B |
| Persona oltre 4-5 m | respiro non più rilevabile → sottostima | documentare la distanza massima utile per la classe "vitalita_bassa" (esce dal Test 5.1 a 1 m vs 2 m) |

## 7. Collocazione nella tesi

- Capitolo proprio (o sezione maggiore), DOPO il confronto PIR/mmWave: l'indice è
  la dimostrazione costruttiva che i dati mmWave abilitano ciò che il PIR non può fare
- Contenuto: motivazione triage (§1) → segnali disponibili (§2) → algoritmo e
  razionale (§3-4) → metodo di taratura e risultati (§5) → limiti (§6)
- La web UI compare solo come "consumatore" dell'indice (un paragrafo + screenshot
  della gauge)

## 8. Estensioni possibili (solo se avanza tempo)

- Sostituire il termine respiro EWMA con la **potenza in banda 0.1-0.5 Hz** su una
  finestra scorrevole di 30 s (mini-FFT a bordo): più robusta ma più costosa — v2
- Isteresi sulle classi (una classe cambia solo dopo N secondi stabili) per evitare
  sfarfallio nella UI
- Confidenza affiancata all'indice (funzione della stabilità del gate attivo)
