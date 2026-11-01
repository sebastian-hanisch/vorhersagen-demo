"""Kern. Teil A: Mieten oder Kaufen mit Vorhersage (Regel mit Vertrauen λ). Teil B: Paging mit Vorhersage der nächsten Ankunft.

Teil A: Miete 1 je Tag, Kaufpreis B; die Nutzung dauert x Tage, das Optimum mit Vorwissen kostet min(x, B). Sagt die Vorhersage „länger als B Tage“,
wird früh gekauft (Tag ⌈λB⌉), sonst spät (Tag ⌈B/λ⌉); λ = 1 ist die Break-even-Regel. Alle Erwartungen sind exakt (Summen über alle Dauern).
Teil B: jede Regel liefert je Anfrage ein Fehler-Flag (1 = Seite fehlte); Belady ist das Optimum mit Vorwissen."""

import math
from collections import OrderedDict

import numpy as np

import vrs_constants as C
from vrs_scenario import next_gaps

# ---------------------------------------------------------------------------------------------------------------------------------
# Teil A


def buy_day(long_prediction: bool, b: int, lam: float) -> int:
    """Kauftag: früh (⌈λB⌉, mindestens 1) bei der Vorhersage „lang“, spät (⌈B/λ⌉) bei „kurz“. Gerundet, damit 0,15 · 20 nicht auf 4 statt 3 fällt."""
    if long_prediction:
        return max(1, math.ceil(round(lam * b, 9)))
    return math.ceil(round(b / lam, 9))


def cost(day: int, x: int, b: int) -> int:
    """Kosten der Regel „kaufe am Tag `day`“ bei Dauer x: endet die Nutzung vorher, wird nie gekauft."""
    return x if x < day else (day - 1) + b


def opt(x: int, b: int) -> int:
    return min(x, b)


def consistency(b: int, lam: float) -> float:
    """Schlechtester Quotient bei **richtiger** Vorhersage (lang ⇔ x ≥ B), maximal über alle Dauern bis X_FACTOR · B."""
    best = 0.0
    for x in range(1, C.X_FACTOR * b + 1):
        best = max(best, cost(buy_day(x >= b, b, lam), x, b) / opt(x, b))
    return best


def robustness(b: int, lam: float) -> float:
    """Schlechtester Quotient über alle Dauern und **beide** Vorhersagen, auch die falsche."""
    best = 0.0
    for x in range(1, C.X_FACTOR * b + 1):
        for pred in (True, False):
            best = max(best, cost(buy_day(pred, b, lam), x, b) / opt(x, b))
    return best


def _mean_cost(xs: np.ndarray, day: int, b: int) -> float:
    return float(np.where(xs < day, xs, (day - 1) + b).mean())


def duration_sets(b: int):
    """Die beiden Dauermengen: kurz (1 bis B − 1) und lang (3B bis 8B − 1), je gleich wahrscheinlich."""
    return np.arange(1, b), np.arange(C.LONG_RANGE[0] * b, C.LONG_RANGE[1] * b)


def expected_costs(b: int, lam: float, p: float) -> tuple[float, float]:
    """(erwartete Kosten, erwartete Optimumskosten) bei Anteil `SHARE_LONG` langer Dauern und Vertauschungswahrscheinlichkeit p der Vorhersage."""
    short, long_ = duration_sets(b)
    early, late = buy_day(True, b, lam), buy_day(False, b, lam)
    s = C.SHARE_LONG
    cost_long = (1 - p) * _mean_cost(long_, early, b) + p * _mean_cost(long_, late, b)
    cost_short = (1 - p) * _mean_cost(short, late, b) + p * _mean_cost(short, early, b)
    e_opt = s * float(np.minimum(long_, b).mean()) + (1 - s) * float(np.minimum(short, b).mean())
    return s * cost_long + (1 - s) * cost_short, e_opt


def expected_ratio(b: int, lam: float, p: float) -> float:
    c, o = expected_costs(b, lam, p)
    return c / o


def best_lambda(b: int, p: float, lams=C.LAM_OPTIONS) -> float:
    """Vertrauen mit dem kleinsten erwarteten Quotienten (bei Gleichstand das kleinste λ)."""
    vals = [expected_ratio(b, lam, p) for lam in lams]
    return lams[int(np.argmin(vals))]


