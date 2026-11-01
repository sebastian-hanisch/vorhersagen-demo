"""Kennzahlen, Verdikt-Logik und Experimente. Verdikte sind reine Funktionen (Art, Text); tests/test_verdicts.py prüft jede Zahl darin."""

from dataclasses import dataclass

import numpy as np

import vrs_algorithm as A
import vrs_constants as C
from vrs_scenario import make_sequence, predictions


@dataclass(frozen=True)
class Settings:
    b: int = C.DEFAULT_B
    lam: float = C.DEFAULT_LAM
    p: float = C.DEFAULT_P
    folge: str = C.DEFAULT_FOLGE
    k: int = C.DEFAULT_K
    vorhersage: str = C.DEFAULT_VORHERSAGE
    verfahren: str = C.DEFAULT_VERFAHREN
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class AnalysisA:
    settings: Settings
    ratio: float                  # erwarteter Quotient E[Kosten] / E[OPT] des gewählten λ
    breakeven: float              # dasselbe für λ = 1 (ohne Vorhersage)
    best_lam: float
    best_ratio: float
    cons: float                   # Konsistenz (richtige Vorhersage, schlechteste Dauer)
    rob: float                    # Robustheit (beliebige Vorhersage, schlechteste Dauer)
    e_cost: float
    e_opt: float
    early: int                    # Kauftag bei der Vorhersage „lang“
    late: int                     # Kauftag bei „kurz“


@dataclass(frozen=True)
class AnalysisB:
    settings: Settings
    faults: dict                  # Verfahren (und „Belady“) -> Zahl der Fehler
    ratios: dict                  # Verfahren -> Fehler / Belady
    cum: dict                     # Verfahren -> kumulierte Fehler je Anfrage
    switches: int                 # Wechsel des Verfolgers
    n_pages: int


def ratio(value: float, ref: float) -> float:
    """Verhältnis zur Referenz; ohne Fehler der Referenz ist 1 der neutrale Wert, wenn auch das Verfahren keine hat, sonst unendlich."""
    if ref <= 0:
        return 1.0 if value <= 0 else float("inf")
    return value / ref


def analyse_a(s: Settings) -> AnalysisA:
    e_cost, e_opt = A.expected_costs(s.b, s.lam, s.p)
    best = A.best_lambda(s.b, s.p)
    return AnalysisA(s, e_cost / e_opt, A.expected_ratio(s.b, 1.0, s.p), best, A.expected_ratio(s.b, best, s.p), A.consistency(s.b, s.lam), A.robustness(s.b, s.lam),
                     e_cost, e_opt, A.buy_day(True, s.b, s.lam), A.buy_day(False, s.b, s.lam))


def run_b(folge: str, k: int, vorhersage: str, seed: int, length: int = C.LENGTH):
    from vrs_scenario import folge_n

    seq = make_sequence(folge, k, length, seed)
    pr = predictions(seq, vorhersage, seed + 100)
    flags, switches = A.run_all(seq, k, pr)
    return flags, switches, folge_n(folge, k)


def analyse_b(s: Settings) -> AnalysisB:
    flags, switches, n = run_b(s.folge, s.k, s.vorhersage, s.seed)
    faults = {name: int(sum(f)) for name, f in flags.items()}
    ratios = {name: ratio(faults[name], faults["Belady"]) for name in C.VERFAHREN}
    cum = {name: np.cumsum(f).tolist() for name, f in flags.items()}
    return AnalysisB(s, faults, ratios, cum, switches, n)


# ---------------------------------------------------------------------------------------------------------------------------------
# Experimente mit festen Folgen und Seeds


def kompromiss_rows(b: int = C.DEFAULT_B, lams=C.KOMPROMISS_LAMS) -> list[dict]:
    """Experiment A1: Konsistenz und Robustheit über λ (exakt, schlechteste Dauer), dazu die Schranken 1 + λ und 1 + 1/λ."""
    return [{"lam": lam, "Konsistenz": A.consistency(b, lam), "Robustheit": A.robustness(b, lam), "Schranke Konsistenz": 1 + lam, "Schranke Robustheit": 1 + 1 / lam} for lam in lams]


