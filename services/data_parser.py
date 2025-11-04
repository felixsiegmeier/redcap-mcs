"""
DataParser Klasse zur Konsolidierung aller Parser und Hilfsfunktionen.
Diese Klasse akzeptiert eine Datei als Input und bietet alle verfügbaren Parser als eigene Methoden.
"""

from __future__ import annotations

import csv
import logging
import re
from io import StringIO, TextIOBase
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
from datetime import datetime, date

# Import nur der Schema-Definitionen
from schemas.parse_schemas.vitals import VitalsModel
from schemas.parse_schemas.lab import LabModel
from schemas.parse_schemas.respiratory import RespiratoryModel
from schemas.parse_schemas.ecmo import EcmoModel
from schemas.parse_schemas.impella import ImpellaModel
from schemas.parse_schemas.crrt import CrrtModel
from schemas.parse_schemas.medication import MedicationModel
from schemas.parse_schemas.fluidbalance import FluidBalanceModel

logger = logging.getLogger(__name__)


class DataParserBase:
    """Basisklasse mit allen Parsing-Operationen."""
    
    def __init__(self, file: Union[str, TextIOBase], delimiter: str = ";"):
        """Initialisiert den DataParser."""
        self.delimiter = delimiter
        self._clean_file: Optional[str] = None
        self._blocks: Optional[Dict[str, Dict[str, str]]] = None
        self._raw_input = file
        self._source_path: Optional[Path] = None
        self.raw_file = self._read_input(file)
        
        self.headers = {
            "Vitaldaten": ['Online erfasste Vitaldaten', 'Manuell erfasste Vitaldaten'],
            "Respiratordaten": ['Online erfasste Respiratorwerte', 'Beatmung', 'Manuell erfasste Respiratorwerte'],
            "Labor": ['Labor: Blutgase arteriell', 'Labor: Blutgase venös', 'Labor: Blutgase gv', 
                     'Labor: Blutgase unspez.', 'Labor: Blutbild', 'Labor: Differentialblutbild',
                     'Labor: Blutgruppe', 'Labor: Gerinnung', 'Labor: TEG', 'Labor: TAT',
                     'Labor: Enzyme', 'Labor: Retention', 'Labor: Lipide', 'Labor: Proteine',
                     'Labor: Elektrolyte', 'Labor: Blutzucker', 'Labor: Klinische Chemie',
                     'Labor: Medikamentenspiegel', 'Labor: Schilddrüse', 'Labor: Serologie/Infektion'],
            'Medikamentengaben': ["Medikamentengaben"],
            'Bilanz': ["Bilanz"],
            'ALLE Patientendaten': ["ALLE Patientendaten"]
        }
        
    def _read_input(self, raw: Union[str, TextIOBase, bytes, bytearray]) -> str:
        """Sorgt dafür, dass der Parser immer einen rohen CSV-String erhält."""
        if isinstance(raw, TextIOBase):
            contents = raw.read()
            if hasattr(raw, "seek"):
                raw.seek(0)
            return contents

        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8", errors="ignore")

        if isinstance(raw, str):
            if "\n" in raw:
                return raw
            potential_path = Path(raw)
            if potential_path.exists() and potential_path.is_file():
                self._source_path = potential_path
                return potential_path.read_text(encoding="utf-8", errors="ignore")
            return raw

        raise TypeError("Unsupported input type for DataParser")

    def _clean_csv(self) -> str:
        """Bereinigt die CSV-Datei."""
        if self._clean_file is not None:
            return self._clean_file
            
        lines = self.raw_file.splitlines()
        skip = {len(lines) - 1}  # Skip last line
        headers = []
        
        # Find lines to skip
        for i, line in enumerate(lines):
            line_stripped = line.lstrip()
            if "Ausdruck: Gesamte Akte" in line_stripped:
                headers.append(i)
            elif any(text in line_stripped for text in [
                "Bei aktuell laufenden Statusmodulen",
                "Datum/Uhrzeit bezieht sich jeweils auf den Intervallstart."
            ]):
                skip.add(i)
                if "Datum/Uhrzeit" in line_stripped:
                    skip.add(i - 1)
            elif re.search(r"Intervall:\s*\d{2}\s*min\.,?", line_stripped):
                skip.add(i)
        
        # Skip header blocks
        for j, h in enumerate(headers):
            skip.update(range(h, min(h + 8, len(lines))))
            if j > 0 and h - 1 >= 0:
                skip.add(h - 1)
        
        # Build clean file
        clean_lines = [line for i, line in enumerate(lines) if i not in skip]
        self._clean_file = "\n".join(clean_lines)
        return self._clean_file
    
    def _split_blocks(self) -> Dict[str, Dict[str, str]]:
        """Teilt die Datei in kategorisierte Blöcke auf.
        
        Lazy loading: Die Blöcke werden nur beim ersten Aufruf berechnet und gespeichert.
        Bei weiteren Aufrufen wird das gespeicherte Ergebnis direkt zurückgegeben.
        """
        if self._blocks is not None:
            return self._blocks
            
        lines = self._clean_csv().splitlines()
        result = {category: {} for category in self.headers}
        current_category = None
        current_block = None
        buffer = []

        for line in lines:
            key = line.split(self.delimiter, 1)[0].strip()
            
            # Check if line starts a new block
            found_category = None
            for category, blocks in self.headers.items():
                if key in blocks:
                    found_category = category
                    break
            
            if found_category:
                # Save previous buffer
                if current_category and current_block and buffer:
                    result[current_category][current_block] = "\n".join(buffer).strip()
                # Start new block
                current_category = found_category
                current_block = key
                buffer = []
            else:
                buffer.append(line)
        
        # Save final buffer
        if current_category and current_block and buffer:
            result[current_category][current_block] = "\n".join(buffer).strip()
            
        self._blocks = result
        return result
    
    def _get_first_entry(self, parts) -> Optional[Tuple[int, str]]:
        """Findet ersten nicht-leeren Eintrag."""
        for i, entry in enumerate(parts):
            if isinstance(entry, str) and entry.strip():
                return (i, entry.strip())
        return None
    
    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parst Timestamp."""
        ts_str = ts_str.strip()
        for fmt in ("%d.%m.%y %H:%M", "%d.%m.%Y %H:%M"):
            try:
                return datetime.strptime(ts_str, fmt)
            except (ValueError, TypeError):
                continue
        return None
    
    def _is_timestamp_row(self, parts) -> bool:
        """Prüft ob Zeile Timestamps enthält."""
        date_pattern = re.compile(r"\d{2}\.\d{2}\.\d{2,4}\s*\d{2}:\d{2}")
        return any(isinstance(tok, str) and date_pattern.search(tok) for tok in parts)
    
    def _parse_table_data(self, category_name: str, data_class, **options):
        """Parst tabellarische Daten (Vitals, Respiratory, Lab)."""
        blocks = self._split_blocks().get(category_name, {})
        data_list = []

        for key, block_str in blocks.items():
            timestamps = None
            lines = [line.rstrip('\r') for line in block_str.splitlines()]
            
            for line in lines:
                parts = line.split(self.delimiter)
                
                # Timestamp row?
                if self._is_timestamp_row(parts):
                    timestamps = [tok.strip() for tok in parts]
                    continue
                    
                if not timestamps:
                    continue
                    
                first_entry = self._get_first_entry(parts)
                if not first_entry:
                    continue
                    
                # Parse values
                for i, token in enumerate(parts):
                    if not isinstance(token, str) or not token.strip():
                        continue
                        
                    # Skip parameter column for lab data
                    if options.get('skip_first') and i == first_entry[0]:
                        continue
                        
                    # Clean token
                    clean_token = token.strip().replace(",", ".")
                    if options.get('clean_lab'):
                        clean_token = clean_token.replace("(-)", "").replace("(+)", "")
                        
                    try:
                        value = float(clean_token)
                    except (ValueError, TypeError):
                        value = clean_token
                        
                    # Get timestamp
                    try:
                        timestamp = self._parse_timestamp(timestamps[i])
                        if not timestamp:
                            continue
                    except (IndexError, TypeError):
                        continue
                        
                    # Clean category name
                    category = key.replace("Labor:", "").strip() if "Labor:" in key else key.strip()
                    
                    data_list.append(data_class(
                        timestamp=timestamp,
                        value=value,
                        category=category,
                        parameter=first_entry[1]
                    ))

        return pd.DataFrame([item.__dict__ for item in data_list])

    def get_blocks(self) -> Dict[str, Dict[str, str]]:
        """Gibt alle Datenblöcke zurück."""
        return self._split_blocks()

    @staticmethod
    def get_date_range_from_df(df: pd.DataFrame) -> Tuple[Optional[date], Optional[date]]:
        """Ermittelt Datumsbereich aus DataFrame."""
        try:
            ts = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
            return (ts.min().date(), ts.max().date()) if not ts.empty else (None, None)
        except:
            return (datetime(2010, 1, 1).date(), datetime.now().date())


class MedicationParserMixin(DataParserBase):
    def parse_medication_logic(self, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Parst Medikamentendaten."""
        blocks = self._split_blocks()
        med_text = blocks.get("Medikamentengaben", {}).get("Medikamentengaben", "")

        clean_text = self._clean_medication_text(med_text)
        lines = [line.split(self.delimiter) for line in clean_text.splitlines()]

        data_list = []
        buffer = []
        current_header = None

        for line in lines:
            if not self._is_timestamp_row(line):
                if buffer and current_header:
                    cols = self._get_medication_columns(current_header)
                    if cols:
                        data_list.extend(self._process_medication_block(buffer, cols, current_header))
                current_header = line
                buffer = []
            else:
                if current_header:
                    buffer.append(line)

        if buffer and current_header:
            cols = self._get_medication_columns(current_header)
            if cols:
                data_list.extend(self._process_medication_block(buffer, cols, current_header))

        return pd.DataFrame([item.__dict__ for item in data_list])

    def _clean_medication_text(self, text: str) -> str:
        """Bereinigt Medikamenten-Text."""
        return re.sub(
            r'"(.*?)"',
            lambda m: m.group(0).replace("\n", " ").replace("\r", "").replace('"', ""),
            text,
            flags=re.DOTALL,
        )

    def _extract_from_cell(self, cell_content: str, pattern: str, converter=None) -> List:
        """Extrahiert Werte aus Zelle mit Pattern."""
        matches = re.findall(pattern, cell_content)
        if converter:
            return [converter(match) for match in matches if converter(match) is not None]
        return matches

    def _get_medication_columns(self, header) -> Optional[Dict[str, int]]:
        """Findet Spalten-Indices für Medikamente."""
        category = next((entry for entry in header if isinstance(entry, str) and entry.strip()), "")
        try:
            return {
                'medication': header.index(category),
                'concentration': header.index("Konzentration"),
                'application': header.index("App.- form"),
                'start': header.index("Start/Änderung"),
                'stop': header.index("Stopp"),
                'rate': header.index("Rate(mL/h)")
            }
        except ValueError:
            return None

    def _process_medication_block(self, lines, cols, header) -> List[MedicationModel]:
        """Verarbeitet Medikamenten-Block."""
        result = []
        category = next((entry for entry in header if isinstance(entry, str) and entry.strip()), "")

        for line in lines:
            if len(line) <= max(cols.values()):
                continue

            start_times = self._extract_from_cell(
                line[cols['start']],
                r"\d{2}\.\d{2}\.\d{2,4}\s*\d{2}:\d{2}",
                self._parse_timestamp,
            )
            stop_times = self._extract_from_cell(
                line[cols['stop']],
                r"\d{2}\.\d{2}\.\d{2,4}\s*\d{2}:\d{2}",
                self._parse_timestamp,
            )
            rates = self._extract_from_cell(
                line[cols['rate']],
                r"\d+(?:[.,]\d+)?",
                lambda x: float(x.replace(",", ".")),
            )

            for i, start in enumerate(start_times):
                result.append(
                    MedicationModel(
                        medication=line[cols['medication']],
                        category=category,
                        concentration=line[cols['concentration']],
                        application=line[cols['application']],
                        start=start,
                        stop=stop_times[i] if i < len(stop_times) else None,
                        rate=rates[i] if i < len(rates) else None,
                    )
                )

        return result


