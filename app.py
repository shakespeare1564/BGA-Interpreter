from __future__ import annotations

import json
import streamlit as st
from bga_logic import BGAInput, analyse_bga

st.set_page_config(page_title="Systematische BGA-Analyse", page_icon="🩸", layout="wide")
st.title("🩸 Systematische Blutgasanalyse")
st.caption("Rechenhilfe für Säure–Base-Status, Anionenlücke und ergänzende Oxygenierungsparameter.")
st.caption("Version 5 · Zusatzparameter ohne Kontrollkästchen")

with st.expander("Wichtige Hinweise"):
    st.markdown(
        """
- Ärztliche Rechen- und Strukturierungshilfe, **kein autonomes Diagnosesystem**.
- Klinik, Verlauf, Präanalytik, Beatmung und Labor müssen mitbeurteilt werden.
- **Keine identifizierenden Patientendaten** eingeben.
- Der Säure–Base-Kern folgt dem 5-Schritte-Schema nach Schiffler et al. (2025).
- CaO₂ und P/F-Quotient sind ergänzende Standardberechnungen; der Artikel behandelt die Oxygenierung nicht systematisch.
- Kompensationsformeln und Delta-Ratio sind Näherungen.
        """
    )

with st.form("bga_form"):
    st.subheader("1 · Probe und Kernparameter")
    c1, c2, c3, c4 = st.columns(4)
    sample_type = c1.selectbox("Entnahme", ["arteriell", "venös", "kapillär"])
    ph = c2.number_input("pH", 6.50, 8.00, 7.40, 0.01, format="%.2f")
    pco2 = c3.number_input("pCO₂ (mmHg)", 5.0, 150.0, 40.0, 1.0)
    hco3 = c4.number_input("HCO₃⁻ (mmol/l)", 2.0, 60.0, 24.0, 0.5)

    c1, c2, c3, c4 = st.columns(4)
    sodium = c1.number_input("Na⁺ (mmol/l)", 80.0, 200.0, 140.0, 1.0)
    chloride = c2.number_input("Cl⁻ (mmol/l)", 40.0, 160.0, 104.0, 1.0)
    albumin_known = c3.checkbox("Albumin vorhanden", True)
    albumin = c4.number_input("Albumin (g/l)", 5.0, 60.0, 40.0, 1.0)

    st.subheader("2 · Oxygenierung und Zusatzparameter")
    st.caption("Nicht vorliegende Zusatzwerte einfach leer lassen.")
    c1, c2, c3, c4 = st.columns(4)
    po2 = c1.number_input(
        "pO₂ (mmHg)",
        min_value=10.0,
        max_value=700.0,
        value=None,
        step=1.0,
        placeholder="optional",
    )
    fio2 = c2.number_input(
        "FiO₂ (%)",
        min_value=21.0,
        max_value=100.0,
        value=None,
        step=1.0,
        placeholder="z. B. 21",
    )
    sao2 = c3.number_input(
        "SaO₂ (%)",
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )
    hb = c4.number_input(
        "Hb (g/dl)",
        min_value=1.0,
        max_value=25.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )

    c1, c2, c3, c4 = st.columns(4)
    lactate = c1.number_input(
        "Laktat (mmol/l)",
        min_value=0.0,
        max_value=30.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )
    potassium = c2.number_input(
        "K⁺ (mmol/l)",
        min_value=1.0,
        max_value=10.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )
    glucose = c3.number_input(
        "Glukose (mmol/l)",
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )
    urea = c4.number_input(
        "Harnstoff (mmol/l)",
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=0.1,
        placeholder="optional",
    )

    with st.expander("Optionale Spezialdiagnostik"):
        measured_osmo = st.number_input(
            "Gemessene Osmolalität (mosmol/kg)",
            min_value=100.0,
            max_value=500.0,
            value=None,
            step=1.0,
            placeholder="optional",
        )
        u1, u2, u3, u4 = st.columns(4)
        urine_na = u1.number_input(
            "Urin-Na (mmol/l)",
            min_value=0.0,
            max_value=400.0,
            value=None,
            step=1.0,
            placeholder="optional",
        )
        urine_k = u2.number_input(
            "Urin-K (mmol/l)",
            min_value=0.0,
            max_value=400.0,
            value=None,
            step=1.0,
            placeholder="optional",
        )
        urine_cl = u3.number_input(
            "Urin-Cl (mmol/l)",
            min_value=0.0,
            max_value=400.0,
            value=None,
            step=1.0,
            placeholder="optional",
        )
        urine_ph = u4.number_input(
            "Urin-pH",
            min_value=4.0,
            max_value=9.0,
            value=None,
            step=0.1,
            placeholder="optional",
        )

    submitted = st.form_submit_button("BGA analysieren", type="primary", use_container_width=True)