def fehler_rows(b: int = C.DEFAULT_B, lams=C.FEHLER_LAMS, ps=C.FEHLER_PS) -> list[dict]:
    """Experiment A2: erwarteter Quotient je Fehlerquote p und Vertrauen λ (exakt), dazu das beste λ aus dem ganzen Gitter."""
    rows = []
    for p in ps:
        best = A.best_lambda(b, p)
        rows.append({"p": p, "Quotienten": {lam: A.expected_ratio(b, lam, p) for lam in lams}, "bestes lam": best, "bester Quotient": A.expected_ratio(b, best, p), "Break-even": A.expected_ratio(b, 1.0, p)})
    return rows


def quali_rows(k: int = C.EXP_K, seeds: int = C.EXP_SEEDS, folgen=C.FOLGEN, vorhersagen=C.VORHERSAGEN, length: int = C.LENGTH) -> list[dict]:
    """Experimente B1 bis B3: Fehler geteilt durch Belady je Folge und Vorhersageart, Mittel über feste Seeds."""
    rows = []
    for folge in folgen:
        for v in vorhersagen:
            acc = {n: [] for n in C.VERFAHREN}
            for seed in range(seeds):
                flags, _, _ = run_b(folge, k, v, seed, length)
                opt = sum(flags["Belady"])
                for n in C.VERFAHREN:
                    acc[n].append(ratio(sum(flags[n]), opt))
            rows.append({"Folge": folge, "Vorhersage": v, **{n: float(np.mean(acc[n])) for n in C.VERFAHREN}})
    return rows


# ---------------------------------------------------------------------------------------------------------------------------------
# Verdikte (rein: Art, Text)


def delta_text(value: float, reference: float, label: str) -> tuple[str, str]:
    """Text und Farbregel des Deltas: „mein Wert minus Referenz“. Gleiche Werte (auf zwei Stellen) bekommen keinen Pfeil und keine Farbe."""
    d = value - reference
    if abs(d) < 0.005:
        return f"gleich wie {label}", "off"
    return f"{d:+.2f} gegen {label}", "inverse"


def fmt(x: float) -> str:
    return "unbeschränkt" if x == float("inf") else f"{x:.2f}"


def verdict_a(a: AnalysisA) -> tuple[str, str]:
    """Kernfrage Teil A: Zahlt sich das Vertrauen in die Vorhersage bei dieser Fehlerquote aus?"""
    s = a.settings
    text = (f"Bei Vertrauen λ = {s.lam:g} und Fehlerquote {s.p * 100:.0f} % zahlt die Regel im Mittel das **{a.ratio:.2f}-Fache** des Optimums; ohne Vorhersage (Break-even, λ = 1) sind es {a.breakeven:.2f}. "
            f"Konsistenz {a.cons:.2f}, Robustheit {a.rob:.2f}. Das beste λ für diese Fehlerquote ist {a.best_lam:g} ({a.best_ratio:.2f}).")
    if a.ratio <= 0.9 * a.breakeven:
        kind = "success"
    elif a.ratio <= a.breakeven + 1e-9:
        kind = "info"
    else:
        kind = "warning"
        text += " Das Vertrauen kostet hier mehr als gar keine Vorhersage."
    return kind, text


def verdict_kompromiss(rows: list[dict]) -> tuple[str, str]:
    """Experiment A1: der Kompromiss."""
    a, b = rows[0], rows[-1]
    return "info", (f"Bei λ = {a['lam']:g} ist die Konsistenz {a['Konsistenz']:.2f}, die Robustheit aber {a['Robustheit']:.2f}; bei λ = {b['lam']:g} sind beide {b['Konsistenz']:.2f}. "
                    f"Beide Kurven liegen unter ihren Schranken 1 + λ und 1 + 1/λ: Wer der Vorhersage mehr traut, gewinnt bei richtiger Vorhersage und verliert im schlechtesten Fall.")


