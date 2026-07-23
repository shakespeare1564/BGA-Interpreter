# Systematische BGA-Analyse

Eine deterministische Streamlit-Web-App zur strukturierten Beurteilung einer Blutgasanalyse.

## Funktionen

- pH-Einordnung
- Erkennung respiratorischer und metabolischer Prozesse
- Kompensationsprüfung
- Serum-Anionenlücke und Albuminkorrektur
- HAGMA-/NAGMA-Hinweise
- Delta-Delta-Quotient
- Osmolalitätslücke
- Urin-Anionenlücke
- CaO₂ und P/F-Quotient
- kopierbarer Befundentwurf und JSON-Export

## Medizinische Grundlage

Der Kernalgorithmus folgt:

> Schiffler C, Jegerlehner S, Bodmer MP, Müller M.  
> Die systematische Interpretation der Blutgasanalyse – Schritt für Schritt.  
> Notaufnahme up2date 2025; 7:229–237. DOI 10.1055/a-2517-5186.

Der Artikel behandelt die Oxygenierung nicht systematisch. CaO₂ und P/F-Quotient sind ergänzende Standardberechnungen.

### Sicherheitsentscheidung beim Delta-Delta-Quotienten

Liegt bei HAGMA das HCO₃⁻ bei oder über 24 mmol/l, wäre der Nenner `24 − HCO₃⁻` null oder negativ. Die App erzwingt dann keinen formal irreführenden Quotienten, sondern weist direkt auf eine wahrscheinliche zusätzliche metabolische Alkalose hin.

## Lokal starten

Voraussetzung: Python 3.11 oder 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Unter Windows:

```powershell
.venv\Scripts\activate
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Auf Streamlit Community Cloud bereitstellen

1. Dieses Projekt in ein GitHub-Repository übertragen.
2. Bei Streamlit Community Cloud anmelden.
3. **Create app** auswählen.
4. Repository, Branch `main` und Entrypoint `app.py` angeben.
5. Bereitstellen.

`requirements.txt` liegt im Repository-Stamm.

## Datenschutz und klinische Nutzung

- Keine Namen, Geburtsdaten, Fallnummern oder andere identifizierende Patientendaten eingeben.
- Die App speichert im eigenen Code keine Eingaben dauerhaft. Hosting- und Plattformprotokolle sind davon unabhängig.
- Für klinischen Routinebetrieb sind Datenschutz, IT-Freigabe, Zweckbestimmung, Validierung und gegebenenfalls Medizinprodukterecht separat zu klären.
- Die App ist kein autonomes Diagnosesystem. Ärztliche Plausibilitätskontrolle bleibt zwingend.
