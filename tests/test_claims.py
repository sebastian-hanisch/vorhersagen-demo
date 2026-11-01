"""Claims: jede Zahl der README, über dieselben Auswertungsfunktionen wie in der App nachgerechnet (Teil A exakt, Teil B mit festen Seeds)."""

import pytest

import vrs_algorithm as A
import vrs_constants as C
import vrs_evaluation as ev

LRU, UNG, MARK, FOLG = C.VERFAHREN
VORH = list(C.VORHERSAGEN)                                            # exakt, 5 %, 25 %, 50 %, alle zufällig, gegnerisch


def r2(x):
    return round(x, 2)


@pytest.fixture(scope="module")
def quali():
    return ev.quali_rows()


def _col(rows, folge, n):
    by = {r["Vorhersage"]: r[n] for r in rows if r["Folge"] == folge}
    return [r2(by[v]) for v in VORH]


def test_kompromisskurve():
    rows = {r["lam"]: r for r in ev.kompromiss_rows()}
    lams = (0.1, 0.25, 0.5, 0.75, 1.0)
    assert [r2(rows[l]["Konsistenz"]) for l in lams] == [1.05, 1.20, 1.45, 1.70, 1.95]
    assert [r2(rows[l]["Robustheit"]) for l in lams] == [10.95, 4.95, 2.95, 2.30, 1.95]
    assert all(rows[l]["Konsistenz"] <= rows[l]["Schranke Konsistenz"] and rows[l]["Robustheit"] <= rows[l]["Schranke Robustheit"] for l in lams)
    assert r2(2 - 1 / 20) == 1.95


def test_fehlerquote_und_vertrauen():
    rows = {r["p"]: r for r in ev.fehler_rows()}
    ps = (0.0, 0.1, 0.25, 0.5)
    assert [r2(rows[p]["Quotienten"][0.1]) for p in ps] == [1.03, 1.36, 1.85, 2.67]
    assert [r2(rows[p]["Quotienten"][0.5]) for p in ps] == [1.30, 1.43, 1.61, 1.93]
    assert [r2(rows[p]["Quotienten"][1.0]) for p in ps] == [1.63] * 4
    assert [rows[p]["bestes lam"] for p in ps] == [0.1, 0.1, 0.65, 1.0]


def test_vorhersage_geraten_und_richtig():
    s = ev.Settings(lam=0.25, p=0.5)
    a = ev.analyse_a(s)
    assert r2(a.ratio) == 2.44 and r2(a.breakeven) == 1.63
    assert r2(ev.analyse_a(ev.Settings(lam=0.25, p=0.0)).ratio) == 1.13


def test_arbeitsmengen(quali):
    assert _col(quali, "Arbeitsmengen", UNG) == [1.00, 1.68, 6.29, 7.75, 9.26, 9.74]
    assert set(_col(quali, "Arbeitsmengen", LRU)) == {2.09}
    assert _col(quali, "Arbeitsmengen", MARK) == [1.15, 1.26, 1.58, 1.83, 2.11, 2.92]
    assert _col(quali, "Arbeitsmengen", FOLG) == [1.00, 1.68, 2.12, 2.12, 2.12, 2.12]
    mark = _col(quali, "Arbeitsmengen", MARK)
    fol = _col(quali, "Arbeitsmengen", FOLG)
    assert all(fol[i] > mark[i] for i in (1, 2, 3)) and fol[5] < mark[5]               # Verfolger über dem Marker bei 5 bis 50 % falsch, darunter bei gegnerischer Vorhersage
    assert all(m < 2.09 for m in mark[:4]) and mark[5] > 2.09                       # unter LRU bis 50 % falsch, darüber bei gegnerischer Vorhersage
    ung = _col(quali, "Arbeitsmengen", UNG)
    assert ung[2] > 2.09 and ung[1] < 2.09                                          # ab 25 % klar über LRU, bei 5 % noch darunter


def test_zipf_und_schleife(quali):
    assert _col(quali, "Zipf", UNG) == [1.00, 1.06, 1.29, 1.58, 2.15, 2.82]
    assert _col(quali, "Zipf", MARK) == [1.47, 1.49, 1.56, 1.64, 1.79, 2.11]
    assert set(_col(quali, "Zipf", LRU)) == {1.75}
    s = "Schleife mit Fremdzugriffen"
    assert _col(quali, s, UNG) == [1.00, 1.77, 3.69, 4.39, 4.85, 4.96]
    assert _col(quali, s, MARK) == [1.36, 1.46, 1.79, 2.05, 2.41, 2.06]
    assert set(_col(quali, s, LRU)) == {5.00}
    assert all(u <= 5.00 for u in _col(quali, s, UNG))                              # nie über LRU


def test_preis_der_konsistenz(quali):
    exakt = {r["Folge"]: r for r in quali if r["Vorhersage"] == "exakt"}
    assert [r2(exakt[f][MARK]) for f in C.FOLGEN] == [1.47, 1.15, 1.36]
    assert all(r2(exakt[f][UNG]) == 1.00 and r2(exakt[f][FOLG]) == 1.00 for f in C.FOLGEN)


def test_presets_teil_b():
    b = ev.analyse_b(ev.Settings(**C.PRESETS["Arbeitsmengen, 25 % falsch"]))
    assert b.faults == {LRU: 1150, UNG: 3710, MARK: 886, FOLG: 1159, "Belady": 557} and b.switches == 1
    assert [r2(b.ratios[n]) for n in C.VERFAHREN] == [2.06, 6.66, 1.59, 2.08]
    g = ev.analyse_b(ev.Settings(**C.PRESETS["Gegnerische Vorhersage"]))
    assert g.faults == {LRU: 1150, UNG: 5359, MARK: 1642, FOLG: 1162, "Belady": 557}
    assert [r2(g.ratios[n]) for n in C.VERFAHREN] == [2.06, 9.62, 2.95, 2.09]


def test_zahlen_der_methodik():
    assert C.LENGTH == 6000 and C.EXP_SEEDS == 4 and C.EXP_K == 10 and C.DEFAULT_B == 20 and C.X_FACTOR == 30
    assert C.FEHLER_PS == (0.0, 0.1, 0.25, 0.5) and C.LONG_RANGE == (3, 8) and C.SHARE_LONG == 0.5
    assert A.buy_day(True, 20, 0.25) == 5
