"""Konstanten: Regler-Grenzen, feste Annahmen, Experimente, Farben und Presets."""

# Teil A: Mieten oder Kaufen mit Vorhersage
B_OPTIONS = (10, 20, 50)
DEFAULT_B = 20
LAM_OPTIONS = tuple(round(0.1 + 0.05 * i, 2) for i in range(19))     # 0,10 bis 1,00
DEFAULT_LAM = 0.25
P_OPTIONS = tuple(round(0.05 * i, 2) for i in range(11))             # 0,00 bis 0,50
DEFAULT_P = 0.0
LONG_RANGE = (3, 8)            # lange Nutzung: 3B bis 8B − 1 Tage, gleich wahrscheinlich
SHARE_LONG = 0.5               # Anteil der langen Nutzungen
X_FACTOR = 30                  # größte betrachtete Dauer in Vielfachen von B (für die Maxima über alle Dauern)

# Teil B: Paging mit Vorhersage der nächsten Ankunft
FOLGEN = ("Zipf", "Arbeitsmengen", "Schleife mit Fremdzugriffen")
DEFAULT_FOLGE = "Zipf"
FOLGE_HILFE = {
    "Zipf": "Wenige Seiten werden oft angefragt, die meisten selten (4k Seiten).",
    "Arbeitsmengen": "Jede Phase nutzt k + 2 Seiten, die nächste Phase andere: LRU ist hier vergleichsweise gut, falsche Vorhersagen schaden der ungeschützten Regel am meisten.",
    "Schleife mit Fremdzugriffen": "Eine Schleife über k + 1 Seiten, dazwischen seltene Fremdzugriffe: LRU ist hier schlecht.",
}
K_MIN, K_MAX, DEFAULT_K = 4, 16, 10
LENGTH = 6000
ZIPF_ALPHA, PHASE_LEN, UNIVERSE_FACTOR, FOREIGN_SHARE, FOREIGN_RANGE = 0.8, 300, 50, 0.1, 1000
VORHERSAGEN = ("exakt", "5 % falsch", "25 % falsch", "50 % falsch", "alle zufällig", "gegnerisch")
DEFAULT_VORHERSAGE = "exakt"
VORHERSAGE_ANTEIL = {"exakt": 0.0, "5 % falsch": 0.05, "25 % falsch": 0.25, "50 % falsch": 0.5, "alle zufällig": 1.0}
VORHERSAGE_HILFE = {
    "exakt": "Jede Vorhersage der nächsten Ankunft stimmt.",
    "5 % falsch": "Jede Vorhersage wird mit 5 % Wahrscheinlichkeit durch eine zufällige Zeit ersetzt (im Mittel jede zwanzigste).",
    "25 % falsch": "Jede Vorhersage wird mit 25 % Wahrscheinlichkeit durch eine zufällige Zeit ersetzt (im Mittel jede vierte).",
    "50 % falsch": "Jede Vorhersage wird mit 50 % Wahrscheinlichkeit durch eine zufällige Zeit ersetzt (im Mittel jede zweite).",
    "alle zufällig": "Alle Vorhersagen sind zufällige Zeiten: die Vorhersage trägt keine Information.",
    "gegnerisch": "Eine Seite, die bald kommt, sieht fern aus, und umgekehrt: die umgekehrte Ordnung der wahren Ankunftszeiten, für die ungeschützte Regel nahezu die schlechteste.",
}
RANDOM_SPAN = 100              # zufällige Vorhersage: 1 bis RANDOM_SPAN Schritte voraus
GEGNER_CAP = 5000
VERFAHREN = ("LRU", "Vorhersage ungeschützt", "Marker mit Vorhersage", "Verfolger")
DEFAULT_VERFAHREN = "Marker mit Vorhersage"
VERFAHREN_HILFE = {
    "LRU": "Verdrängt die am längsten ungenutzte Seite; braucht keine Vorhersage und hat die Garantie k.",
    "Vorhersage ungeschützt": "Verdrängt die Seite, die laut Vorhersage am spätesten wieder kommt. Mit richtigen Vorhersagen ist das optimal (Belady), mit falschen theoretisch ohne Schranke schlecht.",
    "Marker mit Vorhersage": "Nur unmarkierte Seiten (seit Phasenbeginn nicht angefragt) dürfen weichen, unter ihnen nach der Vorhersage. Jedes Marker-Verfahren ist k-kompetitiv, auch mit falscher Vorhersage.",
    "Verfolger": "Folgt träge dem besseren von „Vorhersage ungeschützt“ und LRU und wechselt erst bei mehr als k Fehlern Vorsprung (eigene einfache Fassung).",
}
SEED_MAX, DEFAULT_SEED = 999999, 7