class FluidBalanceParserMixin(DataParserBase):
    def parse_fluidbalance_logic(self) -> pd.DataFrame:
        """Parst Flüssigkeitsbilanz-Daten auf Basis der Bilanz-Blöcke."""
        blocks = self._split_blocks()
        fluid_text = blocks.get("Bilanz", {}).get("Bilanz", "")

        if not fluid_text:
            return pd.DataFrame()

        reader = list(csv.reader(StringIO(fluid_text), delimiter=self.delimiter))
        if not reader:
            return pd.DataFrame()

        header_row = reader[0]
        time_columns: Dict[int, str] = {}
        for idx, cell in enumerate(header_row):
            cleaned = cell.strip().strip('"')
            if cleaned and cleaned.lower() != "flüssigkeitsbilanz":
                time_columns[idx] = cleaned.replace("\n", " ")

        entries: List[FluidBalanceModel] = []
        current_category: Optional[str] = None

        for row in reader[1:]:
            label = row[3].strip() if len(row) > 3 else ""

            if not label:
                continue

            if not label.startswith("("):
                current_category = label
                continue

            parameter = label.strip("() ")
            for col_idx, value_raw in enumerate(row):
                if col_idx not in time_columns:
                    continue
                value_str = value_raw.strip().replace(" ", "")
                if not value_str:
                    continue
                value_str = value_str.replace(",", ".")
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                time_label = time_columns[col_idx]
                timestamp = self._time_range_to_timestamp(time_label)
                entries.append(
                    FluidBalanceModel(
                        timestamp=timestamp,
                        value=value,
                        category=current_category or "unknown",
                        parameter=parameter,
                        time_range=time_label,
                    )
                )

        if not entries:
            return pd.DataFrame()

        return pd.DataFrame([item.dict() for item in entries])

    def _time_range_to_timestamp(self, label: str) -> Optional[datetime]:
        """Ermittelt einen repräsentativen Timestamp aus einem Zeitbereichs-Label."""
        cleaned = label.strip().strip('"')
        cleaned = cleaned.replace("\n", " ")
        match = re.search(
            r"(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})\s*-\s*(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})",
            cleaned,
        )
        if match:
            start = self._parse_timestamp(match.group(1))
            end = self._parse_timestamp(match.group(2))
            if start and end:
                return start + (end - start) / 2
            return start or end

        return self._parse_timestamp(cleaned)


