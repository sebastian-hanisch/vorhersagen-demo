"""Anfragefolgen (wie in der Paging-Demo, Größe aus k abgeleitet) und die Vorhersagen der nächsten Ankunft."""

import numpy as np

import vrs_constants as C


def folge_n(folge: str, k: int) -> int:
    """Zahl der Seiten, die die Folge nutzt: Zipf 4k, Arbeitsmengen k + 2, Schleife k + 1."""
    return {"Zipf": 4 * k, "Arbeitsmengen": k + 2, "Schleife mit Fremdzugriffen": k + 1}[folge]


def make_sequence(folge: str, k: int, length: int, seed: int) -> list[int]:
    n = folge_n(folge, k)
    rng = np.random.default_rng([seed, length, n])
    if folge == "Zipf":
        w = 1.0 / np.arange(1, n + 1) ** C.ZIPF_ALPHA
        return [int(x) for x in rng.choice(n, size=length, p=w / w.sum())]
    if folge == "Arbeitsmengen":
        universe = C.UNIVERSE_FACTOR * n
        out: list[int] = []
        while len(out) < length:
            pool = rng.choice(universe, size=n, replace=False)
            out += [int(x) for x in rng.choice(pool, size=C.PHASE_LEN)]
        return out[:length]
    if folge == "Schleife mit Fremdzugriffen":
        foreign = rng.random(length) < C.FOREIGN_SHARE
        pages = rng.integers(n, n + C.FOREIGN_RANGE, length)
        return [int(pages[i]) if foreign[i] else i % n for i in range(length)]
    raise ValueError(f"unbekannte Folge: {folge}")


def next_gaps(seq) -> list[int]:
    """gap[t]: Schritte bis zur nächsten Anfrage derselben Seite wie in Schritt t (sehr groß, wenn keine mehr kommt)."""
    big = 10 * len(seq)
    last: dict[int, int] = {}
    gap = [big] * len(seq)
    for t in range(len(seq) - 1, -1, -1):
        p = seq[t]
        gap[t] = (last[p] - t) if p in last else big
        last[p] = t
    return gap


def predictions(seq, vorhersage: str, seed: int) -> np.ndarray:
    """Vorhersage der Ankunftszeit (absolute Zeit), abgegeben in Schritt t für die Seite seq[t]."""
    T = len(seq)
    gap = np.array(next_gaps(seq), dtype=float)
    t = np.arange(T)
    if vorhersage == "gegnerisch":
        cap = np.minimum(gap, C.GEGNER_CAP)
        return t + (C.GEGNER_CAP + 1 - cap)                  # nahe Ankunft sieht fern aus und umgekehrt
    p = C.VORHERSAGE_ANTEIL[vorhersage]
    if p == 0.0:
        return t + gap
    rng = np.random.default_rng([seed, T, 77])
    bad = rng.random(T) < p
    rnd = t + rng.integers(1, C.RANDOM_SPAN + 1, T)
    return np.where(bad, rnd, t + gap)
