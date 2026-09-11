/*
 * vitality.h — indice di vitalita' a bordo (obiettivo 6), porting della v3 di
 * analisi/vitalita_proto.py (funzioni scegli_gate / netta / calcola / classifica).
 *
 * Per campione, a 5 Hz, sul canale MOVING del LD2410B:
 *   g        = gate attivo (dalla distanza riportata, o argmax dell'energia)
 *   e_netta  = max(0, (menergy_gate[g] - fondo[g]) * 100 / (100 - fondo[g]))
 *   mov_ewma = a_m * e_netta + (1 - a_m) * mov_ewma          (primo campione: = e_netta)
 *   var_ewma = a_v * |e_netta - e_netta_prec| + (1 - a_v) * var_ewma
 *   vitality = clamp(mov_ewma + k * var_ewma, 0, 100);  se presenza = 0 -> 0
 *   classe   = bassa (< 45) | moderata (< 95) | alta;   "" se presenza = 0
 *
 * Lo stato (due EWMA e un valore precedente) si aggiorna su OGNI campione, anche a
 * stanza vuota, come nel prototipo: cosi' quando qualcuno entra l'indice non parte da
 * zero simulando un finto "nessun segno". Costanti in config.h, identiche al prototipo.
 * Lo stesso prototipo, eseguito sul CSV esportato dal browser con le stesse costanti,
 * deve ridare l'indice registrato a bordo (colonna `vitality_onboard`): e' la verifica
 * dello step 5.
 */
#pragma once

#include "config.h"
#include "radar_task.h"

static const float VIT_FONDO[9] = VIT_FONDO_GATE;
static const char* const VIT_CLASSI[3] = { "vitalita_bassa", "vitalita_moderata", "vitalita_alta" };

struct VitalityStato {
  bool  avviato = false;
  float movEwma = 0, varEwma = 0, eNettaPrec = 0;
  int   gate = 0;                 // ultimo gate usato, per /info e debug
  float eNetta = 0;               // ultima energia netta
};
static VitalityStato vit;

static int vitGateAttivo(const RadarSample& s) {
#if VIT_GATE_DA_DISTANZA
  // Come il prototipo: distanza del bersaglio fermo se c'e' (piu' stabile), altrimenti
  // quella del moving; se nessuna, ripiego sull'energia.
  uint16_t d = s.sdist ? s.sdist : s.mdist;
  if (d > 0) { int g = d / 75; return g > 8 ? 8 : g; }
#endif
  int gMax = 0;
  for (int i = 1; i < 9; i++) if (s.gatesM[i] > s.gatesM[gMax]) gMax = i;
  return gMax;
}

static float vitNetta(uint8_t valore, float fondo) {
  if (fondo >= 99.0f) return (float)valore;
  float e = ((float)valore - fondo) * 100.0f / (100.0f - fondo);
  return e < 0 ? 0 : e;
}

// Aggiorna lo stato e scrive vitality / vitalityClass nel campione.
static void vitalityUpdate(RadarSample& s) {
  if (!s.radarOk) { s.vitality = 0; s.vitalityClass = ""; return; }
  int g = vitGateAttivo(s);
  float e = vitNetta(s.gatesM[g], VIT_FONDO[g]);
  if (!vit.avviato) {
    vit.movEwma = e; vit.varEwma = 0; vit.eNettaPrec = e; vit.avviato = true;
  } else {
    vit.movEwma = VIT_ALPHA_M * e + (1.0f - VIT_ALPHA_M) * vit.movEwma;
    float varRaw = e > vit.eNettaPrec ? e - vit.eNettaPrec : vit.eNettaPrec - e;
    vit.varEwma = VIT_ALPHA_V * varRaw + (1.0f - VIT_ALPHA_V) * vit.varEwma;
    vit.eNettaPrec = e;
  }
  vit.gate = g; vit.eNetta = e;
  float grezzo = vit.movEwma + VIT_K * vit.varEwma;
  if (grezzo < 0) grezzo = 0;
  if (grezzo > 100) grezzo = 100;
  if (!s.presence) { s.vitality = 0; s.vitalityClass = ""; return; }   // gate di presenza
  s.vitality = (uint8_t)(grezzo + 0.5f);
  s.vitalityClass = grezzo < VIT_SOGLIA_1 ? VIT_CLASSI[0] : grezzo < VIT_SOGLIA_2 ? VIT_CLASSI[1] : VIT_CLASSI[2];
}
