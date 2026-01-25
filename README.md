# MCS REDCap Exporter

Streamlit-App zum Prüfen, Erkunden und Aggregieren von MCS-Daten (ECMO/Impella, Labor, Vitals, Beatmung) in REDCap-Formulare.

## Schnellstart
- Python 3.11+ und `uv` empfohlen
- Installieren: `uv sync` (alternativ `pip install -r requirements.txt`)
- Starten: `uv run streamlit run app.py`

## Datenbasis
- Input ist eine semikolon-separierte CSV aus dem mlife-parser (Download-Link in der App).
- Pflichtspalten: `timestamp`, `source_type`, `parameter`, `value`; optional `category`, `rate`.
- Typische `source_type`: Lab, Vitals, Respiratory/Beatmung, Medication, ECMO, Impella, HÄMOFILTER/CRRT, NIRS.

## App Flow
1. Startseite (Upload): CSV laden, Grundvalidierung, Übergabe an den zentralen State.
2. Sidebar: Record-ID setzen, Zeitraum wählen (oder per MCS-Button auf ECMO/Impella-Zeitfenster setzen) und zwischen Views navigieren.
3. Übersicht: Zeitfenster, Datenquellen-Zählung und verfügbare MCS-Geräte anzeigen.
4. Data Explorer: Filter nach Quelle, Zeitraum, Parametern; optional 24h-Median, Ausreißerfilter, Altair-Zeitreihe.
5. Export Builder: Instrumente/Event auswählen (Labor, Hämodynamik/Beatmung/Medikation, ECMO/Pump, Impella), Aggregationsstrategie (`nearest`, `median`, `mean`, `first`, `last`) und Referenzzeiten setzen, Export-Daten erzeugen und als CSV laden.
6. Tagesansicht: Generierte Formulare pro Tag/Event prüfen und Einzelwerte bei Bedarf aus allen Tagesmessungen auswählen.

## Architektur
- Einstieg: [app.py](app.py) wählt Views anhand des Session-States.
- State: [state.py](state.py) hält Datenframe, UI-Status, Zeiträume, Export-Formulare und Geräte-Referenzzeiten.
- Views: [views/startpage.py](views/startpage.py), [views/sidebar.py](views/sidebar.py), [views/homepage.py](views/homepage.py), [views/data_explorer.py](views/data_explorer.py), [views/export_builder.py](views/export_builder.py), [views/daily_form.py](views/daily_form.py).
- Aggregation: Lab-Speziallogik in [services/aggregators/lab_aggregator.py](services/aggregators/lab_aggregator.py); generische Basisklasse in [services/aggregators/base.py](services/aggregators/base.py) und Fächer-spezifische Aggregatoren (z. B. Hämodynamik, ECMO, Impella) in [services/aggregators](services/aggregators).
- REDCap-Modelle: Pydantic-Schemas unter [schemas/db_schemas](schemas/db_schemas) definieren Felder und Validierungen pro Instrument.

## Code-Überblick (kurz)
- `state.py`: zentraler Session-State (DataFrame, Zeitfenster, Record-ID, Export-Forms). `load_data()` normalisiert Timestamp, setzt Zeitfenster und Geräte-Referenzzeiten. `get_data(source)` liefert gefilterte Sichten.
- `views/*`: reine UI-Logik; rufen `state.get_data()` und Aggregatoren indirekt über Export Builder auf.
- `services/aggregators/base.py`: Grundgerüst für alle Instrument-Aggregatoren (Tagesfilter, Regex-Matching auf `category`/`parameter`, Wertestrategien wie `nearest`, `median`, ...).
- `services/aggregators/lab_aggregator.py`: Labor-Aggregator mit Feld-Mapping und Spezialfällen (ACT, ECMELLA, nearest-Time).
- `services/aggregators/*_aggregator.py`: Fächer-spezifische Aggregatoren (z. B. Hämodynamik) erben von `BaseAggregator` und definieren ihr Feld-Mapping.
- `views/export_builder.py`: orchestriert Aggregation pro Tag/Event, speichert fertige Pydantic-Modelle in `state.export_forms`, bietet Download als REDCap-kompatible CSV.

## Aggregation im Detail
1) **Eingangsdaten**: Long-Format-CSV. Wichtige Spalten: `timestamp` (Datetime), `source_type` (z. B. Lab, Vitals, ECMO, Impella, Respiratory, Medication), `category` (Subgruppe) und `parameter` (Messname), `value` (Messwert), optional `rate` (Infusionsrate).
2) **Tagesfilter**: Jeder Aggregator filtert auf das Ziel-Datum (`timestamp.date == selected_day`).
3) **Feld-Mapping**:
	- Labor: `LAB_FIELD_MAP` in [services/aggregators/mapping.py](services/aggregators/mapping.py) ordnet REDCap-Felder via `(source_type, category_pattern, parameter_pattern)` zu (z. B. `"pc02": ("Lab", "Blutgase arteriell", "^PCO2")`).
	- Generische Aggregatoren: `FIELD_MAP` (z. B. in Hämodynamik) enthält Tupel `(source_type, category_pattern, parameter_pattern)`, ausgewertet via Regex auf `category`/`parameter`.
4) **Wertestrategie** (`value_strategy` im State):
	- `nearest`: Wert mit geringster Zeitdifferenz zur Referenzzeit (geräteabhängig aus Sidebar/Builder oder automatisch aus frühestem Device-Timestamp).
	- `median`, `mean`, `first`, `last`: Standard-Aggregate über die Tageswerte.
5) **Spezialfälle**:
	- ACT: eigener `source_type` wird separat gelesen.
	- ECMELLA: Flag, wenn am Tag sowohl ECMO- als auch Impella-Daten existieren.
	- Medikamente (Hämodynamik): Infusionsraten in ml/h werden mit Konzentration (aus Perfusor-String geparst) und Patientengewicht (aus `PatientInfo`) zu µg/kg/min umgerechnet; Fertigspritzen werden ignoriert.
6) **Export-Modelle**: Nach Aggregation werden Pydantic-Modelle (z. B. `LabModel`, `HemodynamicsModel`) gebaut. Diese liegen in `state.export_forms` unter Schlüsseln wie `labor_ecls_arm_2`.
7) **Download**: Export Builder sammelt alle Modelle, serialisiert mit Schema-konformen Formaten (Komma-Dezimal, DD/MM/YYYY, HH:MM) und bietet eine CSV zum REDCap-Import.

## Arbeiten mit Exporten
- Zeiträume steuern globale Filterung sowie die Tagesliste im Export Builder.
- Strategien: `nearest` nutzt gerätespezifische Referenzzeiten, `median`/`mean` mitteln Tageswerte, `first`/`last` wählen chronologisch.
- Download erzeugt eine REDCap-kompatible CSV mit gültigen Validierungstypen (Komma-Dezimalpunkt, DD/MM/YYYY, HH:MM).

## Entwicklung
- Hot-Reload: `uv run streamlit run app.py`
- Sanity-Check Imports: `uv run python -c "import app; print('OK')"`
- Tests: falls ergänzt, mit `uv run pytest`

## Wartung & Erweiterung
- Neue Instrumente: Aggregator (Subklasse von BaseAggregator) in [services/aggregators](services/aggregators) anlegen und im Export Builder registrieren.
- Neue Felder: Mapping im jeweiligen Aggregator erweitern und Schema in [schemas/db_schemas](schemas/db_schemas) anpassen.
- Zusätzliche Views: Datei in [views](views) ergänzen und in [app.py](app.py) routen.
