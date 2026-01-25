from datetime import date, time
from pathlib import Path
from typing import Optional
import re

import pandas as pd
import pytest

from services.aggregators import (
    HemodynamicsAggregator,
    ImpellaAggregator,
    LabAggregator,
    PumpAggregator,
)


TEST_DATE = date(2026, 1, 2)
RECORD_ID = "test-001"
EVENT_NAME = "ecls_arm_2"
INSTANCE = 1
NEAREST_TIME = time(7, 0)


@pytest.fixture(scope="session")
def full_export_df() -> pd.DataFrame:
    data_path = Path(__file__).resolve().parents[1] / "full_export.csv"
    df = pd.read_csv(data_path, sep=";", low_memory=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def _median_value(
    df: pd.DataFrame,
    target_date: date,
    source: str,
    category_pattern: str,
    parameter_pattern: str,
) -> Optional[float]:
    day_df = df[df["timestamp"].dt.date == target_date]
    source_df = day_df[day_df["source_type"].str.contains(source, case=False, na=False)]
    if source_df.empty:
        return None

    param_mask = source_df["parameter"].str.contains(
        parameter_pattern, case=False, na=False, regex=True
    )
    if "category" in source_df.columns and category_pattern != ".*":
        cat_mask = source_df["category"].str.contains(
            category_pattern, case=False, na=False, regex=True
        )
        mask = param_mask & cat_mask
    else:
        mask = param_mask

    values = pd.to_numeric(source_df.loc[mask, "value"], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.median())


def _first_p_level(df: pd.DataFrame, target_date: date) -> Optional[int]:
    day_df = df[df["timestamp"].dt.date == target_date]
    imp_df = day_df[day_df["source_type"].str.contains("Impella", case=False, na=False)]
    mask = imp_df["parameter"].str.contains(
        r"Flu.*regelung|Fluss.*regelung", case=False, na=False, regex=True
    )
    for value in imp_df.loc[mask, "value"]:
        if pd.isna(value):
            continue
        match = re.search(r"P(\d+)", str(value), re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _has_source(df: pd.DataFrame, target_date: date, source: str) -> bool:
    day_df = df[df["timestamp"].dt.date == target_date]
    return not day_df[day_df["source_type"].str.contains(source, case=False, na=False)].empty


def test_lab_aggregator_full_export(full_export_df: pd.DataFrame) -> None:
    expected_ecmella = 1 if (
        _has_source(full_export_df, TEST_DATE, "ECMO")
        and _has_source(full_export_df, TEST_DATE, "Impella")
    ) else 0

    aggregator = LabAggregator(
        date=TEST_DATE,
        record_id=RECORD_ID,
        redcap_event_name=EVENT_NAME,
        redcap_repeat_instrument="labor",
        redcap_repeat_instance=INSTANCE,
        value_strategy="median",
        nearest_time=NEAREST_TIME,
        data=full_export_df,
    )
    entry = aggregator.create_entry()

    expected_p02 = _median_value(
        full_export_df, TEST_DATE, "Lab", "Blutgase arteriell", r"^PO2"
    )
    expected_ph = _median_value(
        full_export_df, TEST_DATE, "Lab", "Blutgase arteriell", r"^PH$|^PH "
    )
    expected_lactate = _median_value(
        full_export_df, TEST_DATE, "Lab", "Blutgase arteriell", r"^LACTAT"
    )
    expected_hb = _median_value(
        full_export_df, TEST_DATE, "Lab", "Blutbild", r"^HB \(HGB\)|^HB\b"
    )
    expected_act = _median_value(full_export_df, TEST_DATE, "ACT", ".*", r"^ACT")

    assert entry.assess_date_labor == TEST_DATE
    assert entry.time_assess_labor == NEAREST_TIME
    assert entry.ecmella_2 == expected_ecmella

    assert expected_p02 is not None
    assert expected_ph is not None
    assert expected_lactate is not None
    assert expected_hb is not None
    assert expected_act is not None

    assert entry.p02 == pytest.approx(expected_p02)
    assert entry.ph == pytest.approx(expected_ph)
    assert entry.lactate == pytest.approx(expected_lactate)
    assert entry.hb == pytest.approx(expected_hb)
    assert entry.act == pytest.approx(expected_act)


def test_hemodynamics_aggregator_full_export(full_export_df: pd.DataFrame) -> None:
    expected_ecmella = 1 if (
        _has_source(full_export_df, TEST_DATE, "ECMO")
        and _has_source(full_export_df, TEST_DATE, "Impella")
    ) else 0

    aggregator = HemodynamicsAggregator(
        date=TEST_DATE,
        record_id=RECORD_ID,
        redcap_event_name=EVENT_NAME,
        redcap_repeat_instance=INSTANCE,
        value_strategy="median",
        data=full_export_df,
    )
    entry = aggregator.create_entry()

    expected_hr = _median_value(
        full_export_df, TEST_DATE, "Vitals", ".*", r"^HF\s*\["
    )
    expected_sys_bp = _median_value(
        full_export_df, TEST_DATE, "Vitals", ".*", r"^ABPs\s*\[|^ARTs\s*\["
    )
    expected_fio2 = _median_value(
        full_export_df, TEST_DATE, "Respiratory", ".*", r"^FiO2\s*\[%\]"
    )

    assert entry.assess_date_hemo == TEST_DATE
    assert entry.ecmella == expected_ecmella

    assert expected_hr is not None
    assert expected_sys_bp is not None
    assert expected_fio2 is not None

    assert entry.hr == pytest.approx(expected_hr)
    assert entry.sys_bp == pytest.approx(expected_sys_bp)
    assert entry.fio2 == pytest.approx(expected_fio2)


def test_pump_aggregator_full_export(full_export_df: pd.DataFrame) -> None:
    aggregator = PumpAggregator(
        date=TEST_DATE,
        record_id=RECORD_ID,
        redcap_repeat_instance=INSTANCE,
        value_strategy="median",
        data=full_export_df,
    )
    entry = aggregator.create_entry()

    expected_rpm = _median_value(
        full_export_df, TEST_DATE, "ECMO", ".*", r"^Drehzahl"
    )
    expected_pf = _median_value(
        full_export_df, TEST_DATE, "ECMO", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min"
    )
    expected_gf = _median_value(
        full_export_df, TEST_DATE, "ECMO", ".*", r"^Gasfluss"
    )
    expected_fi02 = _median_value(
        full_export_df, TEST_DATE, "ECMO", ".*", r"^FiO2"
    )

    assert entry.ecls_compl_date == TEST_DATE

    assert expected_rpm is not None
    assert expected_pf is not None
    assert expected_gf is not None
    assert expected_fi02 is not None

    assert entry.ecls_rpm == pytest.approx(expected_rpm)
    assert entry.ecls_pf == pytest.approx(expected_pf)
    assert entry.ecls_gf == pytest.approx(expected_gf)
    assert entry.ecls_fi02 == pytest.approx(expected_fi02)


def test_impella_aggregator_full_export(full_export_df: pd.DataFrame) -> None:
    aggregator = ImpellaAggregator(
        date=TEST_DATE,
        record_id=RECORD_ID,
        redcap_repeat_instance=INSTANCE,
        value_strategy="median",
        data=full_export_df,
    )
    entry = aggregator.create_entry()

    expected_flow = _median_value(
        full_export_df, TEST_DATE, "Impella", ".*", r"^HZV"
    )
    expected_purge_flow = _median_value(
        full_export_df,
        TEST_DATE,
        "Impella",
        ".*",
        r"Purge.*ml/h",
    )
    expected_purge_pressure = _median_value(
        full_export_df, TEST_DATE, "Impella", ".*", r"Purgedruck"
    )
    expected_p_level = _first_p_level(full_export_df, TEST_DATE)

    assert entry.imp_compl_date == TEST_DATE

    assert expected_flow is not None
    assert expected_purge_flow is not None
    assert expected_purge_pressure is not None
    assert expected_p_level is not None

    assert entry.imp_flow == pytest.approx(expected_flow)
    assert entry.imp_purge_flow == pytest.approx(expected_purge_flow)
    assert entry.imp_purge_pressure == pytest.approx(expected_purge_pressure)
    assert entry.imp_p_level == expected_p_level
