"""Interpretation of CO-Hb and Met-Hb for the BGA Streamlit app.

Thresholds are decision-support orientation only. Clinical symptoms, exposure,
comorbidity, pregnancy and toxicology consultation take precedence.
"""
from __future__ import annotations
from typing import Any, Optional


def fractional_oxyhemoglobin_percent(
    functional_sao2_percent: float,
    cohb_percent: float = 0.0,
    methb_percent: float = 0.0,
) -> float:
    """Estimate fractional O2Hb from functional SaO2 and dyshemoglobins."""
    available = max(0.0, 1.0 - (cohb_percent + methb_percent) / 100.0)
    return functional_sao2_percent * available


def arterial_oxygen_content(
    hb_g_dl: float,
    functional_sao2_percent: float,
    po2_mm_hg: float,
    cohb_percent: float = 0.0,
    methb_percent: float = 0.0,
) -> float:
    oxyhb = fractional_oxyhemoglobin_percent(
        functional_sao2_percent, cohb_percent, methb_percent
    )
    return 1.34 * hb_g_dl * (oxyhb / 100.0) + 0.003 * po2_mm_hg


def assess_carboxyhemoglobin(
    cohb_percent: Optional[float],
    smoking_status: str = "unbekannt",
) -> Optional[dict[str, str]]:
    if cohb_percent is None:
        return None

    status = smoking_status.strip().lower()
    if cohb_percent >= 25:
        return {
            "rank": "severe",
            "level": "deutlich erhöhtes CO-Hb",
            "summary": f"CO-Hb {cohb_percent:.1f}%: schwere CO-Exposition/Intoxikation möglich.",
            "recommendation": (
                "Sofort 100% Sauerstoff geben, Exposition beenden sowie neurologisch und kardial beurteilen. "
                "Hyperbare Oxygenierung bei CO-Hb >25–30% oder bei schwerer Klinik, Bewusstlosigkeit, "
                "neurologischen Auffälligkeiten, kardialer Beteiligung, schwerer Azidose oder Schwangerschaft prüfen."
            ),
        }

    threshold = 2.0 if status == "nichtraucher" else 9.0
    if cohb_percent > threshold:
        return {
            "rank": "moderate",
            "level": "pathologisch erhöhtes CO-Hb",
            "summary": (
                f"CO-Hb {cohb_percent:.1f}%: "
                + (
                    "bei Nichtraucherstatus mit CO-Exposition vereinbar."
                    if status == "nichtraucher"
                    else "auch bei Raucherstatus deutlich verdächtig auf CO-Exposition."
                )
            ),
            "recommendation": (
                "Bei passender Exposition oder Symptomatik 100% Sauerstoff verabreichen, "
                "Exposition beenden und CO-Hb sowie Neurostatus im Verlauf kontrollieren."
            ),
        }

    if cohb_percent > 2.0:
        return {
            "rank": "mild",
            "level": "erhöhtes CO-Hb",
            "summary": (
                f"CO-Hb {cohb_percent:.1f}%: "
                + (
                    "bei Raucherstatus noch rauchassoziiert möglich."
                    if status == "raucher"
                    else "Raucherstatus und mögliche CO-Exposition klären."
                )
            ),
            "recommendation": (
                "Klinik und Expositionsanamnese entscheiden. Bei Nichtraucherstatus, Symptomen "
                "oder plausibler Exposition niedrige Schwelle zur 100%-O₂-Gabe."
            ),
        }

    return {
        "rank": "normal",
        "level": "CO-Hb nicht erhöht",
        "summary": f"CO-Hb {cohb_percent:.1f}%: kein relevanter Anstieg.",
        "recommendation": "Keine CO-spezifische Therapie allein anhand dieses Wertes.",
    }


def assess_methemoglobin(methb_percent: Optional[float]) -> Optional[dict[str, str]]:
    if methb_percent is None:
        return None
    if methb_percent >= 30:
        return {
            "rank": "severe",
            "level": "schwere Methämoglobinämie",
            "summary": f"Met-Hb {methb_percent:.1f}%: schwere Methämoglobinämie.",
            "recommendation": (
                "Oxidans absetzen, hochdosierten Sauerstoff geben und sofort toxikologisch rücksprechen. "
                "Antidottherapie mit Methylenblau ist in der Regel angezeigt; G6PD-Mangel, "
                "serotonerge Medikation und alternative Therapien beachten."
            ),
        }
    if methb_percent >= 20:
        return {
            "rank": "moderate",
            "level": "klinisch relevante Methämoglobinämie",
            "summary": f"Met-Hb {methb_percent:.1f}%: klinisch relevante Methämoglobinämie.",
            "recommendation": (
                "Auslöser stoppen, Sauerstoff geben und dringlich toxikologisch rücksprechen. "
                "Bei Symptomen oder eingeschränkter O₂-Transportreserve Methylenblau erwägen."
            ),
        }
    if methb_percent >= 10:
        return {
            "rank": "mild",
            "level": "deutliche Methämoglobinämie",
            "summary": f"Met-Hb {methb_percent:.1f}%: Zyanose und funktionelle Hypoxie möglich.",
            "recommendation": (
                "Auslöser suchen und stoppen, Sauerstoffgabe sowie engmaschige klinische Kontrolle. "
                "Therapieentscheidung nach Symptomatik und Komorbidität."
            ),
        }
    if methb_percent > 1.5:
        return {
            "rank": "mild",
            "level": "leicht erhöhtes Met-Hb",
            "summary": f"Met-Hb {methb_percent:.1f}%: leicht erhöht.",
            "recommendation": (
                "Oxidierende Medikamente/Expositionen prüfen. Bei Symptomen, Anämie oder "
                "kardiorespiratorischer Erkrankung engmaschiger beurteilen."
            ),
        }
    return {
        "rank": "normal",
        "level": "Met-Hb nicht erhöht",
        "summary": f"Met-Hb {methb_percent:.1f}%: im Referenzbereich.",
        "recommendation": "Keine Met-Hb-spezifische Therapie allein anhand dieses Wertes.",
    }


def assess_dyshemoglobins(
    cohb_percent: Optional[float],
    methb_percent: Optional[float],
    smoking_status: str,
) -> dict[str, Any]:
    notes: list[str] = []
    if (cohb_percent or 0) > 2 or (methb_percent or 0) > 1.5:
        notes.append(
            "Bei Dys-Hämoglobinämie können SpO₂, berechnete SaO₂ und ein normaler pO₂ "
            "den tatsächlichen Sauerstofftransport überschätzen."
        )
    return {
        "cohb": assess_carboxyhemoglobin(cohb_percent, smoking_status),
        "methb": assess_methemoglobin(methb_percent),
        "notes": notes,
    }
