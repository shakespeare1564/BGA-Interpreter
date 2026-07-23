from __future__ import annotations

import json
import streamlit as st
from bga_logic import BGAInput, analyse_bga

st.set_page_config(page_title="Systematische BGA-Analyse", page_icon="🩸", layout="wide")
st.title("🩸 Systematische Blutgasanalyse")
st.caption("Rechenhilfe für Säure–Base-Status, Anionenlücke und ergänzende Oxygenierungsparameter.")

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
    albumin = c4.number_input("Albumin (g/l)", 5.0, 60.0, 40.0, 1.0, disabled=not albumin_known)

    st.subheader("2 · Oxygenierung und Zusatzparameter")
    c1, c2, c3, c4 = st.columns(4)
    po2_known = c1.checkbox("pO₂ vorhanden")
    po2 = c1.number_input("pO₂ (mmHg)", 10.0, 700.0, 90.0, 1.0, disabled=not po2_known)
    fio2_known = c2.checkbox("FiO₂ bekannt")
    fio2 = c2.number_input("FiO₂ (%)", 21.0, 100.0, 21.0, 1.0, disabled=not fio2_known)
    sao2_known = c3.checkbox("SaO₂ vorhanden")
    sao2 = c3.number_input("SaO₂ (%)", 0.0, 100.0, 97.0, 0.1, disabled=not sao2_known)
    hb_known = c4.checkbox("Hb vorhanden")
    hb = c4.number_input("Hb (g/dl)", 1.0, 25.0, 14.0, 0.1, disabled=not hb_known)

    c1, c2, c3, c4 = st.columns(4)
    lactate_known = c1.checkbox("Laktat vorhanden")
    lactate = c1.number_input("Laktat (mmol/l)", 0.0, 30.0, 1.0, 0.1, disabled=not lactate_known)
    potassium_known = c2.checkbox("Kalium vorhanden")
    potassium = c2.number_input("K⁺ (mmol/l)", 1.0, 10.0, 4.0, 0.1, disabled=not potassium_known)
    glucose_known = c3.checkbox("Glukose vorhanden")
    glucose = c3.number_input("Glukose (mmol/l)", 0.0, 100.0, 5.5, 0.1, disabled=not glucose_known)
    urea_known = c4.checkbox("Harnstoff vorhanden")
    urea = c4.number_input("Harnstoff (mmol/l)", 0.0, 100.0, 5.0, 0.1, disabled=not urea_known)

    with st.expander("Optionale Spezialdiagnostik"):
        c1, c2 = st.columns(2)
        osmo_known = c1.checkbox("Gemessene Osmolalität vorhanden")
        measured_osmo = c1.number_input("Osmolalität (mosmol/kg)", 100.0, 500.0, 290.0, 1.0, disabled=not osmo_known)
        urine_known = c2.checkbox("Urinelektrolyte vollständig")
        u1, u2, u3, u4 = st.columns(4)
        urine_na = u1.number_input("Urin-Na", 0.0, 400.0, 40.0, disabled=not urine_known)
        urine_k = u2.number_input("Urin-K", 0.0, 400.0, 30.0, disabled=not urine_known)
        urine_cl = u3.number_input("Urin-Cl", 0.0, 400.0, 90.0, disabled=not urine_known)
        urine_ph_known = u4.checkbox("Urin-pH vorhanden")
        urine_ph = u4.number_input("Urin-pH", 4.0, 9.0, 5.5, 0.1, disabled=not urine_ph_known)

    submitted = st.form_submit_button("BGA analysieren", type="primary", use_container_width=True)

if submitted:
    data = BGAInput(
        sample_type=sample_type, ph=ph, pco2=pco2, hco3=hco3,
        sodium=sodium, chloride=chloride,
        albumin=albumin if albumin_known else None,
        po2=po2 if po2_known else None,
        potassium=potassium if potassium_known else None,
        lactate=lactate if lactate_known else None,
        hb=hb if hb_known else None,
        sao2_percent=sao2 if sao2_known else None,
        fio2_percent=fio2 if fio2_known else None,
        glucose=glucose if glucose_known else None,
        urea=urea if urea_known else None,
        measured_osmolality=measured_osmo if osmo_known else None,
        urine_na=urine_na if urine_known else None,
        urine_k=urine_k if urine_known else None,
        urine_cl=urine_cl if urine_known else None,
        urine_ph=urine_ph if urine_ph_known else None,
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
    m4.metric("P/F-Quotient", f'{result["pf_ratio"]:.0f} mmHg' if result["pf_ratio"] is not None else "nicht berechenbar")

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
        if result["cao2"] is not None:
            st.metric("CaO₂", f'{result["cao2"]:.1f} ml O₂/dl')
            st.caption("CaO₂ = 1,34 × Hb × SaO₂ + 0,003 × pO₂")
        else:
            st.info("Für CaO₂ werden arterielle Probe, pO₂, Hb und SaO₂ benötigt.")
        if result["pf_ratio"] is not None:
            st.metric("P/F-Quotient", f'{result["pf_ratio"]:.0f} mmHg')
        else:
            st.info("Für P/F werden arterielle Probe, pO₂ und FiO₂ benötigt.")

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
