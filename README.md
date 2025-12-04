# mLife Data Parser

Ein Tool zur Konsolidierung und Transformation von medizinischen Patientendaten (CSV) in ein einheitliches "Long Format" (Tidy Data).

## Features

- **Parsing**: Liest komplexe, heterogene CSV-Exportdateien (mLife).
- **Konsolidierung**: Führt Vitaldaten, Labordaten, Beatmung, Medikamente, Bilanzierung und Gerätedaten (ECMO, Impella, CRRT, NIRS) zusammen.
- **Formatierung**: Gibt eine bereinigte CSV-Datei im Long Format aus (`timestamp`, `source_type`, `category`, `parameter`, `value`).
- **Validierung**: Nutzt Pydantic-Modelle zur Sicherstellung der Datenintegrität.

## Installation

1. Repository klonen.
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   # oder mit uv
   uv sync
   ```

## Nutzung

### Kommandozeile (CLI)

```bash
python cli.py <input_file> [-o output.csv]
```

Beispiel:
```bash
python cli.py data/gesamte_akte.csv -o mein_export.csv
```

### Grafische Oberfläche (GUI)

Startet eine minimale Benutzeroberfläche zur Dateiauswahl:

```bash
python main.py
```

## Projektstruktur

```
.
├── cli.py                  # CLI Einstiegspunkt
├── main.py                 # GUI Einstiegspunkt (Flet)
├── services/
│   ├── data_parser.py      # Kern-Parsing-Logik & Mixins
│   └── pipeline.py         # Orchestrierung des Parsing-Prozesses
└── schemas/
    └── parse_schemas/      # Pydantic Datenmodelle
        ├── base.py         # Basisklasse (BaseDataModel)
        ├── vitals.py
        ├── lab.py
        ├── medication.py
        └── ...
```

## Datenmodell

Alle Daten werden auf ein gemeinsames Schema gemappt:

- `timestamp`: Zeitpunkt der Messung/Handlung
- `source_type`: Herkunft (z.B. "Vitals", "Lab", "Medication")
- `category`: Unterkategorie (z.B. "Blutgase", "Katecholamine")
- `parameter`: Name des Parameters (z.B. "pH", "Norepinephrin")
- `value`: Numerischer Wert oder Textwert

Zusätzliche Felder (z.B. für Medikamente: `rate`, `concentration`) sind im Modell vorhanden und werden bei Bedarf mit ausgegeben.
