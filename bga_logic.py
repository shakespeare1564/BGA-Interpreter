"""Deterministic calculations for systematic blood gas analysis.

Core acid-base workflow follows Schiffler et al., Notaufnahme up2date 2025;
7:229-237, DOI 10.1055/a-2517-5186.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Optional

PH_LOW, PH_HIGH = 7.35, 7.45
PCO2_LOW, PCO2_HIGH = 36.0, 44.0
HCO3_LOW, HCO3_HIGH = 22.0, 26.0
AG_REF, HCO3_REF, PCO2_REF = 12.0, 24.0, 40.0


@dataclass(frozen=True)
class BGAInput:
    sample_type: str
    ph: float
    pco2: float
    hco3: float
    sodium: float
    chloride: float
    albumin: Optional[float] = None
    po2: Optional[float] = None
    potassium: Optional[float] = None
    lactate: Optional[float] = None
    hb: Optional[float] = None
    sao2_percent: Optional[float] = None
    fio2_percent: Optional[float] = None
    glucose: Optional[float] = None
    urea: Optional[float] = None
    measured_osmolality: Optional[float] = None
    urine_na: Optional[float] = None
    urine_k: Optional[float] = None
    urine_cl: Optional[float] = None
    urine_ph: Optional[float] = None
    urine_ketones: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_ph(ph: float) -> str:
    if ph < PH_LOW:
        return "Azidämie"
    if ph > PH_HIGH:
        return "Alkalämie"
    return "pH im Referenzbereich"


def calculate_anion_gap(na: float, cl: float, hco3: float) -> float:
    return na - (cl + hco3)


def expected_normal_ag(albumin: Optional[float]) -> Optional[float]:
    if albumin is None:
        return None
    return AG_REF - 2.5 * ((40.0 - albumin) / 10.0)


def albumin_corrected_ag(ag: float, albumin: Optional[float]) -> Optional[float]:
    if albumin is None:
        return None
    return ag + 2.5 * ((40.0 - albumin) / 10.0)


def winter_expected_pco2(hco3: float) -> tuple[float, float, float]:
    center = 1.5 * hco3 + 8.0
    return center, center - 2.0, center + 2.0


def metabolic_alkalosis_expected_pco2(hco3: float) -> float:
    return 0.7 * hco3 + 20.0


def respiratory_acidosis_expected_hco3(pco2: float) -> tuple[float, float]:
    delta = pco2 - PCO2_REF
    return HCO3_REF + 0.1 * delta, HCO3_REF + 0.4 * delta


def respiratory_alkalosis_expected_hco3(pco2: float) -> tuple[float, float]:
    delta = PCO2_REF - pco2
    return HCO3_REF - 0.2 * delta, HCO3_REF - 0.4 * delta


def determine_processes(compensation: dict[str, Any]) -> list[str]:
    """Return interpreted processes, not raw directional parameter changes.

    A low HCO3- during a respiratory alkalosis can be physiological
    compensation and must not automatically be labelled as a separate
    metabolic acidosis.
    """
    mode = compensation.get("mode") or "kein eindeutiger Primärprozess"
    processes = [mode]

    for flag in compensation.get("flags", []):
        if flag.startswith("Zusätzliche "):
            cleaned = flag.rstrip(".")
            cleaned = cleaned.replace(" wahrscheinlich", "")
            cleaned = cleaned.replace(" erwägen", "")
            processes.append(cleaned)

    return list(dict.fromkeys(processes))


def has_metabolic_acidosis(compensation: dict[str, Any]) -> bool:
    text = " ".join(
        [compensation.get("mode", ""), *compensation.get("flags", [])]
    ).lower()
    return "metabolische azidose" in text


def compensation_assessment(ph: float, pco2: float, hco3: float) -> dict[str, Any]:
    out: dict[str, Any] = {"mode": "", "details": [], "flags": []}

    if ph < PH_LOW and hco3 < HCO3_LOW and pco2 > PCO2_HIGH:
        out["mode"] = "gemischte respiratorische und metabolische Azidose"
        return out
    if ph > PH_HIGH and hco3 > HCO3_HIGH and pco2 < PCO2_LOW:
        out["mode"] = "gemischte respiratorische und metabolische Alkalose"
        return out

    if ph < PH_LOW and hco3 < HCO3_LOW:
        center, low, high = winter_expected_pco2(hco3)
        out["mode"] = "metabolische Azidose"
        out["details"].append(f"Winter-Formel: pCO₂ {center:.1f} mmHg, Bereich {low:.1f}–{high:.1f}.")
        if pco2 > high:
            out["flags"].append("Zusätzliche respiratorische Azidose wahrscheinlich.")
        elif pco2 < low:
            out["flags"].append("Zusätzliche respiratorische Alkalose wahrscheinlich.")
        else:
            out["flags"].append("Respiratorische Antwort im erwarteten Bereich.")
        return out

    if ph > PH_HIGH and hco3 > HCO3_HIGH:
        expected = metabolic_alkalosis_expected_pco2(hco3)
        out["mode"] = "metabolische Alkalose"
        out["details"].append(f"Erwartetes pCO₂: ca. {expected:.1f} mmHg.")
        if pco2 > expected + 5:
            out["flags"].append("Zusätzliche respiratorische Azidose wahrscheinlich.")
        elif pco2 < expected - 5:
            out["flags"].append("Zusätzliche respiratorische Alkalose wahrscheinlich.")
        else:
            out["flags"].append("Respiratorische Antwort näherungsweise passend.")
        return out

    if pco2 > PCO2_HIGH:
        acute, chronic = respiratory_acidosis_expected_hco3(pco2)
        out["mode"] = "respiratorische Azidose"
        out["details"].append(f"Erwartetes HCO₃⁻: akut {acute:.1f}, chronisch {chronic:.1f} mmol/l.")
        nearest = "akuten" if abs(hco3 - acute) <= abs(hco3 - chronic) else "chronischen"
        out["flags"].append(f"HCO₃⁻ liegt näher am {nearest} Kompensationsmuster.")
        if hco3 > max(acute, chronic) + 2:
            out["flags"].append("Zusätzliche metabolische Alkalose erwägen.")
        if hco3 < min(acute, chronic) - 2:
            out["flags"].append("Zusätzliche metabolische Azidose erwägen.")
        return out

    if pco2 < PCO2_LOW:
        acute, chronic = respiratory_alkalosis_expected_hco3(pco2)
        out["mode"] = "respiratorische Alkalose"
        out["details"].append(f"Erwartetes HCO₃⁻: akut {acute:.1f}, chronisch {chronic:.1f} mmol/l.")
        nearest = "akuten" if abs(hco3 - acute) <= abs(hco3 - chronic) else "chronischen"
        out["flags"].append(f"HCO₃⁻ liegt näher am {nearest} Kompensationsmuster.")
        if hco3 > max(acute, chronic) + 2:
            out["flags"].append("Zusätzliche metabolische Alkalose erwägen.")
        if hco3 < min(acute, chronic) - 2:
            out["flags"].append("Zusätzliche metabolische Azidose erwägen.")
        return out

    out["mode"] = "kein eindeutiger Primärprozess"
    out["flags"].append("Bei normalem pH sind kompensierte oder gemischte Störungen weiterhin möglich.")
    return out


def delta_ratio(corrected_ag: float, hco3: float) -> Optional[float]:
    denominator = HCO3_REF - hco3
    if denominator <= 0:
        return None
    return (corrected_ag - AG_REF) / denominator


def delta_ratio_interpretation(value: float) -> str:
    if value < 0.8:
        return "Zusätzliche NAGMA möglich."
    if value <= 1.2:
        return "Weitgehend vereinbar mit isolierter HAGMA."
    if value <= 2.0:
        return "Zusätzliche Störung möglich; Klinik und Verlauf einbeziehen."
    return "Zusätzliche metabolische Alkalose oder chronische respiratorische Azidose möglich."


def glucose_to_mmol_l(value: float, unit: str) -> float:
    """Convert glucose to mmol/l for internal calculations."""
    normalized = unit.strip().lower()
    if normalized == "mmol/l":
        return value
    if normalized == "mg/dl":
        return value / 18.0
    raise ValueError("Glukose-Einheit muss mmol/l oder mg/dl sein.")


def glucose_to_mg_dl(value_mmol_l: float) -> float:
    return value_mmol_l * 18.0


def format_urine_ketones(grade: int) -> str:
    if grade == 0:
        return "0"
    return "+" * grade


def calculated_osmolality(na: float, glucose: float, urea: float) -> float:
    return 2.0 * na + glucose + urea


def osmolal_gap(measured: float, na: float, glucose: float, urea: float) -> float:
    return measured - calculated_osmolality(na, glucose, urea)


def urine_anion_gap(urine_na: float, urine_k: float, urine_cl: float) -> float:
    return urine_na + urine_k - urine_cl


def arterial_oxygen_content(hb: float, sao2_percent: float, po2: float) -> float:
    return 1.34 * hb * (sao2_percent / 100.0) + 0.003 * po2


def pf_ratio(po2: float, fio2_percent: float) -> float:
    if fio2_percent <= 0:
        raise ValueError("FiO₂ must be > 0")
    return po2 / (fio2_percent / 100.0)


def classify_room_air_pao2(po2: float) -> dict[str, str]:
    """Orientierende Schweregradeinteilung des arteriellen PaO₂ unter Raumluft."""
    if po2 >= 80:
        return {"level": "keine manifeste Hypoxämie", "short": "nicht hypoxämisch", "rank": "normal"}
    if po2 >= 60:
        return {"level": "leichtgradige arterielle Hypoxämie", "short": "leichtgradig", "rank": "mild"}
    if po2 >= 40:
        return {"level": "mittelgradige arterielle Hypoxämie", "short": "mittelgradig", "rank": "moderate"}
    return {"level": "schwergradige arterielle Hypoxämie", "short": "schwergradig", "rank": "severe"}


def classify_pf_oxygenation(pf: float) -> dict[str, str]:
    """P/F-basierte Schweregradeinteilung als reine Oxygenierungsorientierung."""
    if pf > 300:
        return {"level": "keine relevante P/F-basierte Oxygenierungsstörung", "short": "P/F >300", "rank": "normal"}
    if pf > 200:
        return {"level": "leichtgradige P/F-basierte Oxygenierungsstörung", "short": "leichtgradig", "rank": "mild"}
    if pf > 100:
        return {"level": "mittelgradige P/F-basierte Oxygenierungsstörung", "short": "mittelgradig", "rank": "moderate"}
    return {"level": "schwergradige P/F-basierte Oxygenierungsstörung", "short": "schwergradig", "rank": "severe"}


def assess_oxygenation(
    sample_type: str,
    po2: Optional[float],
    fio2_percent: Optional[float],
) -> Optional[dict[str, Any]]:
    """Beurteilt die arterielle Oxygenierung unter Berücksichtigung der FiO₂."""
    if po2 is None or not sample_type.lower().startswith("arter"):
        return None

    if fio2_percent is None:
        grade = classify_room_air_pao2(po2)
        if po2 < 80:
            summary = (
                f"PaO₂ {po2:.0f} mmHg: arterielle Hypoxämie. Falls die Probe unter Raumluft "
                f"abgenommen wurde, entspricht dies einer {grade['level']}."
            )
        else:
            summary = (
                f"PaO₂ {po2:.0f} mmHg: keine manifeste Hypoxämie nach der "
                f"orientierenden Raumluft-Einteilung."
            )
        return {
            "summary": summary,
            "severity": grade["level"],
            "severity_short": grade["short"],
            "rank": grade["rank"],
            "basis": "PaO₂; Raumluft nicht gesichert",
            "notes": [
                "FiO₂ fehlt: Das Ausmaß der Oxygenierungsstörung kann nicht sicher beurteilt werden.",
                "Alter, Höhe über dem Meeresspiegel und klinischer Kontext sind zusätzlich zu berücksichtigen.",
            ],
        }

    if fio2_percent <= 21.5:
        grade = classify_room_air_pao2(po2)
        summary = f"{grade['level'][0].upper() + grade['level'][1:]} unter Raumluft (PaO₂ {po2:.0f} mmHg)."
        notes = [
            "Die PaO₂-Grenzen sind eine orientierende BGA-Einteilung; Alter, Höhe und klinischer Verlauf bleiben relevant."
        ]
        if po2 < 60:
            notes.insert(0, "PaO₂ <60 mmHg: klinisch relevante arterielle Hypoxämie.")
        return {
            "summary": summary,
            "severity": grade["level"],
            "severity_short": grade["short"],
            "rank": grade["rank"],
            "basis": "arterieller PaO₂ unter Raumluft",
            "notes": notes,
        }

    pf = pf_ratio(po2, fio2_percent)
    grade = classify_pf_oxygenation(pf)
    summary = (
        f"{grade['level'][0].upper() + grade['level'][1:]} bei PaO₂ {po2:.0f} mmHg, "
        f"FiO₂ {fio2_percent:.0f}% und P/F {pf:.0f} mmHg."
    )
    return {
        "summary": summary,
        "severity": grade["level"],
        "severity_short": grade["short"],
        "rank": grade["rank"],
        "basis": "PaO₂/FiO₂",
        "notes": [
            "Unter Sauerstoffzufuhr darf der absolute PaO₂ nicht mit Raumluft-Grenzen graduiert werden; entscheidender ist der P/F-Quotient.",
            "Die P/F-Bänder allein stellen keine ARDS-Diagnose; zusätzliche klinische, bildgebende und respiratorische Kriterien sind erforderlich.",
        ],
    }


def validate_input(data: BGAInput) -> list[str]:
    checks = [
        (6.5 <= data.ph <= 8.0, "pH außerhalb 6,5–8,0."),
        (5 <= data.pco2 <= 150, "pCO₂ außerhalb 5–150 mmHg."),
        (2 <= data.hco3 <= 60, "HCO₃⁻ außerhalb 2–60 mmol/l."),
        (80 <= data.sodium <= 200, "Natrium außerhalb 80–200 mmol/l."),
        (40 <= data.chloride <= 160, "Chlorid außerhalb 40–160 mmol/l."),
    ]
    errors = [message for ok, message in checks if not ok]
    if data.albumin is not None and not 5 <= data.albumin <= 60:
        errors.append("Albumin außerhalb 5–60 g/l.")
    if data.sao2_percent is not None and not 0 <= data.sao2_percent <= 100:
        errors.append("SaO₂ muss 0–100 % betragen.")
    if data.fio2_percent is not None and not 21 <= data.fio2_percent <= 100:
        errors.append("FiO₂ muss 21–100 % betragen.")
    if not 0 <= data.urine_ketones <= 4:
        errors.append("Urin-Ketone müssen zwischen 0 und 4 Kreuzen liegen.")
    return errors


def analyse_bga(data: BGAInput) -> dict[str, Any]:
    errors = validate_input(data)
    if errors:
        return {"errors": errors}

    ag = calculate_anion_gap(data.sodium, data.chloride, data.hco3)
    expected_ag = expected_normal_ag(data.albumin)
    corrected_ag = albumin_corrected_ag(ag, data.albumin)
    ag_eval = corrected_ag if corrected_ag is not None else ag

    compensation = compensation_assessment(data.ph, data.pco2, data.hco3)

    result: dict[str, Any] = {
        "errors": [],
        "ph_status": classify_ph(data.ph),
        "processes": determine_processes(compensation),
        "compensation": compensation,
        "anion_gap": ag,
        "expected_normal_ag": expected_ag,
        "corrected_anion_gap": corrected_ag,
        "ag_interpretation": "",
        "delta_ratio": None,
        "delta_interpretation": None,
        "osmolality": None,
        "urine_anion_gap": None,
        "urine_ketones": None,
        "cao2": None,
        "pf_ratio": None,
        "oxygenation_assessment": None,
        "warnings": [],
    }

    if ag_eval > 16:
        result["ag_interpretation"] = "Erhöhte Anionenlücke: HAGMA wahrscheinlich."
        dr = delta_ratio(ag_eval, data.hco3)
        result["delta_ratio"] = dr
        if dr is not None:
            result["delta_interpretation"] = delta_ratio_interpretation(dr)
        elif data.hco3 >= HCO3_REF:
            result["delta_interpretation"] = (
                "HAGMA bei normalem/erhöhtem HCO₃⁻: zusätzliche metabolische Alkalose sehr wahrscheinlich; "
                "kein Quotient mit nichtpositivem Nenner."
            )
    elif has_metabolic_acidosis(compensation):
        result["ag_interpretation"] = (
            "Keine erhöhte Anionenlücke bei nachgewiesener metabolischer Azidose: "
            "NAGMA erwägen. Eine frühe HAGMA ist klinisch nicht sicher ausgeschlossen."
        )
    elif data.hco3 < HCO3_LOW and compensation.get("mode") == "respiratorische Alkalose":
        result["ag_interpretation"] = (
            "Anionenlücke nicht erhöht. Das erniedrigte HCO₃⁻ ist mit der "
            "Kompensation der respiratorischen Alkalose vereinbar; daraus allein "
            "ergibt sich kein Hinweis auf eine zusätzliche NAGMA."
        )
    else:
        result["ag_interpretation"] = "Anionenlücke nicht deutlich erhöht."

    if data.albumin is None:
        result["warnings"].append("Albumin fehlt: HAGMA kann unterschätzt werden.")

    if data.measured_osmolality is not None and data.glucose is not None and data.urea is not None:
        result["osmolality"] = {
            "calculated": calculated_osmolality(data.sodium, data.glucose, data.urea),
            "gap": osmolal_gap(data.measured_osmolality, data.sodium, data.glucose, data.urea),
        }

    if data.urine_na is not None and data.urine_k is not None and data.urine_cl is not None:
        uag = urine_anion_gap(data.urine_na, data.urine_k, data.urine_cl)
        result["urine_anion_gap"] = {
            "value": uag,
            "interpretation": (
                "negativ: bei isolierter NAGMA eher gastrointestinaler HCO₃⁻-Verlust"
                if uag < 0 else
                "positiv: bei isolierter NAGMA verminderte renale Säureelimination/RTA erwägen"
            ),
        }

    ketone_display = format_urine_ketones(data.urine_ketones)
    result["urine_ketones"] = {
        "grade": data.urine_ketones,
        "display": ketone_display,
        "interpretation": (
            "Keine semiquantitativ nachweisbaren Urinketone."
            if data.urine_ketones == 0
            else "Positive Urinketone; bei passender Klinik Ketose beziehungsweise Ketoazidose prüfen."
        ),
    }

    arterial = data.sample_type.lower().startswith("arter")
    if arterial and data.po2 is not None and data.hb is not None and data.sao2_percent is not None:
        result["cao2"] = arterial_oxygen_content(data.hb, data.sao2_percent, data.po2)
    if arterial and data.po2 is not None and data.fio2_percent is not None:
        result["pf_ratio"] = pf_ratio(data.po2, data.fio2_percent)
    result["oxygenation_assessment"] = assess_oxygenation(
        data.sample_type, data.po2, data.fio2_percent
    )
    if not arterial and data.po2 is not None:
        result["warnings"].append("Nichtarterielle Probe: pO₂ nicht zur arteriellen Oxygenierung verwenden.")

    return result
