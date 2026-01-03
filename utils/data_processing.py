"""
Gemeinsame Datenverarbeitungsfunktionen für Explorer und Export Builder.
"""

import pandas as pd
from typing import Tuple


def filter_outliers(df: pd.DataFrame, lower_pct: float = 2.5, upper_pct: float = 97.5) -> Tuple[pd.DataFrame, int]:
    """
    Filtert Ausreißer basierend auf Perzentilen pro Parameter.
    
    Args:
        df: DataFrame mit Daten (muss "value"-Spalte enthalten)
        lower_pct: Unteres Perzentil (Standard: 2.5%)
        upper_pct: Oberes Perzentil (Standard: 97.5%)
    
    Returns:
        Tuple (gefilterter DataFrame, Anzahl entfernter Ausreißer)
    """
    if df.empty or "value" not in df.columns:
        return df, 0
    
    df_work = df.copy()
    df_work["_value_numeric"] = pd.to_numeric(df_work["value"], errors="coerce")
    
    original_count = len(df_work)
    
    # Erstelle Maske für zu behaltende Zeilen
    keep_mask = pd.Series(True, index=df_work.index)
    
    # Pro Parameter filtern (falls vorhanden)
    if "parameter" in df_work.columns:
        for param in df_work["parameter"].dropna().unique():
            param_mask = df_work["parameter"] == param
            param_values = df_work.loc[param_mask, "_value_numeric"].dropna()
            
            if len(param_values) < 5:  # Zu wenige Werte für sinnvolle Perzentile
                continue
            
            lower = param_values.quantile(lower_pct / 100)
            upper = param_values.quantile(upper_pct / 100)
            
            # Numerische Werte außerhalb des Bereichs markieren
            numeric_mask = param_mask & df_work["_value_numeric"].notna()
            out_of_range = numeric_mask & (
                (df_work["_value_numeric"] < lower) | (df_work["_value_numeric"] > upper)
            )
            keep_mask = keep_mask & ~out_of_range
    else:
        # Ohne Parameter: globale Perzentile
        numeric_vals = df_work["_value_numeric"].dropna()
        if len(numeric_vals) >= 5:
            lower = numeric_vals.quantile(lower_pct / 100)
            upper = numeric_vals.quantile(upper_pct / 100)
            
            numeric_mask = df_work["_value_numeric"].notna()
            out_of_range = numeric_mask & (
                (df_work["_value_numeric"] < lower) | (df_work["_value_numeric"] > upper)
            )
            keep_mask = keep_mask & ~out_of_range
    
    df_filtered = df[keep_mask].copy()
    outlier_count = original_count - len(df_filtered)
    
    return df_filtered, outlier_count
