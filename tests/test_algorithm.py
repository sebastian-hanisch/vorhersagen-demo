"""Kern von Hand gerechnet: Kauftage, Kosten, Erwartung (Teil A); Verdrängung, Vorhersagen, Marker, Verfolger (Teil B)."""

import pytest

import vrs_algorithm as A
import vrs_constants as C
from vrs_scenario import folge_n, make_sequence, next_gaps, predictions


def test_kauftage_von_hand():
    assert (A.buy_day(True, 20, 0.25), A.buy_day(False, 20, 0.25)) == (5, 80)
    assert (A.buy_day(True, 20, 1.0), A.buy_day(False, 20, 1.0)) == (20, 20)
    assert A.buy_day(True, 20, 0.15) == 3                           # 0,15 · 20 ist in Gleitkomma 3,0000000000000004: gerundet, nicht 4
    assert A.buy_day(False, 20, 0.15) == 134                        # ⌈133,33⌉
    assert A.buy_day(True, 10, 0.1) == 1 and A.buy_day(False, 10, 0.1) == 100


def test_kosten_von_hand():
    assert A.cost(5, 3, 20) == 3                                    # endet vor dem Kauftag: nur Miete
    assert A.cost(5, 5, 20) == 4 + 20                               # Kauf am Tag 5: vier Tage Miete plus Kaufpreis
    assert A.cost(1, 7, 20) == 20                                   # sofort gekauft
    assert A.opt(7, 20) == 7 and A.opt(50, 20) == 20


def test_konsistenz_und_robustheit_von_hand():
    b = 20
    assert A.consistency(b, 1.0) == pytest.approx((19 + 20) / 20)   # Break-even: 2 − 1/B
    assert A.robustness(b, 1.0) == pytest.approx((19 + 20) / 20)
    # λ = 0,5: früh Tag 10, spät Tag 40; richtige Vorhersage: lang bei x = 20 → (9 + 20)/20 = 1,45, kurz bei x = 19 → 19/19 = 1
    assert A.consistency(b, 0.5) == pytest.approx(1.45)
    # falsche Vorhersage „kurz“ bei x = 40: (39 + 20)/20 = 2,95
    assert A.robustness(b, 0.5) == pytest.approx(2.95)


def test_erwartung_von_hand():
    b = 10
    c, o = A.expected_costs(b, 1.0, 0.0)
    # λ = 1: Kauftag 10; kurze Dauern 1..9 (Mittel 5) kosten x, lange Dauern 30..79 kosten 9 + 10 = 19; Optimum: lang 10, kurz Mittel 5
    assert c == pytest.approx(0.5 * 19 + 0.5 * 5) and o == pytest.approx(0.5 * 10 + 0.5 * 5)
    assert A.expected_ratio(b, 1.0, 0.0) == pytest.approx(12 / 7.5)
    # λ = 0,5, p = 0: früh Tag 5, spät Tag 20: lang 4 + 10 = 14, kurz Mittel 5
    assert A.expected_ratio(b, 0.5, 0.0) == pytest.approx((0.5 * 14 + 0.5 * 5) / 7.5)
    # p = 1: immer vertauscht: lang bekommt „kurz“ (Kauftag 20: 19 + 10 = 29), kurz bekommt „lang“ (Kauftag 5: x für x < 5, sonst 14)
    kurz = (1 + 2 + 3 + 4 + 5 * 14) / 9
    assert A.expected_ratio(b, 0.5, 1.0) == pytest.approx((0.5 * 29 + 0.5 * kurz) / 7.5)


def test_bestes_vertrauen_von_hand():
    assert A.best_lambda(20, 0.0) == 0.1                            # bei richtiger Vorhersage: so viel Vertrauen wie möglich
    assert A.best_lambda(20, 0.5) == 1.0                            # bei geratener Vorhersage: keines


def test_lru_und_belady_von_hand():
    seq = [1, 2, 3, 1, 2, 3]
    assert A.run_lru(seq, 2) == [1, 1, 1, 1, 1, 1]
    assert A.run_belady(seq, 2) == [1, 1, 1, 0, 1, 0]              # 3 verdrängt die 2 (kommt später als die 1); 2 verdrängt die 1 (kommt nie wieder)


def test_naechste_ankunft_von_hand():
    seq = [1, 2, 1, 3, 2]
    big = 10 * len(seq)
    assert next_gaps(seq) == [2, 3, big, big, big]
    pr = predictions(seq, "exakt", 0)
    assert list(pr) == [2, 4, 2 + big, 3 + big, 4 + big]
    g = predictions(seq, "gegnerisch", 0)
    assert list(g) == [4999, 4999, 2 + 4951, 3 + 4951, 4 + 4951]     # t + 5001 − min(Abstand, 5000): nahe Ankunft sieht fern aus, die Seiten ohne Wiederkehr (Abstand 50) bekommen 4951


def test_ungeschuetzt_und_marker_unterscheiden_sich_von_hand():
    # k = 2; Anfragen 1, 2, 3, 4 mit Vorhersagen 100, 5, 7, 9. Bei Anfrage 3 sind beide Seiten markiert: neue Phase, verdrängt wird die 1 (Vorhersage 100).
    # Bei Anfrage 4 liegen {2, 3} im Speicher, markiert ist nur die 3: der Marker verdrängt die 2, die ungeschützte Regel die 3 (Vorhersage 7 > 5).
    seq, pr = [1, 2, 3, 4], [100, 5, 7, 9]
    free = A.PredCache(2, False)
    mark = A.PredCache(2, True)
    for page, p in zip(seq, pr):
        free.step(page, p)
        mark.step(page, p)
    assert set(free.pred) == {2, 4} and set(mark.pred) == {3, 4}


def test_verfolger_wechselt_von_hand():
    seq = list(range(10))
    a = ([1] * 10, [frozenset({i}) for i in range(10)])           # A fehlt immer
    b = ([0] * 10, [frozenset({i}) for i in range(10)])           # B fehlt nie (nur ein Gedankenspiel)
    flags, switches = A.run_follower(seq, 4, a, b, slack=3)
    assert switches == 1                                          # nach dem vierten Fehler von A (4 > 0 + 3) wird gewechselt
    assert sum(flags) == 10                                       # der echte Speicher hat hier nur Fehlstarts: alle Seiten sind neu


def test_folgen_haben_die_erwartete_groesse_und_sind_reproduzierbar():
    assert [folge_n(f, 10) for f in C.FOLGEN] == [40, 12, 11]
    for f in C.FOLGEN:
        s = make_sequence(f, 10, 500, 3)
        assert len(s) == 500 and s == make_sequence(f, 10, 500, 3) and s != make_sequence(f, 10, 500, 4)
    assert set(make_sequence("Schleife mit Fremdzugriffen", 10, 500, 1)) >= set(range(11))
