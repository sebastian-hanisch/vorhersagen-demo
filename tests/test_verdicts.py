"""Verdikte: jede Zahl und jede Verzweigung der Texte. Die Verdikte sind reine Funktionen (Art, Text); die Zahlen im Text werden aus den Eingaben nachgerechnet."""

import numpy as np
import pytest

import vrs_constants as C
import vrs_evaluation as ev


def _a(ratio, breakeven=1.63, lam=0.25, p=0.0, best=0.1, best_ratio=1.03, cons=1.2, rob=4.95):
    s = ev.Settings(lam=lam, p=p)
    return ev.AnalysisA(s, ratio, breakeven, best, best_ratio, cons, rob, ratio * 10, 10.0, 5, 80)


def test_verdict_a_zahlen_und_text():
    kind, text = ev.verdict_a(_a(1.13))
    assert kind == "success"
    assert "Bei Vertrauen λ = 0.25 und Fehlerquote 0 % zahlt die Regel im Mittel das **1.13-Fache** des Optimums; ohne Vorhersage (Break-even, λ = 1) sind es 1.63." in text
    assert "Konsistenz 1.20, Robustheit 4.95." in text and "Das beste λ für diese Fehlerquote (bei dieser Dauerverteilung) ist 0.1 (1.03)." in text
    assert "mehr als gar keine Vorhersage" not in text


@pytest.mark.parametrize("ratio,art", [(1.40, "success"), (1.466, "success"), (1.468, "info"), (1.63, "info"), (1.64, "warning"), (2.44, "warning")])
def test_verdict_a_schwellen(ratio, art):
    assert ev.verdict_a(_a(ratio))[0] == art                       # grün bis 90 % der Break-even-Kosten, gelb bis zu ihnen, darüber Warnung


def test_verdict_a_warnung_nennt_den_grund():
    kind, text = ev.verdict_a(_a(2.44, p=0.5, best=1.0, best_ratio=1.63))
    assert kind == "warning" and "Fehlerquote 50 %" in text and "Das Vertrauen kostet hier mehr als gar keine Vorhersage." in text


def test_verdict_kompromiss():
    rows = [{"lam": 0.1, "Konsistenz": 1.05, "Robustheit": 10.95}, {"lam": 1.0, "Konsistenz": 1.95, "Robustheit": 1.95}]
    kind, text = ev.verdict_kompromiss(rows)
    assert kind == "info"
    assert "Bei λ = 0.1 ist die Konsistenz 1.05, die Robustheit aber 10.95; bei λ = 1 sind beide 1.95." in text


def test_verdict_fehler():
    rows = [{"p": 0.0, "bestes lam": 0.1, "Quotienten": {0.1: 1.03, 1.0: 1.63}, "Break-even": 1.63},
            {"p": 0.5, "bestes lam": 1.0, "Quotienten": {0.1: 2.67, 1.0: 1.63}, "Break-even": 1.63}]
    kind, text = ev.verdict_fehler(rows)
    assert kind == "info"
    assert "0 % → λ = 0.1, 50 % → λ = 1" in text and "Bei 50 % falschen Vorhersagen kostet λ = 0.1 das 2.67-Fache des Optimums, die Break-even-Regel 1.63." in text


def _b(verfahren, ratios, faults=None, switches=0, vorhersage="exakt"):
    s = ev.Settings(verfahren=verfahren, vorhersage=vorhersage, folge="Zipf", k=10)
    faults = faults or {**{n: int(r * 100) for n, r in ratios.items()}, "Belady": 100}
    return ev.AnalysisB(s, faults, ratios, {}, switches, 40)


R = {"LRU": 1.75, "Vorhersage ungeschützt": 1.0, "Marker mit Vorhersage": 1.47, "Verfolger": 1.0}


def test_verdict_b_zahlen_und_arten():
    kind, text = ev.verdict_b(_b("Vorhersage ungeschützt", R))
    assert kind == "success"
    assert "**Vorhersage ungeschützt** hat auf „Zipf“ mit k = 10 und Vorhersage „exakt“ **100** Fehler gegen 100 bei Belady: das **1.00-Fache**. LRU liegt bei 1.75." in text
    kind, text = ev.verdict_b(_b("Marker mit Vorhersage", R))
    assert kind == "info" and "1.47-Fache" in text and "schlechter als LRU" not in text
    r = {**R, "Vorhersage ungeschützt": 6.29, "LRU": 2.09}
    kind, text = ev.verdict_b(_b("Vorhersage ungeschützt", r))
    assert kind == "warning" and "Das ist schlechter als LRU ohne jede Vorhersage." in text


def test_verdict_b_verfolger_nennt_die_wechsel():
    kind, text = ev.verdict_b(_b("Verfolger", {**R, "Verfolger": 2.1, "LRU": 2.09}, switches=3))
    assert "Der Verfolger hat 3-mal gewechselt." in text and kind == "warning"
    assert "Der Verfolger hat" not in ev.verdict_b(_b("LRU", R))[1]


def _rows():
    def r(folge, v, lru, pred, mark, fol):
        return {"Folge": folge, "Vorhersage": v, "LRU": lru, "Vorhersage ungeschützt": pred, "Marker mit Vorhersage": mark, "Verfolger": fol}
    return [r("Arbeitsmengen", "exakt", 2.09, 1.0, 1.15, 1.0), r("Arbeitsmengen", "25 % falsch", 2.09, 6.29, 1.58, 2.12),
            r("Arbeitsmengen", "alle zufällig", 2.09, 9.26, 2.11, 2.12), r("Arbeitsmengen", "gegnerisch", 2.09, 9.74, 2.92, 2.12),
            r("Zipf", "exakt", 1.75, 1.0, 1.47, 1.0), r("Zipf", "gegnerisch", 1.75, 2.82, 2.11, 1.75)]


def test_verdict_quali():
    kind, text = ev.verdict_quali(_rows())
    assert kind == "warning"
    assert "mit exakter Vorhersage optimal (1.00), bei 25 % falschen Vorhersagen schon 6.29 (LRU: 2.09) und bei lauter zufälligen 9.26." in text
    assert "Der Marker mit Vorhersage liegt bei 1.15, 1.58 und 2.11." in text


def test_verdict_gegner():
    kind, text = ev.verdict_gegner(_rows())
    assert kind == "warning"
    assert "auf „Arbeitsmengen“ das **9.74-Fache** von Belady (LRU: 2.09); der Marker bleibt bei höchstens 2.92." in text


def test_verdict_konsistenz():
    kind, text = ev.verdict_konsistenz(_rows())
    assert kind == "info"
    assert "Arbeitsmengen 1.15, Zipf 1.47" in text and "LRU zahlt 2.09, 1.75." in text


def test_delta_text_und_fmt_und_ratio():
    assert ev.delta_text(1.13, 1.13, "Break-even") == ("gleich wie Break-even", "off")
    assert ev.delta_text(1.13, 1.63, "Break-even") == ("-0.50 gegen Break-even", "inverse")
    assert ev.fmt(float("inf")) == "unbeschränkt" and ev.fmt(1.5) == "1.50"
    assert ev.ratio(5, 0) == float("inf") and ev.ratio(0, 0) == 1.0 and ev.ratio(3, 2) == 1.5