# ---------------------------------------------------------------------------------------------------------------------------------
# Teil B


def run_lru(seq, k):
    cache: OrderedDict = OrderedDict()
    flags = []
    for p in seq:
        if p in cache:
            cache.move_to_end(p)
            flags.append(0)
        else:
            flags.append(1)
            if len(cache) == k:
                cache.popitem(last=False)
            cache[p] = True
    return flags


def run_belady(seq, k):
    gap = next_gaps(seq)
    cache: dict[int, int] = {}                       # Seite -> tatsächliche nächste Ankunft
    flags = []
    for t, p in enumerate(seq):
        if p in cache:
            cache[p] = t + gap[t]
            flags.append(0)
            continue
        flags.append(1)
        if len(cache) == k:
            del cache[max(cache, key=cache.get)]
        cache[p] = t + gap[t]
    return flags


class PredCache:
    """Zwischenspeicher, der nach der Vorhersage verdrängt: ungeschützt (`marker` falsch) oder als Marker (nur unmarkierte Seiten dürfen weichen)."""

    def __init__(self, k: int, marker: bool):
        self.k, self.marker = k, marker
        self.pred: dict[int, float] = {}
        self.marked: set[int] = set()

    def step(self, page: int, pr: float) -> int:
        hit = page in self.pred
        if not hit and len(self.pred) == self.k:
            pool = list(self.pred)
            if self.marker:
                unmarked = [q for q in pool if q not in self.marked]
                if not unmarked:                      # alle markiert: neue Phase
                    self.marked.clear()
                    unmarked = pool
                pool = unmarked
            victim = max(pool, key=lambda q: self.pred[q])
            del self.pred[victim]
            self.marked.discard(victim)
        self.pred[page] = pr
        if self.marker:
            self.marked.add(page)
        return 0 if hit else 1


def run_pred(seq, k, pr, marker: bool, states: bool = False):
    c = PredCache(k, marker)
    flags, caches = [], []
    for t, page in enumerate(seq):
        flags.append(c.step(page, pr[t]))
        if states:
            caches.append(frozenset(c.pred))
    return (flags, caches) if states else flags


def lru_states(seq, k):
    cache: OrderedDict = OrderedDict()
    flags, caches = [], []
    for p in seq:
        if p in cache:
            cache.move_to_end(p)
            flags.append(0)
        else:
            flags.append(1)
            if len(cache) == k:
                cache.popitem(last=False)
            cache[p] = True
        caches.append(frozenset(cache))
    return flags, caches


def run_follower(seq, k, a, b, slack: int | None = None):
    """Der echte Speicher ahmt träge den Verfolgten nach (a, b = (Flags, Speicherzustände) der beiden Verfahren). Gewechselt wird erst,
    wenn der andere um mehr als `slack` (Standard k) Fehler besser liegt. Rückgabe: Flags und die Zahl der Wechsel."""
    slack = k if slack is None else slack
    cache: set[int] = set()
    flags: list[int] = []
    ca = cb = 0
    cur, switches = 0, 0
    for t, page in enumerate(seq):
        ca += a[0][t]
        cb += b[0][t]
        if cur == 0 and cb + slack < ca:
            cur, switches = 1, switches + 1
        elif cur == 1 and ca + slack < cb:
            cur, switches = 0, switches + 1
        target = (a if cur == 0 else b)[1][t]
        if page in cache:
            flags.append(0)
            continue
        flags.append(1)
        if len(cache) == k:
            outside = [q for q in cache if q not in target]
            victim = outside[0] if outside else next(iter(cache))
            cache.remove(victim)
        cache.add(page)
    return flags, switches


def run_all(seq, k, pr):
    """Alle vier Verfahren und Belady: Fehler-Flags je Verfahren, dazu die Zahl der Wechsel des Verfolgers."""
    lru_f, lru_c = lru_states(seq, k)
    pred_f, pred_c = run_pred(seq, k, pr, False, states=True)
    mark_f = run_pred(seq, k, pr, True)
    fol_f, switches = run_follower(seq, k, (pred_f, pred_c), (lru_f, lru_c))
    return {"LRU": lru_f, "Vorhersage ungeschützt": pred_f, "Marker mit Vorhersage": mark_f, "Verfolger": fol_f, "Belady": run_belady(seq, k)}, switches
