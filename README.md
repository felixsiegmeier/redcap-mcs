# Clean M-Life

Anwendung zur Analyse, Aggregation und Visualisierung medizinischer Patientendaten.

## Schnellstart
- Repository klonen: `git clone <repo-url>`
- Abhängigkeiten installieren (über `uv` oder klassisch):
  - `uv sync` **oder** `pip install -r requirements.txt`

## Architekturüberblick
```
[CSV Upload]
    ↓
[Parser (services/data_parser.py)]
    ↓
[State Management (state_provider)]
    ↓
[Aggregation (services/value_aggregation)]
    ↓
[Views (views/…)]
```

### 1. Datenquelle & Upload
- CSV-Dateien liegen typischerweise im Ordner `data/`.
- Der Upload erfolgt über die Startseite (`views/startpage.py`).
- Dateien werden an `StateProvider.parse_data_to_state()` weitergegeben.

### 2. Parsing & Transformation
- Implementiert in `services/data_parser.py`.
- Die Klasse `DataParser` kombiniert spezialisierte Mixins (`MedicationParserMixin`, `DeviceParserMixin` etc.) auf Basis der gemeinsamen `DataParserBase`.
- Kernschritte:
  - `_clean_csv()` und `_split_blocks()` bereiten Rohdaten vor.
  - Tabellarische Werte werden via `_parse_table_data()` in `pandas.DataFrame` überführt.
  - Spezifische Parser (`parse_medication_logic`, `parse_fluidbalance_logic`, `parse_respiratory_data`, `parse_nirs_logic`, …) nutzen Pydantic-Modelle aus `schemas/parse_schemas/` zur Validierung.
- Rückgaben fließen als DataFrames in den Applikationszustand.

### 3. State Management
- `state_provider/state_provider.py` kapselt den Zugriff auf den App-State.
- Delegation:
  - `QueryManager` (lesende Operationen, Filter, Aggregationen, Zeitbereichs-Abfragen).
  - `DataManager` (Mutationen, Parsing, Formular-Updates).
- `AppState` (`schemas/app_state_schemas/app_state.py`) speichert Parsed Data, UI-Status, Metadaten und Zeitbereiche.

### 4. Aggregation & Value Services
- Spezialisierte Aggregatoren liegen in `services/value_aggregation/` (z.B. `lab_aggregator.py`).
- Aufrufende Komponenten geben Parameter wie Datum, Kategorie, Aggregationsstrategie (median, mean, first, last, nearest) an.
- Aggregatoren beziehen Daten ausschließlich über den `state_provider`.

### 5. Views & UI
- UI-Komponenten befinden sich im Verzeichnis `views/`.
- Beispiele:
  - `homepage.py` zeigt eine Übersicht.
  - `vitals_data.py`, `lab_data.py` visualisieren Messwerte.
  - `export_builder.py`, `lab_form.py` erzeugen strukturierte Formulare.
- `views/sidebar.py` steuert Navigation, Record-ID und Datumsbereich.
- Views interagieren ausschließlich über den `state_provider`, um Datenkohärenz sicherzustellen.

## Utility-Funktionen
- Gemeinsame Hilfsfunktionen rund um Datumskonvertierungen wurden in `services/utils.py` konsolidiert (`coerce_to_datetime`, `normalize_date_range`, `expand_date_range_to_bounds`).
- Diese Utilities werden u.a. von Sidebar, Export Builder und DataManager verwendet, um Verdopplung zu vermeiden.

## Erweiterungspunkte
- **Neue Parser**: Methoden im passenden Mixin ergänzen und in `DataManager.parse_data_to_state()` verdrahten.
- **Neue Aggregationen**: Im Ordner `services/value_aggregation/` platzieren; Zugriff über `state_provider.query_manager` sicherstellen.
- **Weitere Views**: Neue Datei in `views/` anlegen und in `app.py` registrieren.
- **Schemas**: Neue Datenmodelle unter `schemas/` hinzufügen bzw. erweitern.

## Entwicklung & Tests
- Lokale Imports prüfen: `uv run python -c "import app; print('OK')"`

- Bestehende Tests unter `tests/` starten: `uv run pytest`

## Lizenz
- (Hier Lizenzinformationen ergänzen, falls erforderlich.)