if submitted:
    data = BGAInput(
        sample_type=sample_type, ph=ph, pco2=pco2, hco3=hco3,
        sodium=sodium, chloride=chloride,
        albumin=albumin if albumin_known else None,
        po2=po2,
        potassium=potassium,
        lactate=lactate,
        hb=hb,
        sao2_percent=sao2,
        fio2_percent=fio2,
        glucose=glucose,
        urea=urea,
        measured_osmolality=measured_osmo,
        urine_na=urine_na,
        urine_k=urine_k,
        urine_cl=urine_cl,
        urine_ph=urine_ph,
    )
    result = analyse_bga(data)
    if result["errors"]:
        for error in result["errors"]:
            st.error(error)
        st.stop()

    st.divider()
    st.header("Ergebnis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("pH-Einordnung", result["ph_status"])
    m2.metric("Anionenlücke", f'{result["anion_gap"]:.1f} mmol/l')
    m3.metric("Albuminkorrigierte AG", f'{result["corrected_anion_gap"]:.1f} mmol/l' if result["corrected_anion_gap"] is not None else "nicht berechenbar")
    oxy = result["oxygenation_assessment"]
    m4.metric("Oxygenierungsstörung", oxy["severity_short"] if oxy is not None else "nicht beurteilbar")

    tab1, tab2, tab3, tab4 = st.tabs(["Säure–Base", "Anionenlücke", "Oxygenierung", "Dokumentation"])

    with tab1:
        st.subheader("Erkannte Prozesse")
        for item in result["processes"]:
            st.write(f"• {item}")
        comp = result["compensation"]
        st.subheader("Kompensationsprüfung")
        st.write(f'**Einordnung:** {comp["mode"]}')
        for detail in comp["details"]:
            st.info(detail)
        for flag in comp["flags"]:
            st.warning(flag)

    with tab2:
        st.write(f'**Gemessene AG:** {result["anion_gap"]:.1f} mmol/l')
        if result["expected_normal_ag"] is not None:
            st.write(f'**Bei Albumin erwartete normale AG:** {result["expected_normal_ag"]:.1f} mmol/l')
        if result["corrected_anion_gap"] is not None:
            st.write(f'**Auf Albumin 40 g/l korrigierte AG:** {result["corrected_anion_gap"]:.1f} mmol/l')
        st.success(result["ag_interpretation"])
        if result["delta_ratio"] is not None:
            st.write(f'**Delta-Delta-Quotient:** {result["delta_ratio"]:.2f}')
        if result["delta_interpretation"]:
            st.warning(result["delta_interpretation"])
        if result["osmolality"] is not None:
            st.write(f'**Berechnete Osmolalität:** {result["osmolality"]["calculated"]:.1f} mosmol/kg')
            st.write(f'**Osmolalitätslücke:** {result["osmolality"]["gap"]:.1f} mosmol/kg')
        if result["urine_anion_gap"] is not None:
            st.write(f'**Urin-Anionenlücke:** {result["urine_anion_gap"]["value"]:.1f} mmol/l')
            st.info(result["urine_anion_gap"]["interpretation"])

    with tab3:
        if sample_type != "arteriell":
            st.warning("Nichtarterielle Probe: pO₂ nicht zur arteriellen Oxygenierungsbeurteilung verwenden.")

        oxy = result["oxygenation_assessment"]
        if oxy is not None:
            if oxy["rank"] == "severe":
                st.error(oxy["summary"])
            elif oxy["rank"] in {"moderate", "mild"}:
                st.warning(oxy["summary"])
            else:
                st.success(oxy["summary"])
            st.caption(f'Bewertungsgrundlage: {oxy["basis"]}')
            for note in oxy["notes"]:
                st.info(note)
        elif sample_type == "arteriell":
            st.info("Für die Schweregradeinordnung wird ein arterieller pO₂ benötigt.")

        c_oxy1, c_oxy2 = st.columns(2)
        c_oxy1.metric(
            "P/F-Quotient",
            f'{result["pf_ratio"]:.0f} mmHg' if result["pf_ratio"] is not None else "nicht berechenbar",
        )
        if result["cao2"] is not None:
            c_oxy2.metric("CaO₂", f'{result["cao2"]:.1f} ml O₂/dl')
            c_oxy2.caption("CaO₂ = 1,34 × Hb × SaO₂ + 0,003 × pO₂")
        else:
            c_oxy2.metric("CaO₂", "nicht berechenbar")
            c_oxy2.caption("Benötigt arterielle Probe, pO₂, Hb und SaO₂.")

    with tab4:
        comp = result["compensation"]
        lines = [
            f'{result["ph_status"]} bei pH {ph:.2f}.',
            "Prozesse: " + "; ".join(result["processes"]) + ".",
            f'Kompensationsbeurteilung: {comp["mode"]}.',
            *comp["details"], *comp["flags"],
            f'Anionenlücke {result["anion_gap"]:.1f} mmol/l.',
        ]
        if result["corrected_anion_gap"] is not None:
            lines.append(f'Albuminkorrigierte Anionenlücke {result["corrected_anion_gap"]:.1f} mmol/l.')
        lines.append(result["ag_interpretation"])
        if result["delta_interpretation"]:
            lines.append(result["delta_interpretation"])
        if result["oxygenation_assessment"] is not None:
            lines.append(result["oxygenation_assessment"]["summary"])
            lines.extend(result["oxygenation_assessment"]["notes"])
        if result["cao2"] is not None:
            lines.append(f'CaO₂ {result["cao2"]:.1f} ml O₂/dl.')
        if result["pf_ratio"] is not None:
            lines.append(f'P/F-Quotient {result["pf_ratio"]:.0f} mmHg.')
        for warning in result["warnings"]:
            lines.append("Hinweis: " + warning)
        report = " ".join(lines)
        st.text_area("Kopierbarer Befundentwurf", report, height=220)
        st.download_button(
            "Ergebnis als JSON herunterladen",
            json.dumps({"input": data.to_dict(), "result": result}, ensure_ascii=False, indent=2),
            "bga_analyse.json", "application/json", use_container_width=True,
        )

    for warning in result["warnings"]:
        st.warning(warning)

st.divider()
st.caption("Literaturgrundlage: Schiffler C et al. Notaufnahme up2date 2025; 7:229–237. DOI 10.1055/a-2517-5186. Ärztliche Plausibilitätskontrolle erforderlich.")
