"""Randfälle: kleinste und größte Einstellungen, kurze Folgen, Folgen ohne Fehler, Extremwerte der Regler."""

import pytest

import vrs_algorithm as A
import vrs_constants as C
import vrs_evaluation as ev
from vrs_scenario import make_sequence, predictions


@pytest.mark.parametrize("b", [C.B_OPTIONS[0], C.B_OPTIONS[-1]])
@pytest.mark.parametrize("lam", [C.LAM_OPTIONS[0], C.LAM_OPTIONS[-1]])
@pytest.mark.parametrize("p", [C.P_OPTIONS[0], C.P_OPTIONS[-1]])
def test_teil_a_extreme_einstellungen(b, lam, p):
    a = ev.analyse_a(ev.Settings(b=b, lam=lam, p=p))
    assert a.ratio >= 1.0 and a.cons >= 1.0 and a.rob >= a.cons - 1e-9 and a.best_lam in C.LAM_OPTIONS
    assert a.early <= a.late or lam == 1.0
    kind, text = ev.verdict_a(a)
    assert kind in ("success", "info", "warning") and text


@pytest.mark.parametrize("folge", C.FOLGEN)
@pytest.mark.parametrize("k", [C.K_MIN, C.K_MAX])
def test_teil_b_kleinster_und_groesster_speicher(folge, k):
    b = ev.analyse_b(ev.Settings(folge=folge, k=k))
    assert b.faults["Belady"] <= min(b.faults[n] for n in C.VERFAHREN)
    assert all(len(v) == C.LENGTH for v in b.cum.values()) and b.n_pages >= k


@pytest.mark.parametrize("vorhersage", C.VORHERSAGEN)
@pytest.mark.parametrize("verfahren", C.VERFAHREN)
def test_jede_auswahl_von_teil_b_laeuft(vorhersage, verfahren):
    b = ev.analyse_b(ev.Settings(vorhersage=vorhersage, verfahren=verfahren))
    kind, text = ev.verdict_b(b)
    assert kind in ("success", "info", "warning") and text


def test_sehr_kurze_folgen():
    for length in (1, 2, 5):
        seq = make_sequence("Zipf", 4, length, 0)
        pr = predictions(seq, "25 % falsch", 1)
        flags, _ = A.run_all(seq, 4, pr)
        assert all(len(f) == length for f in flags.values())
        assert flags["Belady"][0] == 1                                       # die erste Anfrage fehlt immer


def test_folge_die_in_den_speicher_passt_hat_nur_die_ersten_fehler():
    seq = [0, 1, 2, 3] * 50
    pr = predictions(seq, "gegnerisch", 0)
    flags, _ = A.run_all(seq, 4, pr)
    assert all(sum(f) == 4 for f in flags.values())                        # vier Seiten, vier Plätze: nur die Erstzugriffe fehlen


def test_ratio_ohne_belady_fehler():
    assert ev.ratio(0, 0) == 1.0 and ev.ratio(3, 0) == float("inf")


@pytest.mark.parametrize("seed", [0, C.SEED_MAX])
def test_grenzen_des_seeds(seed):
    b = ev.analyse_b(ev.Settings(vorhersage="25 % falsch", seed=seed))
    assert b.faults["Belady"] > 0


def test_gleicher_seed_gleiches_ergebnis_anderer_seed_anderes():
    s = ev.Settings(vorhersage="25 % falsch", folge="Arbeitsmengen")
    a, b = ev.analyse_b(s), ev.analyse_b(s)
    assert a.faults == b.faults
    c = ev.analyse_b(ev.Settings(vorhersage="25 % falsch", folge="Arbeitsmengen", seed=8))
    assert c.faults != a.faults
