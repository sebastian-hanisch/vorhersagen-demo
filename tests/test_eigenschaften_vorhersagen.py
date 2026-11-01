"""Eigenschaften, die für jede Eingabe gelten müssen: Schranken von Konsistenz und Robustheit, Monotonie in λ und p, Marker-Garantie, Verfolger, exakte Vorhersage."""

import pytest

import vrs_algorithm as A
import vrs_constants as C
import vrs_evaluation as E
from vrs_scenario import make_sequence, predictions


@pytest.mark.parametrize("b", C.B_OPTIONS)
def test_konsistenz_und_robustheit_liegen_unter_den_schranken(b):
    for lam in C.LAM_OPTIONS:
        assert A.consistency(b, lam) <= 1 + lam + 1e-9, (b, lam)
        assert A.robustness(b, lam) <= 1 + 1 / lam + 1e-9, (b, lam)


@pytest.mark.parametrize("b", C.B_OPTIONS)
def test_mehr_vertrauen_gibt_mehr_robustheit_nach_und_weniger_konsistenzpreis(b):
    lams = C.LAM_OPTIONS
    cons = [A.consistency(b, lam) for lam in lams]
    rob = [A.robustness(b, lam) for lam in lams]
    assert all(x <= y + 1e-9 for x, y in zip(cons, cons[1:]))               # λ wächst: die Konsistenz wird schlechter
    assert all(x >= y - 1e-9 for x, y in zip(rob, rob[1:]))                 # λ wächst: die Robustheit wird besser


@pytest.mark.parametrize("b", C.B_OPTIONS)
def test_lambda_eins_ist_break_even_und_unabhaengig_von_p(b):
    assert A.consistency(b, 1.0) == pytest.approx(2 - 1 / b) and A.robustness(b, 1.0) == pytest.approx(2 - 1 / b)
    vals = {round(A.expected_ratio(b, 1.0, p), 12) for p in C.P_OPTIONS}
    assert len(vals) == 1


@pytest.mark.parametrize("b", C.B_OPTIONS)
def test_erwartete_kosten_monoton_in_lambda_bei_den_extremen_der_fehlerquote(b):
    lams = C.FEHLER_LAMS
    r0 = [A.expected_ratio(b, lam, 0.0) for lam in lams]
    r5 = [A.expected_ratio(b, lam, 0.5) for lam in lams]
    assert all(x <= y + 1e-9 for x, y in zip(r0, r0[1:]))                   # richtige Vorhersage: mehr Vertrauen ist besser
    assert all(x >= y - 1e-9 for x, y in zip(r5, r5[1:]))                   # geratene Vorhersage: weniger Vertrauen ist besser


@pytest.mark.parametrize("b", C.B_OPTIONS)
def test_bestes_vertrauen_waechst_mit_der_fehlerquote(b):
    best = [A.best_lambda(b, p) for p in C.P_OPTIONS]
    assert all(x <= y for x, y in zip(best, best[1:]))
    assert best[0] == C.LAM_OPTIONS[0] and best[-1] == 1.0


def test_erwartete_kosten_sind_mindestens_das_erwartete_optimum():
    for b in C.B_OPTIONS:
        for lam in (0.1, 0.5, 1.0):
            for p in (0.0, 0.5):
                c, o = A.expected_costs(b, lam, p)
                assert c >= o


@pytest.mark.parametrize("vorhersage", C.VORHERSAGEN)
@pytest.mark.parametrize("folge", C.FOLGEN)
@pytest.mark.parametrize("k", [4, 10])
def test_marker_verliert_hoechstens_den_faktor_k_gegen_belady(folge, k, vorhersage):
    """Jedes Marker-Verfahren ist k-kompetitiv, mit beliebiger Vorhersage: Fehler ≤ k · OPT + k."""
    seq = make_sequence(folge, k, 3000, 1)
    pr = predictions(seq, vorhersage, 5)
    opt = sum(A.run_belady(seq, k))
    assert sum(A.run_pred(seq, k, pr, True)) <= k * opt + k


@pytest.mark.parametrize("vorhersage", C.VORHERSAGEN)
@pytest.mark.parametrize("folge", C.FOLGEN)
def test_alle_verfahren_haben_mindestens_die_fehler_von_belady_und_der_verfolger_haelt_die_schranke(folge, vorhersage):
    k = 8
    flags, switches, _ = E.run_b(folge, k, vorhersage, 2, 2500)
    opt = sum(flags["Belady"])
    assert all(len(f) == 2500 for f in flags.values())
    for n in C.VERFAHREN:
        assert sum(flags[n]) >= opt, n
    # Der Verfolger ahmt träge nach: höchstens das bessere der beiden Verfolgten plus k je Wechsel und die Sperre
    best = min(sum(flags["Vorhersage ungeschützt"]), sum(flags["LRU"]))
    assert sum(flags["Verfolger"]) <= best + k + k * (switches + 1)


@pytest.mark.parametrize("folge", C.FOLGEN)
@pytest.mark.parametrize("seed", [0, 3])
def test_bei_exakter_vorhersage_ist_der_verfolger_belady_und_wechselt_nie(folge, seed):
    flags, switches, _ = E.run_b(folge, 10, "exakt", seed, 3000)
    assert sum(flags["Verfolger"]) == sum(flags["Belady"]) == sum(flags["Vorhersage ungeschützt"]) and switches == 0
    assert sum(flags["Belady"]) <= sum(flags["LRU"])


def test_gegnerische_vorhersage_haengt_nicht_vom_seed_ab_zufaellige_schon():
    seq = make_sequence("Zipf", 10, 500, 1)
    assert list(predictions(seq, "gegnerisch", 1)) == list(predictions(seq, "gegnerisch", 2))
    assert list(predictions(seq, "alle zufällig", 1)) != list(predictions(seq, "alle zufällig", 2))
    assert list(predictions(seq, "exakt", 1)) == list(predictions(seq, "exakt", 2))


def test_je_mehr_falsche_vorhersagen_desto_mehr_zufaellige_zeiten():
    seq = make_sequence("Zipf", 10, 2000, 1)
    exakt = predictions(seq, "exakt", 4)
    anteile = [float((predictions(seq, v, 4) != exakt).mean()) for v in ("5 % falsch", "25 % falsch", "50 % falsch", "alle zufällig")]
    assert anteile == sorted(anteile) and anteile[0] < 0.1 and anteile[-1] > 0.9