# feste Experimente (nie ein einzelner Seed als Befund)
KOMPROMISS_LAMS = LAM_OPTIONS
FEHLER_LAMS = (0.1, 0.25, 0.5, 0.75, 1.0)
FEHLER_PS = (0.0, 0.1, 0.25, 0.5)
EXP_K, EXP_SEEDS = 10, 4
GEGNER_VORHERSAGE = "gegnerisch"

COLORS = {"LRU": "#7c7c7c", "Vorhersage ungeschützt": "#c0392b", "Marker mit Vorhersage": "#2F6B65", "Verfolger": "#4c78a8"}
COLOR_OPT = "#d97706"
COLOR_BREAKEVEN = "#7c7c7c"
COLOR_CONS = "#2F6B65"
COLOR_ROB = "#c0392b"

PRESETS = {
    "Klassisch (λ = 0,25, richtige Vorhersage)": {"b": 20, "lam": 0.25, "p": 0.0, "folge": "Zipf", "k": 10, "vorhersage": "exakt", "verfahren": "Marker mit Vorhersage", "seed": DEFAULT_SEED},
    "Falsche Vorhersage (50 %)": {"b": 20, "lam": 0.25, "p": 0.5, "folge": "Zipf", "k": 10, "vorhersage": "exakt", "verfahren": "Marker mit Vorhersage", "seed": DEFAULT_SEED},
    "Ohne Vorhersage (λ = 1)": {"b": 20, "lam": 1.0, "p": 0.0, "folge": "Zipf", "k": 10, "vorhersage": "exakt", "verfahren": "Marker mit Vorhersage", "seed": DEFAULT_SEED},
    "Arbeitsmengen, 25 % falsch": {"b": 20, "lam": 0.25, "p": 0.0, "folge": "Arbeitsmengen", "k": 10, "vorhersage": "25 % falsch", "verfahren": "Vorhersage ungeschützt", "seed": DEFAULT_SEED},
    "Gegnerische Vorhersage": {"b": 20, "lam": 0.25, "p": 0.0, "folge": "Arbeitsmengen", "k": 10, "vorhersage": "gegnerisch", "verfahren": "Vorhersage ungeschützt", "seed": DEFAULT_SEED},
    "Zipf, exakt (Verfolger)": {"b": 20, "lam": 0.25, "p": 0.0, "folge": "Zipf", "k": 10, "vorhersage": "exakt", "verfahren": "Verfolger", "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Klassisch (λ = 0,25, richtige Vorhersage)": "Mieten oder Kaufen mit richtiger Vorhersage und viel Vertrauen: die Kosten liegen nahe am Optimum, dafür ist die Robustheit schwach.",
    "Falsche Vorhersage (50 %)": "Mit 50 % Wahrscheinlichkeit ist die Vorhersage vertauscht: das Vertrauen kostet mehr als die Break-even-Regel ohne Vorhersage.",
    "Ohne Vorhersage (λ = 1)": "Die Break-even-Regel: kauft am Tag B, ignoriert die Vorhersage und gilt in jedem Fall.",
    "Arbeitsmengen, 25 % falsch": "Auf Arbeitsmengen kippt die ungeschützte Vorhersage schon bei einem Viertel falscher Vorhersagen weit über LRU.",
    "Gegnerische Vorhersage": "Die umgekehrte Ordnung der Ankunftszeiten, für die ungeschützte Regel nahezu die schlechteste Vorhersage: sie wird mehrfach so teuer wie LRU, der Marker bleibt beschränkt.",
    "Zipf, exakt (Verfolger)": "Der Verfolger folgt bei richtiger Vorhersage der Vorhersage und ist optimal.",
}
