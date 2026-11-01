"""Orakel: getrennt geschriebene zweite Fassungen (tagweise Simulation, Aufzählung aller Dauern, Listen-LRU, Belady über Positionslisten) gegen den Kern."""

import random
from fractions import Fraction

import pytest

import vrs_algorithm as A
import vrs_constants as C
from vrs_scenario import make_sequence, next_gaps, predictions


def day_by_day(day: int, x: int, b: int) -> int:
    """Tagweise: jeder Tag kostet 1 Miete, am Beginn des Kauftags wird gekauft."""
    total, bought = 0, False
    for d in range(1, x + 1):
        if not bought and d == day:
            total += b
            bought = True
        if not bought:
            total += 1
    return total


@pytest.mark.parametrize("b", C.B_OPTIONS)
@pytest.mark.parametrize("lam", [0.1, 0.25, 0.5, 1.0])
def test_kosten_gleichen_der_tagweisen_simulation(b, lam):
    for pred in (True, False):
        day = A.buy_day(pred, b, lam)
        for x in range(1, min(day + 30, 400)):
            assert A.cost(day, x, b) == day_by_day(day, x, b)


@pytest.mark.parametrize("b", [10, 20])
@pytest.mark.parametrize("lam", [0.1, 0.3, 0.5, 0.75, 1.0])
def test_konsistenz_und_robustheit_gleichen_der_brute_force(b, lam):
    cons = rob = 0.0
    for x in range(1, C.X_FACTOR * b + 1):
        for pred in (True, False):
            q = day_by_day(A.buy_day(pred, b, lam), x, b) / min(x, b)
            rob = max(rob, q)
            if pred == (x >= b):
                cons = max(cons, q)
    assert A.consistency(b, lam) == pytest.approx(cons) and A.robustness(b, lam) == pytest.approx(rob)


@pytest.mark.parametrize("p", [0.0, 0.1, 0.25, 0.5])
@pytest.mark.parametrize("lam", [0.1, 0.5, 1.0])
def test_erwartung_gleicht_der_aufzaehlung_mit_bruechen(lam, p):
    """Alle (Dauer, Klasse der Vorhersage) einzeln mit exaktem Gewicht aufzählen."""
    b = 10
    pf = Fraction(p).limit_denominator(1000)
    short = list(range(1, b))
    long_ = list(range(C.LONG_RANGE[0] * b, C.LONG_RANGE[1] * b))
    cost = opt = Fraction(0)
    for xs, is_long in ((short, False), (long_, True)):
        for x in xs:
            w = Fraction(1, 2) / len(xs)
            for pred_long, wp in ((is_long, 1 - pf), (not is_long, pf)):
                cost += w * wp * day_by_day(A.buy_day(pred_long, b, lam), x, b)
            opt += w * min(x, b)
    assert A.expected_ratio(b, lam, p) == pytest.approx(float(cost / opt))


def belady_by_positions(seq, k):
    """Belady mit Positionslisten je Seite (getrennt von der Abstandsrechnung des Kerns)."""
    pos = {}
    for t, p in enumerate(seq):
        pos.setdefault(p, []).append(t)
    cache, faults = set(), 0
    for t, p in enumerate(seq):
        if p in cache:
            continue
        faults += 1
        if len(cache) == k:
            def nxt(q):
                return next((u for u in pos[q] if u > t), float("inf"))
            cache.remove(max(cache, key=nxt))
        cache.add(p)
    return faults


def lru_by_list(seq, k):
    cache, faults = [], 0
    for p in seq:
        if p in cache:
            cache.remove(p)
            cache.append(p)
            continue
        faults += 1
        if len(cache) == k:
            cache.pop(0)
        cache.append(p)
    return faults


@pytest.mark.parametrize("folge", C.FOLGEN)
@pytest.mark.parametrize("k", [4, 10])
def test_belady_und_lru_gleichen_den_zweiten_fassungen(folge, k):
    seq = make_sequence(folge, k, 1500, 2)
    assert sum(A.run_belady(seq, k)) == belady_by_positions(seq, k)
    assert sum(A.run_lru(seq, k)) == lru_by_list(seq, k)


def test_belady_ist_bei_zufaelligen_folgen_das_optimum_unter_allen_verdraengungen():
    """Aufzählung aller Verdrängungsentscheidungen auf kleinen Folgen: kein Verfahren hat weniger Fehler als Belady."""
    rng = random.Random(4)
    for _ in range(60):
        k = rng.randint(2, 3)
        seq = [rng.randint(0, 4) for _ in range(rng.randint(5, 12))]

        def best(t, cache):
            if t == len(seq):
                return 0
            p = seq[t]
            if p in cache:
                return best(t + 1, cache)
            if len(cache) < k:
                return 1 + best(t + 1, cache | {p})
            return 1 + min(best(t + 1, (cache - {v}) | {p}) for v in cache)

        assert sum(A.run_belady(seq, k)) == best(0, frozenset())


@pytest.mark.parametrize("folge", C.FOLGEN)
def test_naechste_ankunft_gleicht_der_suche_nach_vorn(folge):
    seq = make_sequence(folge, 6, 400, 1)
    gap = next_gaps(seq)
    big = 10 * len(seq)
    for t in range(len(seq)):
        nxt = next((u for u in range(t + 1, len(seq)) if seq[u] == seq[t]), None)
        assert gap[t] == (nxt - t if nxt is not None else big)


@pytest.mark.parametrize("folge", C.FOLGEN)
@pytest.mark.parametrize("k", [4, 10])
@pytest.mark.parametrize("seed", [0, 1])
def test_ungeschuetzt_mit_exakter_vorhersage_ist_belady(folge, k, seed):
    seq = make_sequence(folge, k, 2000, seed)
    pr = predictions(seq, "exakt", seed)
    assert sum(A.run_pred(seq, k, pr, False)) == sum(A.run_belady(seq, k))
