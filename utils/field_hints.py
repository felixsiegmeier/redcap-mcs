
import pandas as pd
import streamlit as st
from datetime import date, datetime
from typing import List, Optional, Tuple, Any

from state import get_data

def get_form_date(form: Any) -> Optional[date]:
    """Holt das Datum aus einem Formular-Objekt."""
    date_fields = [
        "timestamp", "date", "birthdate", 
        "assess_date_labor", "assess_date_hemo", 
        "ecls_compl_date", "imp_compl_date",
        "pre_assess_date", "pre_assess_date_i"
    ]
    for field in date_fields:
        val = getattr(form, field, None) if not hasattr(form, "get") else form.get(field)
        if val:
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val).date()
                except ValueError:
                    try:
                        return datetime.strptime(val, "%Y-%m-%d").date()
                    except ValueError:
                        pass
    return None

# Feld-Labels (erweitert)
FIELD_LABELS = {
    # Labor
    "ph": "pH", "pc02": "PCO2", "p02": "PO2", "hco3": "HCO3", "be": "BE",
    "sa02": "SaO2 (%)", "k": "Kalium", "na": "Natrium", "gluc": "Glukose",
    "lactate": "Laktat", "wbc": "Leukozyten", "hb": "Hämoglobin", "hct": "Hämatokrit",
    "plt": "Thrombozyten", "ptt": "PTT", "quick": "Quick (%)", "inr": "INR",
    "act": "ACT", "ck": "CK", "ckmb": "CK-MB", "got": "GOT", "alat": "ALAT",
    "ggt": "GGT", "ldh": "LDH", "lipase": "Lipase", "crea": "Kreatinin",
    "cc": "Krea-Clearance", "urea": "Harnstoff", "crp": "CRP", "pct": "PCT",
    "bili": "Bilirubin", "albumin": "Albumin", "fhb": "freies Hb", "hapto": "Haptoglobin",
    "sv02": "SvO2 (%)",
    # Hemodynamics
    "hr": "Herzfrequenz", "sys_bp": "RR sys", "dia_bp": "RR dia", "mean_bp": "MAP",
    "cvp": "ZVD", "nirs_left_c": "NIRS links cerebral", "nirs_right_c": "NIRS rechts cerebral",
    "nirs_left_f": "NIRS links femoral", "nirs_right_f": "NIRS rechts femoral",
    "fi02": "FiO2 (%)", "vent_peep": "PEEP", "vent_pip": "PIP", "conv_vent_rate": "Atemfrequenz",
    "norepinephrine": "Noradrenalin", "epinephrine": "Adrenalin", "dobutamine": "Dobutamin",
    "milrinone": "Milrinon", "vasopressin": "Vasopressin",
    "ery_t": "Erythrozyten", "ffp_t": "FFP", "thromb_t": "Thrombozyten", 
    "ppsb_t": "PPSB", "fib_t": "Fibrinogen",
    "urine": "Urin (ml)", "output_renal_repl": "CRRT Output", "fluid_balance_numb": "Bilanz",
    # ECMO
    "ecls_rpm": "Drehzahl (rpm)", "ecls_pf": "Blutfluss (L/min)", 
    "ecls_gf": "Gasfluss (L/min)", "ecls_fi02": "FiO2 (%)",
    # Impella
    "imp_flow": "Flow (L/min)", "imp_purge_flow": "Purge-Flow (ml/h)",
    "imp_purge_pressure": "Purge-Druck (mmHg)", "imp_p_level": "P-Level",
}

