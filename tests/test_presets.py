"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink; feste Experimente."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import vrs_constants as C
import vrs_evaluation as ev
import vrs_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_ranges():
    for name, preset in C.PRESETS.items():
        assert preset["b"] in C.B_OPTIONS and preset["lam"] in C.LAM_OPTIONS and preset["p"] in C.P_OPTIONS, name
        assert preset["folge"] in C.FOLGEN and C.K_MIN <= preset["k"] <= C.K_MAX and preset["vorhersage"] in C.VORHERSAGEN, name
        assert preset["verfahren"] in C.VERFAHREN and 0 <= preset["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_choice_has_a_help_text_and_defaults_are_valid():
    assert set(C.FOLGE_HILFE) == set(C.FOLGEN) and set(C.VORHERSAGE_HILFE) == set(C.VORHERSAGEN) and set(C.VERFAHREN_HILFE) == set(C.VERFAHREN) and set(C.COLORS) == set(C.VERFAHREN)
    assert set(C.VORHERSAGE_ANTEIL) | {C.GEGNER_VORHERSAGE} == set(C.VORHERSAGEN)
    assert C.DEFAULT_B in C.B_OPTIONS and C.DEFAULT_LAM in C.LAM_OPTIONS and C.DEFAULT_P in C.P_OPTIONS and C.DEFAULT_FOLGE in C.FOLGEN
    assert C.DEFAULT_VORHERSAGE in C.VORHERSAGEN and C.DEFAULT_VERFAHREN in C.VERFAHREN and C.K_MIN <= C.DEFAULT_K <= C.K_MAX
    assert list(C.LAM_OPTIONS) == sorted(C.LAM_OPTIONS) and C.LAM_OPTIONS[0] == 0.1 and C.LAM_OPTIONS[-1] == 1.0 and len(C.LAM_OPTIONS) == 19
    assert list(C.P_OPTIONS) == sorted(C.P_OPTIONS) and C.P_OPTIONS[0] == 0.0 and C.P_OPTIONS[-1] == 0.5


def test_experiment_grids_are_inside_the_controls():
    assert set(C.FEHLER_LAMS) <= set(C.LAM_OPTIONS) and set(C.FEHLER_PS) <= set(C.P_OPTIONS) and set(C.KOMPROMISS_LAMS) <= set(C.LAM_OPTIONS)
    assert C.K_MIN <= C.EXP_K <= C.K_MAX and C.DEFAULT_B in C.B_OPTIONS


def test_experiment_rows_have_the_documented_shape():
    rows = ev.kompromiss_rows(lams=(0.5, 1.0))
    assert [r["lam"] for r in rows] == [0.5, 1.0] and {"Konsistenz", "Robustheit", "Schranke Konsistenz", "Schranke Robustheit"} <= set(rows[0])
    rows = ev.fehler_rows(lams=(0.5, 1.0), ps=(0.0, 0.5))
    assert [r["p"] for r in rows] == [0.0, 0.5] and set(rows[0]["Quotienten"]) == {0.5, 1.0}
    rows = ev.quali_rows(seeds=1, folgen=("Zipf",), vorhersagen=("exakt", "gegnerisch"), length=300)
    assert [(r["Folge"], r["Vorhersage"]) for r in rows] == [("Zipf", "exakt"), ("Zipf", "gegnerisch")] and set(C.VERFAHREN) <= set(rows[0])


def _app_with(params: dict) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    for key, value in params.items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_uebernimmt_gueltige_werte():
    at = _app_with({"b": "50", "lam": "0.5", "p": "0.25", "folge": "Arbeitsmengen", "k": "6", "vorhersage": "gegnerisch", "verfahren": "Verfolger", "seed": "5"})
    state = {k: at.session_state[k] for k in P.SETTING_SPECS}
    assert state == {"b_select": 50, "lam_select": 0.5, "p_select": 0.25, "folge_select": "Arbeitsmengen", "k_slider": 6, "vorhersage_select": "gegnerisch", "verfahren_select": "Verfolger", "seed_input": 5}


def test_permalink_begrenzt_und_ignoriert_ungueltiges():
    at = _app_with({"k": "99", "b": "33", "lam": "0.123", "p": "0.9", "folge": "x", "vorhersage": "y", "verfahren": "z", "seed": "99999999"})
    assert at.session_state["k_slider"] == C.K_MAX
    assert at.session_state["b_select"] == C.DEFAULT_B and at.session_state["lam_select"] == C.DEFAULT_LAM and at.session_state["p_select"] == C.DEFAULT_P
    assert at.session_state["folge_select"] == C.DEFAULT_FOLGE and at.session_state["vorhersage_select"] == C.DEFAULT_VORHERSAGE and at.session_state["verfahren_select"] == C.DEFAULT_VERFAHREN
    assert at.session_state["seed_input"] == C.SEED_MAX
