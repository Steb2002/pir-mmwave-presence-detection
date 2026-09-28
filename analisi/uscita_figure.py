"""
Dove e con che nome finiscono le figure generate dagli script di analisi.

Le PNG a 300 dpi vanno direttamente in overleaf/figures/, con il nome usato nei
\\includegraphics dei capitoli, cosi' la tesi usa subito la versione rigenerata.
I PDF vettoriali vanno in overleaf/figures/origin/: fuori dal \\graphicspath, quindi
LaTeX non li sceglie al posto delle PNG, ma restano disponibili come sorgente.

Le figure che la tesi non usa mantengono il nome figNN_* dello script.
"""
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PNG = RADICE / "overleaf" / "figures"
PDF = PNG / "origin"

# nome nello script -> nome nel tex
NOMI = {
    "fig01_dose_risposta": "Dose_risposta",
    "fig02_timeline_sotto_banco": "Timeline_sotto_banco",
    "fig04_distanza_regressione": "Distanza_regressione",
    "fig05_energia_distanza": "Energia_distanza",
    "fig06_latenze": "Latenze",
    "fig07_impulsi_pir": "Impulsi_pir",
    "fig08_due_persone": "Due_persone",
    "fig09_selettivita": "Selettivita",
    "fig10_gate_engineering": "Energia_gate_2410B",
    "fig11_saturazione": "Saturazione_segnale",
    "fig12_respiro": "Respiro",
    "fig13_consumi": "Consumi",
    "fig14_portata_ostacoli": "Portata_ostacoli",
    "fig15_attenuazione_materiali": "Attenuazione_materiali",
    "fig17_portata_tre_sensori": "Portata_tre_sensori",
    "fig18_falsi_positivi": "Falsi_positivi",
    "fig19_dipme_tre_sensori": "Dipme_tre_sensori",
    "fig20_angolare": "Angolare",
    "fig21_vitalita_scenari": "Vitalita_scenari",
    "fig22_vitalita_bordo": "Vitalita_bordo",
    "fig27_geometrie": "Geometrie",
    "fig28_collegamenti": "Collegamenti",
    "fig28_tipo_movimento": "Tipo_movimento",
    "fig30_percorsi_dati": "Percorsi_dati",
    "fig32_transitorio": "Transitorio",
}


def nome_file(nome):
    """Nome del file (senza estensione) per la figura che lo script chiama `nome`."""
    return NOMI.get(nome, nome)


def salva(fig, nome):
    """PNG a 300 dpi in overleaf/figures/, PDF vettoriale in overleaf/figures/origin/.

    Senza data di creazione nei metadati: rigenerando una figura con gli stessi dati
    si ottengono file identici, e git non segnala modifiche che non ci sono.
    """
    import matplotlib.pyplot as plt
    PDF.mkdir(parents=True, exist_ok=True)
    n = nome_file(nome)
    fig.savefig(PNG / f"{n}.png", dpi=300, bbox_inches="tight", metadata={"Software": None})
    fig.savefig(PDF / f"{n}.pdf", bbox_inches="tight", metadata={"CreationDate": None, "Creator": None})
    plt.close(fig)
    print(f"  ok  {n}.png (+ origin/{n}.pdf)")