def verdict_fehler(rows: list[dict]) -> tuple[str, str]:
    """Experiment A2: das beste Vertrauen hängt von der Fehlerquote ab."""
    teile = ", ".join(f"{r['p'] * 100:.0f} % → λ = {r['bestes lam']:g}" for r in rows)
    schlecht = rows[-1]
    lam_min = min(schlecht["Quotienten"])
    return "info", (f"Bestes Vertrauen je Fehlerquote: {teile}. Bei {schlecht['p'] * 100:.0f} % falschen Vorhersagen kostet λ = {lam_min:g} das {schlecht['Quotienten'][lam_min]:.2f}-Fache des Optimums, "
                    f"die Break-even-Regel {schlecht['Break-even']:.2f}.")


def verdict_b(b: AnalysisB) -> tuple[str, str]:
    """Kernfrage Teil B: Wie viel kostet das Verfahren gegenüber Belady, und gegenüber LRU?"""
    s = b.settings
    q = b.ratios[s.verfahren]
    lru = b.ratios["LRU"]
    text = (f"**{s.verfahren}** hat auf „{s.folge}“ mit k = {s.k} und Vorhersage „{s.vorhersage}“ **{b.faults[s.verfahren]}** Fehler gegen {b.faults['Belady']} bei Belady: das **{fmt(q)}-Fache**. "
            f"LRU liegt bei {fmt(lru)}.")
    if s.verfahren == "Verfolger":
        text += f" Der Verfolger hat {b.switches}-mal gewechselt."
    if q <= 1.0 + 1e-9:
        kind = "success"
    elif q <= lru + 1e-9:
        kind = "info"
    else:
        kind = "warning"
        text += " Das ist schlechter als LRU ohne jede Vorhersage."
    return kind, text


def _row(rows, folge, vorhersage):
    return next(r for r in rows if r["Folge"] == folge and r["Vorhersage"] == vorhersage)


def verdict_quali(rows: list[dict]) -> tuple[str, str]:
    """Experiment B1: Qualität der Vorhersage auf den Arbeitsmengen."""
    exakt = _row(rows, "Arbeitsmengen", "exakt")
    f25 = _row(rows, "Arbeitsmengen", "25 % falsch")
    zufall = _row(rows, "Arbeitsmengen", "alle zufällig")
    return "warning", (f"Auf den Arbeitsmengen ist die ungeschützte Regel mit exakter Vorhersage optimal ({exakt['Vorhersage ungeschützt']:.2f}), bei 25 % falschen Vorhersagen schon {f25['Vorhersage ungeschützt']:.2f} (LRU: {f25['LRU']:.2f}) "
                       f"und bei lauter zufälligen {zufall['Vorhersage ungeschützt']:.2f}. Der Marker mit Vorhersage liegt bei {exakt['Marker mit Vorhersage']:.2f}, {f25['Marker mit Vorhersage']:.2f} und {zufall['Marker mit Vorhersage']:.2f}.")


def verdict_gegner(rows: list[dict]) -> tuple[str, str]:
    """Experiment B2: gegnerische Vorhersage."""
    sub = [r for r in rows if r["Vorhersage"] == C.GEGNER_VORHERSAGE]
    worst = max(sub, key=lambda r: r["Vorhersage ungeschützt"])
    best_marker = max(r["Marker mit Vorhersage"] for r in sub)
    return "warning", (f"Bei gegnerischer Vorhersage wird die ungeschützte Regel auf „{worst['Folge']}“ das **{worst['Vorhersage ungeschützt']:.2f}-Fache** von Belady (LRU: {worst['LRU']:.2f}); "
                       f"der Marker bleibt bei höchstens {best_marker:.2f}.")


def verdict_konsistenz(rows: list[dict]) -> tuple[str, str]:
    """Experiment B3: der Preis der Konsistenz bei exakter Vorhersage."""
    sub = [r for r in rows if r["Vorhersage"] == "exakt"]
    marker = ", ".join(f"{r['Folge']} {r['Marker mit Vorhersage']:.2f}" for r in sub)
    lru = ", ".join(f"{r['LRU']:.2f}" for r in sub)
    return "info", (f"Bei exakter Vorhersage sind die ungeschützte Regel und der Verfolger optimal (1,00), der Marker mit Vorhersage zahlt einen Preis: {marker}. LRU zahlt {lru}.")