class AllPatientDataMixin(DataParserBase):
    def _extract_all_patient_data_headers(self, data_str: str) -> set:
        lines = data_str.splitlines()
        headers_set = set()
        for line in lines:
            l = line.split(self.delimiter)
            if len(l) > 2 and l[0] == "" and l[1] == "" and l[2] and l[2] != "Datum":
                headers_set.add(l[2])
        return headers_set

    def _get_from_all_patient_data_by_string(self, query: str) -> Dict[str, Dict[str, List[str]]]:
        patient_data = self._split_blocks().get("ALLE Patientendaten", {})
        if isinstance(patient_data, dict):
            data_str = next(iter(patient_data.values()), "")
        else:
            data_str = patient_data

        headers = self._extract_all_patient_data_headers(data_str)
        matching_headers = [header for header in headers if query.lower() in header.lower()]

        lines = data_str.splitlines()
        result: Dict[str, Dict[str, List[str]]] = {header: {} for header in matching_headers}

        current_header: Optional[str] = None
        current_sub_header_counter = 1
        current_sub_header: Optional[str] = None
        current_sub_header_line: Optional[str] = None
        buffer: List[str] = []

        for line in lines:
            parts = line.split(self.delimiter)
            if len(parts) < 3:
                continue

            key = parts[2]

            if key in headers:
                if current_header is not None and current_sub_header is not None and buffer:
                    result[current_header].setdefault(current_sub_header, []).extend(buffer)
                    buffer = []

                if key in matching_headers:
                    if key == current_header:
                        if current_sub_header_line is None:
                            current_sub_header_line = line
                        elif line != current_sub_header_line:
                            current_sub_header_counter += 1
                            current_sub_header_line = line
                    else:
                        current_sub_header_counter = 1

                    current_header = key
                    current_sub_header = f"{current_header} {current_sub_header_counter}"
                    result[current_header].setdefault(current_sub_header, [])
                else:
                    current_header = None
                    current_sub_header = None
                    current_sub_header_line = None
                    current_sub_header_counter = 1
            else:
                if current_header is not None:
                    buffer.append(line)

        if current_header is not None and current_sub_header is not None and buffer:
            result[current_header].setdefault(current_sub_header, []).extend(buffer)
        return result

    def _get_device_values(self, parts) -> Tuple[Optional[str], Optional[str]]:
        non_empty = [entry for entry in parts if isinstance(entry, str) and entry.strip()]
        if len(non_empty) >= 2:
            return non_empty[0], non_empty[1]
        return None, None

    def _find_timestamp(self, parts) -> Optional[datetime]:
        for token in parts:
            if isinstance(token, str) and re.search(r"\d{2}\.\d{2}\.\d{2,4}\s*\d{2}:\d{2}", token):
                return self._parse_timestamp(token)
        return None

    def _parse_device_data(self, search_term: str, data_class, nested=False):
        device_blocks = self._get_from_all_patient_data_by_string(search_term)
        data_list = []

        def process_lines(lines, category):
            timestamp = None
            for line in lines:
                parts = line.split(self.delimiter)

                if self._is_timestamp_row(parts):
                    timestamp = self._find_timestamp(parts)
                    continue

                if not timestamp:
                    continue

                parameter, value_str = self._get_device_values(parts)
                if not parameter or not value_str:
                    continue

                try:
                    value = float(value_str.replace(",", "."))
                except ValueError:
                    value = value_str

                data_list.append(
                    data_class(
                        timestamp=timestamp,
                        value=value,
                        category=category,
                        parameter=parameter,
                    )
                )

        if nested:
            for key, device_dict in device_blocks.items():
                for device_key, lines in device_dict.items():
                    process_lines(lines, device_key)
        else:
            for key, lines in device_blocks.get(search_term, {}).items():
                process_lines(lines, key)

        print(f"Parsed {len(data_list)} entries for {search_term}")
        return pd.DataFrame([item.__dict__ for item in data_list])

    def parse_from_all_patient_data(self, keyword: str) -> pd.DataFrame:
        all_data = self.parse_all_patient_data()
        matching_headers = [h for h in all_data.keys() if keyword.upper() in h.upper()]
        dfs = []
        for h in matching_headers:
            dfs.extend(list(all_data[h].values()))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def parse_all_patient_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        patient_data = self._split_blocks().get("ALLE Patientendaten", {})
        if isinstance(patient_data, dict):
            data_str = next(iter(patient_data.values()), "")
        else:
            data_str = patient_data

        headers = self._extract_all_patient_data_headers(data_str)
        result = {}

        for header in headers:
            blocks = self._get_from_all_patient_data_by_string(header)
            result[header] = {}

            for sub_header, lines in blocks.get(header, {}).items():
                data_list = []
                timestamp = None
                for line in lines:
                    parts = line.split(self.delimiter)

                    if self._is_timestamp_row(parts):
                        timestamp = self._find_timestamp(parts)
                        continue

                    if not timestamp:
                        continue

                    parameter, value_str = self._get_device_values(parts)
                    if not parameter or not value_str:
                        continue

                    try:
                        value = float(value_str.replace(",", "."))
                    except ValueError:
                        value = value_str

                    data_list.append(
                        {
                            'timestamp': timestamp,
                            'value': value,
                            'category': sub_header,
                            'parameter': parameter,
                            'source_header': header,
                        }
                    )

                if data_list:
                    result[header][sub_header] = pd.DataFrame(data_list)

        return result


