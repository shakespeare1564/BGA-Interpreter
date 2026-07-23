"""Conservative interpretation of CO-Hb and Met-Hb for the BGA app.

The reference ranges follow Venturini et al., Notaufnahme up2date 2026:
CO-Hb 0.5–1.5 %, Met-Hb 0–1.5 %. The module intentionally avoids deriving
antidote or hyperbaric-treatment indications from a single laboratory value.
"""
from __future__ import annotations

from typing import Any


COHB_UPPER_REFERENCE = 1.5
METHB_UPPER_REFERENCE = 1.5


def fractional_oxyhemoglobin_percent(
    functional_sao2_percent: float,
    co_hb_percent: float = 0.0,
    met_hb_percent: float = 0.0,
) -> float:
    """Estimate fractional O2Hb if the entered SaO2 is a functional saturation.

    A directly measured O2Hb fraction from co-oximetry is preferable whenever
    dyshemoglobins are elevated.
    """
    available_fraction = max(0.0, 1.0 - (co_hb_percent + met_hb_percent) / 100.0)
    return functional_sao2_percent * available_fraction


def dyshemoglobin_adjusted_cao2(
    hb_g_dl: float,
    functional_sao2_percent: float,
    po2_mm_hg: float,
    co_hb_percent: float = 0.0,
    met_hb_percent: float = 0.0,
) -> float:
    oxyhb_percent = fractional_oxyhemoglobin_percent(
        functional_sao2_percent,
        co_hb_percent,
        met_hb_percent,
    )
    return 1.34 * hb_g_dl * (oxyhb_percent / 100.0) + 0.003 * po2_mm_hg


def assess_dyshemoglobins(
    co_hb_percent: float,
    met_hb_percent: float,
    smoking_status: str = "unbekannt",
) -> dict[str, Any]:
    """Interpret CO-Hb and Met-Hb without replacing clinical toxicology assessment."""
    if not 0.0 <= co_hb_percent <= 100.0:
        raise ValueError("CO-Hb muss zwischen 0 und 100 % liegen.")
    if not 0.0 <= met_hb_percent <= 100.0:
        raise ValueError("Met-Hb muss zwischen 0 und 100 % liegen.")

    status = smoking_status.strip().lower()
    smoker = status.startswith("rauch")

    co_elevated = co_hb_percent > COHB_UPPER_REFERENCE
    met_elevated = met_hb_percent > METHB_UPPER_REFERENCE

    if not co_elevated:
        co_summary = f"CO-Hb {co_hb_percent:.1f} %: im Referenzbereich."
        co_rank = "normal"
    elif smoker:
        co_summary = (
            f"CO-Hb {co_hb_percent:.1f} %: erhöht. Eine raucherassoziierte Erhöhung ist möglich; "
            "bei passender Exposition oder Symptomatik eine zusätzliche CO-Belastung dennoch ausschließen."
        )
        co_rank = "warning"
    else:
        co_summary = (
            f"CO-Hb {co_hb_percent:.1f} %: erhöht. Raucherstatus, Expositionsanamnese und Klinik prüfen; "
            "eine akute CO-Belastung ist möglich."
        )
        co_rank = "warning"

    if not met_elevated:
        met_summary = f"Met-Hb {met_hb_percent:.1f} %: im Referenzbereich."
        met_rank = "normal"
    else:
        met_summary = (
            f"Met-Hb {met_hb_percent:.1f} %: erhöht. Oxidierende Medikamente oder Substanzen sowie "
            "klinische Zeichen einer Methämoglobinämie prüfen."
        )
        met_rank = "warning"

    saturation_warning = co_elevated or met_elevated
    if saturation_warning:
        saturation_note = (
            "Bei erhöhtem CO-Hb oder Met-Hb können Pulsoxymetrie und eine aus pO₂ abgeleitete SaO₂ den "
            "effektiven Sauerstofftransport überschätzen. Gemessene Hämoglobinfraktionen, Hb, Klinik und Verlauf "
            "gemeinsam bewerten."
        )
        cao2_note = (
            "Die Standard-CaO₂-Berechnung mit SaO₂ kann bei Dys-Hämoglobinämie zu hoch ausfallen. "
            "Eine direkt gemessene O₂Hb-Fraktion ist für CaO₂ vorzuziehen; die App zeigt ergänzend nur eine Schätzung."
        )
    else:
        saturation_note = "Kein Hinweis auf eine relevante Dys-Hämoglobinämie anhand der eingegebenen Werte."
        cao2_note = "Die Standard-CaO₂-Berechnung ist durch CO-Hb/Met-Hb nicht relevant eingeschränkt."

    oxygen_note_parts: list[str] = []
    if co_elevated:
        oxygen_note_parts.append(
            "Bei klinischem Verdacht auf akute CO-Exposition oder typischer Symptomatik hochdosierten Sauerstoff "
            "geben und eine dringliche toxikologische beziehungsweise hyperbarmedizinische Beurteilung veranlassen."
        )
    if met_elevated:
        oxygen_note_parts.append(
            "Bei klinisch relevanter Methämoglobinämie Sauerstoff geben und dringlich toxikologisch beurteilen; "
            "eine Antidotentscheidung darf nicht allein aus diesem App-Ergebnis abgeleitet werden."
        )

    return {
        "co_hb_percent": co_hb_percent,
        "met_hb_percent": met_hb_percent,
        "co_rank": co_rank,
        "met_rank": met_rank,
        "co_summary": co_summary,
        "met_summary": met_summary,
        "saturation_warning": saturation_warning,
        "saturation_note": saturation_note,
        "cao2_note": cao2_note,
        "oxygen_note": " ".join(oxygen_note_parts),
        "summary": " ".join([co_summary, met_summary, saturation_note]),
    }
