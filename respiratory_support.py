"""Cautious respiratory-support decision aid for the BGA app."""
from __future__ import annotations
from typing import Any, Optional

from bga_logic import BGAInput, pf_ratio


def respiratory_support_recommendation(
    data: BGAInput,
    respiratory_rate: int = 16,
    hypercapnia_risk: bool = False,
    clinical_context: str = "nicht spezifiziert",
    red_flags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Generate cautious, rule-based respiratory support recommendations.

    The result is decision support only. Oxygen, NIV and invasive ventilation
    decisions require clinical assessment, including work of breathing,
    consciousness, airway protection, haemodynamics and the underlying cause.
    """
    red_flags = red_flags or []
    arterial = data.sample_type.lower().startswith("arter")
    target_low, target_high = (88, 92) if hypercapnia_risk else (94, 98)
    target_text = f"{target_low}–{target_high} %"

    po2 = data.po2 if arterial else None
    sao2 = data.sao2_percent if arterial else None
    fio2 = data.fio2_percent if arterial else None
    pf = None
    if po2 is not None and fio2 is not None:
        pf = pf_ratio(po2, fio2)

    if not arterial:
        oxygen = (
            "Keine verlässliche Sauerstoffempfehlung aus dem pO₂ einer nichtarteriellen Probe ableitbar. "
            "SpO₂, klinischen Zustand und bei relevanter respiratorischer Insuffizienz eine aBGA heranziehen."
        )
    else:
        hypoxemia = (po2 is not None and po2 < 60) or (sao2 is not None and sao2 < target_low)
        severe_hypoxemia = (po2 is not None and po2 < 40) or (pf is not None and pf <= 100)
        hyperoxia = (
            sao2 is not None
            and sao2 > target_high
            and fio2 is not None
            and fio2 > 21.5
        )

        if severe_hypoxemia:
            oxygen = (
                f"Schwere Oxygenierungsstörung: Sauerstoffgabe beziehungsweise Eskalation der respiratorischen Unterstützung "
                f"ist dringlich; O₂ kontrolliert auf einen Zielbereich von {target_text} titrieren. "
                "Engmaschige klinische und arterielle BGA-Kontrolle erforderlich."
            )
        elif hypoxemia:
            if fio2 is not None and fio2 > 21.5:
                oxygen = (
                    f"Trotz laufender Sauerstoffgabe besteht eine relevante Hypoxämie. O₂-Zufuhr und Applikationssystem "
                    f"überprüfen beziehungsweise eskalieren und auf {target_text} titrieren; Ursache der Gasaustauschstörung behandeln."
                )
            else:
                oxygen = (
                    f"Kontrollierte Sauerstoffgabe ist anhand der arteriellen Werte angezeigt; auf einen Zielbereich von "
                    f"{target_text} titrieren."
                )
        elif hyperoxia:
            oxygen = (
                f"Sättigung oberhalb des gewählten Zielbereichs unter zusätzlichem Sauerstoff. FiO₂ soweit klinisch vertretbar "
                f"reduzieren und auf {target_text} titrieren."
            )
        else:
            oxygen = (
                f"Aus der aktuellen aBGA ergibt sich keine zwingende zusätzliche Sauerstoffgabe. Sättigung im Zielbereich "
                f"{target_text} halten und Verlauf kontrollieren."
            )

    hypercapnic_acidosis = data.ph <= 7.35 and data.pco2 > 45
    context_lower = clinical_context.lower()
    copd_like = any(term in context_lower for term in ("copd", "ohs", "neuromusk", "thoraxwand"))
    cardiogenic_edema = "lungenödem" in context_lower or "kardiogen" in context_lower
    relevant_hypoxemia = arterial and (
        (po2 is not None and po2 < 60)
        or (pf is not None and pf <= 300)
    )

    if hypercapnic_acidosis:
        if copd_like:
            niv = (
                f"NIV ist bei akuter hyperkapnischer respiratorischer Azidose im angegebenen Kontext dringend zu beginnen "
                f"beziehungsweise zu prüfen (pH {data.ph:.2f}, pCO₂ {data.pco2:.0f} mmHg"
                + (f", AF {respiratory_rate}/min" if respiratory_rate else "")
                + "), sofern keine Kontraindikation oder unmittelbare Intubationsindikation besteht."
            )
        else:
            niv = (
                f"Akute hyperkapnische respiratorische Azidose (pH {data.ph:.2f}, pCO₂ {data.pco2:.0f} mmHg): "
                "NIV-Indikation unverzüglich klinisch prüfen. Der Nutzen ist besonders für AECOPD/OHS und andere "
                "ventilatorische Pumpenstörungen belegt."
            )
        if respiratory_rate > 24:
            niv += " Die Tachypnoe verstärkt die Dringlichkeit der ventilatorischen Unterstützung."
    elif cardiogenic_edema and (relevant_hypoxemia or respiratory_rate >= 25):
        niv = (
            "Bei angegebenem kardiogenem Lungenödem und respiratorischer Belastung CPAP/NIV zusätzlich zur kausalen Therapie "
            "frühzeitig erwägen; Blutdruck und Kontraindikationen beachten."
        )
    elif relevant_hypoxemia and pf is not None and pf <= 200:
        niv = (
            "Ausgeprägte hypoxämische respiratorische Insuffizienz: HFNO, CPAP/NIV oder invasive Beatmung abhängig von Ursache, "
            "Atemarbeit und Verlauf in einem eng überwachten Setting prüfen. NIV darf eine notwendige Intubation nicht verzögern."
        )
    else:
        niv = (
            "Aus der BGA allein ergibt sich keine klare NIV-Indikation. Klinische Atemarbeit, Atemfrequenz, Grunderkrankung "
            "und Verlauf bleiben entscheidend."
        )

    if red_flags:
        invasive = (
            "Dringliche Atemwegssicherung beziehungsweise invasive Beatmung prüfen, da folgende klinische Red Flags angegeben sind: "
            + "; ".join(red_flags)
            + ". Eine NIV darf die Intubation bei unmittelbarer Gefährdung nicht verzögern."
        )
    elif hypercapnic_acidosis and data.ph < 7.25:
        invasive = (
            f"Schwere hyperkapnische Azidose (pH {data.ph:.2f}) mit erhöhtem NIV-Versagensrisiko: Behandlung in einem "
            "Intensiv-/Überwachungssetting mit unmittelbarer Intubationsbereitschaft. Bei fehlender rascher klinischer und "
            "BGA-Besserung invasive Beatmung einleiten."
        )
    elif arterial and pf is not None and pf <= 100:
        invasive = (
            f"Sehr schwere Oxygenierungsstörung (P/F {pf:.0f} mmHg): sofortige intensivmedizinische Eskalation und "
            "Intubationsbereitschaft; invasive Beatmung bei fehlender rascher Stabilisierung oder zunehmender Atemarbeit."
        )
    else:
        invasive = (
            "Keine automatische Intubationsindikation allein aus der BGA. Invasive Beatmung ist bei NIV-Versagen, fehlender "
            "Atemwegssicherung, Bewusstseinsstörung, Kreislaufinstabilität, Erschöpfung oder therapierefraktärer Hypoxämie zu prüfen."
        )

    reassessment = (
        "Nach Beginn oder Änderung von O₂/NIV frühzeitige klinische Reevaluation und Verlaufskontrolle der aBGA; "
        "bei NIV fehlende Besserung von pH, pCO₂, Atemfrequenz oder Vigilanz als Warnzeichen werten."
    )
    disclaimer = (
        "Diese Empfehlung ist eine BGA-basierte Entscheidungshilfe und ersetzt keine unmittelbare ärztliche Beurteilung von "
        "Atemarbeit, Vigilanz, Schutzreflexen, Hämodynamik, Sekretmanagement und Grunderkrankung. Bei CO-/MetHb-Erhöhung sind "
        "SpO₂/SaO₂ und die Standard-O₂-Logik nur eingeschränkt verwertbar."
    )

    return {
        "oxygen": oxygen,
        "niv": niv,
        "invasive": invasive,
        "reassessment": reassessment,
        "disclaimer": disclaimer,
        "target_saturation": target_text,
        "pf_ratio": pf,
    }
