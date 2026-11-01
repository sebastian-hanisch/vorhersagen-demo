"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import vrs_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_kompromiss(rows):
    """Konsistenz und Robustheit über λ (logarithmische Achse) mit den Schranken."""
    xs = [r["lam"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["Konsistenz"] for r in rows], mode="lines+markers", name="Konsistenz (Vorhersage richtig)", line=dict(color=C.COLOR_CONS, width=3),
                             hovertemplate="λ = %{x}: %{y:.2f}<extra>Konsistenz</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["Robustheit"] for r in rows], mode="lines+markers", name="Robustheit (schlechtester Fall)", line=dict(color=C.COLOR_ROB, width=3),
                             hovertemplate="λ = %{x}: %{y:.2f}<extra>Robustheit</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["Schranke Konsistenz"] for r in rows], mode="lines", name="Schranke 1 + λ", line=dict(color=C.COLOR_CONS, width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=xs, y=[r["Schranke Robustheit"] for r in rows], mode="lines", name="Schranke 1 + 1/λ", line=dict(color=C.COLOR_ROB, width=1, dash="dot")))
    top = max(r["Schranke Robustheit"] for r in rows)
    fig.update_yaxes(type="log", range=[math.log10(0.95), math.log10(top) + 0.05], title_text="Quotient zum Optimum (logarithmisch)")
    fig.update_xaxes(title_text="Vertrauen λ (klein = traue der Vorhersage)")
    return _base(fig)


def build_fehler(rows, lams):
    """Erwarteter Quotient über dem Vertrauen λ, eine Linie je Fehlerquote; gestrichelt die Break-even-Regel."""
    fig = go.Figure()
    palette = ("#2F6B65", "#4c78a8", "#d97706", "#c0392b")
    for i, r in enumerate(rows):
        fig.add_trace(go.Scatter(x=[str(l) for l in lams], y=[r["Quotienten"][l] for l in lams], mode="lines+markers", name=f"{r['p'] * 100:.0f} % falsch", line=dict(color=palette[i % 4], width=3),
                                 hovertemplate="λ = %{x}: %{y:.2f}<extra>" + f"{r['p'] * 100:.0f} % falsch" + "</extra>"))
    fig.add_hline(y=rows[0]["Break-even"], line=dict(color=C.COLOR_BREAKEVEN, dash="dash"), annotation_text="Break-even (ohne Vorhersage)", annotation_position="top left")
    fig.update_xaxes(title_text="Vertrauen λ", type="category")
    fig.update_yaxes(title_text="Erwartete Kosten / erwartetes Optimum", rangemode="tozero")
    return _base(fig)


def build_a_curve(b: int, s):
    """Kosten über der Dauer: Regel mit Vorhersage „lang“, „kurz“ und das Optimum; die Kaufstellen sind markiert."""
    import vrs_algorithm as A

    xs = list(range(1, 4 * b + 1))
    early, late = A.buy_day(True, b, s.lam), A.buy_day(False, b, s.lam)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[A.opt(x, b) for x in xs], mode="lines", name="Optimum", line=dict(color=C.COLOR_OPT, width=3, dash="dash")))
    fig.add_trace(go.Scatter(x=xs, y=[A.cost(early, x, b) for x in xs], mode="lines", name=f"Vorhersage „lang“: kaufe am Tag {early}", line=dict(color=C.COLOR_CONS, width=3, shape="hv")))
    fig.add_trace(go.Scatter(x=xs, y=[A.cost(late, x, b) for x in xs], mode="lines", name=f"Vorhersage „kurz“: kaufe am Tag {late}", line=dict(color=C.COLOR_ROB, width=3, shape="hv")))
    fig.update_xaxes(title_text="Tatsächliche Nutzungsdauer (Tage)")
    fig.update_yaxes(title_text="Kosten (Tagesmieten)", rangemode="tozero")
    return _base(fig)