# Mapping: Feld -> (source_type, category_pattern, parameter_pattern)
# Für das Abrufen aller Tageswerte
FIELD_TO_SOURCE = {
    # Labor (aus Lab source_type)
    "pc02": ("Lab", "Blutgase arteriell", r"^PCO2"),
    "p02": ("Lab", "Blutgase arteriell", r"^PO2"),
    "ph": ("Lab", "Blutgase arteriell", r"^PH$|^PH "),
    "hco3": ("Lab", "Blutgase arteriell", r"^HCO3"),
    "be": ("Lab", "Blutgase arteriell", r"^ABEc"),
    "sa02": ("Lab", "Blutgase arteriell", r"^O2-SAETTIGUNG"),
    "k": ("Lab", "Blutgase arteriell", r"^KALIUM"),
    "na": ("Lab", "Blutgase arteriell", r"^NATRIUM"),
    "gluc": ("Lab", "Blutgase arteriell", r"^GLUCOSE"),
    "lactate": ("Lab", "Blutgase arteriell", r"^LACTAT"),
    "sv02": ("Lab", "Blutgase venös", r"^O2-SAETTIGUNG"),
    "wbc": ("Lab", "Blutbild", r"^WBC"),
    "hb": ("Lab", "Blutbild", r"^HB"),
    "hct": ("Lab", "Blutbild", r"^HCT"),
    "plt": ("Lab", "Blutbild", r"^PLT"),
    "ptt": ("Lab", "Gerinnung", r"^PTT"),
    "quick": ("Lab", "Gerinnung", r"^TPZ"),
    "inr": ("Lab", "Gerinnung", r"^INR"),
    "ck": ("Lab", "Enzyme", r"^CK \[|^CK$"),
    "ckmb": ("Lab", "Enzyme", r"^CK-MB"),
    "got": ("Lab", "Enzyme", r"^GOT"),
    "alat": ("Lab", "Enzyme", r"^GPT"),
    "ggt": ("Lab", "Enzyme", r"^GGT"),
    "ldh": ("Lab", "Enzyme", r"^LDH"),
    "lipase": ("Lab", "Enzyme", r"^LIPASE"),
    "crp": ("Lab", "Klinische Chemie|Proteine", r"^CRP"),
    "pct": ("Lab", "Klinische Chemie|Proteine", r"^PROCALCITONIN"),
    "crea": ("Lab", "Klinische Chemie|Retention", r"^KREATININ"),
    "urea": ("Lab", "Klinische Chemie|Retention", r"^HARNSTOFF"),
    "cc": ("Lab", "Klinische Chemie|Retention", r"^GFRKREA"),
    "bili": ("Lab", "Klinische Chemie", r"^BILI"),
    "albumin": ("Lab", "Klinische Chemie|Proteine", r"^ALBUMIN"),
    "fhb": ("Lab", "Blutbild|Klinische Chemie", r"^FREIES HB"),
    "hapto": ("Lab", "Klinische Chemie|Proteine", r"^HAPTOGLOBIN"),
    # Vitals
    "hr": ("Vitals", ".*", r"^HF\s*\["),
    "sys_bp": ("Vitals", ".*", r"^ABPs\s*\[|^ARTs\s*\["),
    "dia_bp": ("Vitals", ".*", r"^ABPd\s*\[|^ARTd\s*\["),
    "mean_bp": ("Vitals", ".*", r"^ABPm\s*\[|^ARTm\s*\["),
    "cvp": ("Vitals", ".*", r"^ZVDm\s*\["),
    "pcwp": ("Vitals", r"^Online.*", r"^PCWP\s*\[|^PAWP\s*\["),
    "sys_pap": ("Vitals", r"^Online.*", r"^PAPs\s*\["),
    "dia_pap": ("Vitals", r"^Online.*", r"^PAPd\s*\["),
    "mean_pap": ("Vitals", r"^Online.*", r"^PAPm\s*\["),
    "ci": ("Vitals", r"^Online.*", r"^CCI\s*\[|^HZV"),
    "sp02": ("Vitals", ".*", r"^SpO2\s*\[%\]"),
    "nirs_left_c": ("Vitals", ".*", r"NIRS Channel 1 RSO2|NIRS.*Channel.*1"),
    "nirs_right_c": ("Vitals", ".*", r"NIRS Channel 2 RSO2|NIRS.*Channel.*2"),
    "nirs_left_f": ("Vitals", ".*", r"NIRS Channel 3 RSO2|NIRS.*Channel.*3"),
    "nirs_right_f": ("Vitals", ".*", r"NIRS Channel 4 RSO2|NIRS.*Channel.*4"),
    # Respiratory
    "fi02": ("Respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)"),
    "o2": ("O2_Supply", ".*", r"^O2\s*l/min"),
    "vent_peep": ("Respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)"),
    "vent_pip": ("Respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz"),
    "conv_vent_rate": ("Respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz"),
    # Neurologie
    "gcs": ("GCS", ".*", r"^Summe GCS2"),
    # ECMO
    "ecls_rpm": ("ECMO", ".*", r"^Drehzahl"),
    "ecls_pf": ("ECMO", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min"),
    "ecls_gf": ("ECMO", ".*", r"^Gasfluss"),
    "ecls_fi02": ("ECMO", ".*", r"^FiO2"),
    # Impella
    "imp_flow": ("Impella", ".*", r"^HZV"),
    "imp_purge_flow": ("Impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h"),
    "imp_purge_pressure": ("Impella", ".*", r"Purgedruck"),
    "imp_p_level": ("Impella", ".*", r"P-Level|P\s*Level"),
    # Katecholamine (aus Medication)
    "norepinephrine": ("Medication", ".*", r"(?<!o)Norepinephrin|^Arterenol"),
    "epinephrine": ("Medication", ".*", r"(?<!Nor)Epinephrin|^Suprarenin"),
    "dobutamine": ("Medication", ".*", r"Dobutamin"),
    "milrinone": ("Medication", ".*", r"Milrinone|Corotrop"),
    "vasopressin": ("Medication", ".*", r"Vasopressin|Empressin"),
    # Transfusionen (aus Medication)
    "thromb_t": ("Medication", "Blutersatz", r"^TK"),
    "ery_t": ("Medication", "Blutersatz", r"^EK"),
    "ffp_t": ("Medication", "Blutersatz", r"^FFP"),
    "ppsb_t": ("Medication", ".*", r"Prothromplex|Cofactor"),
    "fib_t": ("Medication", ".*", r"Haemocomplettan"),
    "at3_t": ("Medication", ".*", r"Antithrombin"),
}

def get_day_values(field: str, day: date) -> List[Tuple[float, str]]:
    """
    Holt alle Werte eines Feldes für einen Tag.
    
    Returns:
        Liste von (wert, uhrzeit_string) Tupeln
    """
    if field not in FIELD_TO_SOURCE:
        return []
    
    source_type, category_pattern, param_pattern = FIELD_TO_SOURCE[field]
    
    # Daten laden
    df = get_data(source_type.lower() if source_type != "Impella" else "impella")
    if df.empty:
        return []
    
    # Auf Tag filtern
    if "timestamp" not in df.columns:
        return []
    
    day_df = df[df["timestamp"].dt.date == day]
    if day_df.empty:
        return []
    
    # Parameter-Filter
    param_mask = day_df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
    
    # Category-Filter (optional)
    if "category" in day_df.columns and category_pattern != ".*":
        cat_mask = day_df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
        mask = param_mask & cat_mask
    else:
        mask = param_mask
    
    filtered = day_df[mask]
    if filtered.empty:
        return []
    
    # Werte extrahieren
    results = []
    for _, row in filtered.iterrows():
        try:
            val = float(row["value"])
            time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
            results.append((val, time_str))
        except (ValueError, TypeError):
            continue
    
    # Nach Zeit sortieren
    results.sort(key=lambda x: x[1])
    return results

def render_field_with_hints(
    label: str,
    current_value: Optional[float],
    day_values: List[Tuple[float, str]],
    key_base: str,
    help_text: Optional[str] = None,
    label_visibility: str = "visible"
) -> Optional[float]:
    """
    Rendert ein numerisches Feld mit Dropdown für Tageswerte.
    Die manuelle Eingabe wurde entfernt - es können nur Werte aus den Rohdaten gewählt werden.
    """
    if not day_values:
        # Keine Alternativwerte verfügbar
        st.text_input(
            label,
            value=f"{current_value:.2f}" if current_value is not None else "---",
            disabled=True,
            key=f"{key_base}_disabled",
            help=help_text or "Keine Rohdaten für dieses Feld gefunden",
            label_visibility=label_visibility
        )
        return current_value

    # Dropdown-Optionen erstellen
    options = []
    value_map = {}
    
    # Falls der aktuelle Wert nicht in den Rohdaten ist, fügen wir ihn als "Aktueller Wert" hinzu
    # damit er ausgewählt bleibt, bis der User einen anderen wählt.
    current_val_in_day_values = False
    for val, time_str in day_values:
        if current_value is not None and abs(val - current_value) < 0.001:
            current_val_in_day_values = True
        
        option_label = f"{val:.2f} ({time_str})"
        options.append(option_label)
        value_map[option_label] = val
    
    if current_value is not None and not current_val_in_day_values:
        # Aktuellen Wert an den Anfang stellen
        current_label = f"{current_value:.2f} (Aktuell)"
        options.insert(0, current_label)
        value_map[current_label] = current_value
        current_option = current_label
    else:
        # Aktuellen Wert in den Optionen finden
        current_option = None
        if current_value is not None:
            for opt, opt_val in value_map.items():
                if abs(opt_val - current_value) < 0.001:
                    current_option = opt
                    break
        
        if current_option is None and options:
            current_option = options[0]

    selected_option = st.selectbox(
        label,
        options=options,
        index=options.index(current_option) if current_option in options else 0,
        key=f"{key_base}_select",
        help=help_text or f"{len(day_values)} Werte verfügbar",
        label_visibility=label_visibility
    )
    
    return value_map.get(selected_option)