class DeviceParserMixin(AllPatientDataMixin):
    def parse_nirs_logic(self) -> pd.DataFrame:
        """Parst NIRS-Daten anhand der generischen all_patient_data-Struktur."""
        all_patient_data = self.parse_all_patient_data()
        if not all_patient_data:
            return pd.DataFrame()

        candidate_headers = [
            header
            for header in all_patient_data.keys()
            if any(token in header.upper() for token in ("NIRS", "PSI", "ICP"))
        ]
        frames: List[pd.DataFrame] = []
        for header in candidate_headers:
            sub_blocks = all_patient_data.get(header, {})
            for sub_header, df in sub_blocks.items():
                if df is None or df.empty:
                    continue
                normalized = df.copy()
                normalized["source_header"] = header
                normalized["source_category"] = sub_header
                normalized["category"] = "nirs"
                frames.append(normalized)

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        if "timestamp" in result.columns:
            result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce")
            result = result.dropna(subset=["timestamp"])

        return result.reset_index(drop=True)


class RespiratoryParserMixin(AllPatientDataMixin):
    def _parse_aditional_respiratory_data(self, data_class) -> pd.DataFrame:
        hfnc_blocks = self._get_from_all_patient_data_by_string("High-Flow Nasen CPAP")
        o2_data = self._get_from_all_patient_data_by_string("O2 Gabe")
        return pd.DataFrame()

    def parse_respiratory_data(self) -> pd.DataFrame:
        table_data = self._parse_table_data("Respiratordaten", RespiratoryModel)
        mode_data = self._parse_aditional_respiratory_data(RespiratoryModel)
        return pd.concat([table_data, mode_data], axis=0)


class DataParser(
    MedicationParserMixin,
    FluidBalanceParserMixin,
    DeviceParserMixin,
    RespiratoryParserMixin,
):
    """Abwärtskompatible Fassade für die bisherigen Parser-Aufrufe."""

    pass