def build_cumulative(b, highlighted: str):
    """Kumulierte Fehler der vier Verfahren und von Belady (b ist eine AnalysisB)."""
    fig = go.Figure()
    xs = list(range(1, len(b.cum["LRU"]) + 1))
    for n in C.VERFAHREN:
        fig.add_trace(go.Scatter(x=xs, y=b.cum[n], mode="lines", name=n, line=dict(color=C.COLORS[n], width=4 if n == highlighted else 2),
                                 hovertemplate="nach Anfrage %{x}: %{y}<extra>" + n + "</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=b.cum["Belady"], mode="lines", name="Belady (Optimum)", line=dict(color=C.COLOR_OPT, width=2, dash="dash"),
                             hovertemplate="nach Anfrage %{x}: %{y}<extra>Belady</extra>"))
    fig.update_xaxes(title_text="Anfrage")
    fig.update_yaxes(title_text="Fehler (kumuliert)", rangemode="tozero")
    return _base(fig)


def build_ratios(b):
    """Fehler geteilt durch Belady je Verfahren, hervorgehoben das gewählte."""
    names = list(C.VERFAHREN)
    vals = [min(b.ratios[n], 50.0) for n in names]
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=[C.COLORS[n] for n in names], text=[f"{v:.2f}" for v in vals], textposition="outside", hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    fig.add_hline(y=1.0, line=dict(color=C.COLOR_OPT, dash="dash"), annotation_text="Belady = 1", annotation_position="top left")
    fig.update_yaxes(title_text="Fehler / Belady", range=[0, max(vals) * 1.25])
    return _base(fig, height=300)


def build_quali(rows):
    """Fehler / Belady über der Vorhersagequalität, ein Feld je Folge, eine Linie je Verfahren (logarithmische Achse)."""
    folgen = list(dict.fromkeys(r["Folge"] for r in rows))
    fig = make_subplots(rows=1, cols=len(folgen), subplot_titles=folgen, shared_yaxes=True)
    allv = []
    for i, folge in enumerate(folgen, start=1):
        sub = [r for r in rows if r["Folge"] == folge]
        for n in C.VERFAHREN:
            ys = [r[n] for r in sub]
            allv += ys
            fig.add_trace(go.Scatter(x=[r["Vorhersage"] for r in sub], y=ys, mode="lines+markers", name=n, legendgroup=n, showlegend=(i == 1), line=dict(color=C.COLORS[n], width=3),
                                     hovertemplate="%{x}: %{y:.2f}<extra>" + n + "</extra>"), row=1, col=i)
    fig.update_yaxes(type="log", range=[math.log10(0.95), math.log10(max(allv)) + 0.05], title_text="Fehler / Belady (logarithmisch)", row=1, col=1)
    fig.update_xaxes(tickangle=-45)
    return _base(fig, height=420)


def build_gegner(rows):
    sub = [r for r in rows if r["Vorhersage"] == C.GEGNER_VORHERSAGE]
    fig = go.Figure()
    for n in C.VERFAHREN:
        fig.add_trace(go.Bar(x=[r["Folge"] for r in sub], y=[r[n] for r in sub], name=n, marker_color=C.COLORS[n], hovertemplate="%{x}: %{y:.2f}<extra>" + n + "</extra>"))
    fig.update_layout(barmode="group")
    fig.add_hline(y=1.0, line=dict(color=C.COLOR_OPT, dash="dash"), annotation_text="Belady = 1", annotation_position="top left")
    fig.update_yaxes(title_text="Fehler / Belady", rangemode="tozero")
    return _base(fig, height=320)


def build_konsistenz(rows):
    sub = [r for r in rows if r["Vorhersage"] == "exakt"]
    fig = go.Figure()
    for n in C.VERFAHREN:
        fig.add_trace(go.Bar(x=[r["Folge"] for r in sub], y=[r[n] for r in sub], name=n, marker_color=C.COLORS[n], text=[f"{r[n]:.2f}" for r in sub], textposition="outside",
                             hovertemplate="%{x}: %{y:.2f}<extra>" + n + "</extra>"))
    fig.update_layout(barmode="group")
    fig.add_hline(y=1.0, line=dict(color=C.COLOR_OPT, dash="dash"), annotation_text="Belady = 1", annotation_position="top left")
    fig.update_yaxes(title_text="Fehler / Belady", range=[0, max(r[n] for r in sub for n in C.VERFAHREN) * 1.2])
    return _base(fig, height=320)
