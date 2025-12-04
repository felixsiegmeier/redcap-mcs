import pandas as pd
from mlife_core.services.parsers import DataParser

def run_parsing_pipeline(input_file: str) -> pd.DataFrame:
    """
    Runs the complete parsing pipeline:
    1. Parses all data sections (Vitals, Lab, Devices, Meds, etc.)
    2. Consolidates standard data into Long Format
    3. Integrates Medication data
    4. Returns the final sorted DataFrame
    """
    
    # Initialize Parser
    data_parser = DataParser(input_file, delimiter=";")
    
    # Container for all dataframes
    dfs = []
    
    # 1. Vitals
    print("Parsing Vitals...")
    vitals = data_parser.parse_vitals()
    if not vitals.empty:
        vitals['source_type'] = 'Vitals'
        dfs.append(vitals)
        
    # 2. Lab
    print("Parsing Lab...")
    lab = data_parser.parse_lab()
    if not lab.empty:
        lab['source_type'] = 'Lab'
        dfs.append(lab)
        
    # 3. Respiratory
    print("Parsing Respiratory...")
    respiratory = data_parser.parse_respiratory_data()
    if not respiratory.empty:
        respiratory['source_type'] = 'Respiratory'
        dfs.append(respiratory)
        
    # 4. All Patient Data (Devices, Scores, Misc)
    print("Parsing All Patient Data (Devices, Scores, etc.)...")
    all_patient_data = data_parser.parse_complete_all_patient_data()
    if not all_patient_data.empty:
        # Wir nutzen 'source_header' als 'source_type', falls noch nicht vorhanden,
        # oder mappen es explizit. Hier übernehmen wir einfach den Header als Typ.
        # Da die Spalte 'source_header' bereits existiert, können wir sie direkt nutzen.
        # Um konsistent mit dem Schema zu sein, kopieren wir source_header nach source_type.
        all_patient_data['source_type'] = all_patient_data['source_header']
        dfs.append(all_patient_data)
        
    # 5. Fluid Balance
    print("Parsing Fluid Balance...")
    fluid = data_parser.parse_fluidbalance_logic()
    if not fluid.empty:
        fluid['source_type'] = 'FluidBalance'
        dfs.append(fluid)
        
    # 6. Medication
    print("Parsing Medication...")
    meds = data_parser.parse_medication_logic()
    if not meds.empty:
        meds['source_type'] = 'Medication'
        dfs.append(meds)
    
    # 7. Patient Info (Static)
    print("Parsing Patient Info...")
    pat_info = data_parser.parse_patient_info()
    if not pat_info.empty:
        dfs.append(pat_info)
    
    if not dfs:
        return pd.DataFrame()

    # Concatenate all (Long Format)
    print("Consolidating data (Long Format)...")
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Ensure timestamp is datetime
    full_df['timestamp'] = pd.to_datetime(full_df['timestamp'], errors='coerce')
    full_df = full_df.dropna(subset=['timestamp'])
    
    # Sort by timestamp
    full_df = full_df.sort_values('timestamp')
    
    # Reorder columns
    cols = full_df.columns.tolist()
    priority_cols = ['timestamp', 'source_type', 'category', 'parameter', 'value']
    other_cols = [c for c in cols if c not in priority_cols]
    
    final_cols = priority_cols + other_cols
    final_cols = [c for c in final_cols if c in full_df.columns]
    
    return full_df[final_cols]
