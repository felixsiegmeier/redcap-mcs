import pandas as pd

class AppState:
    def __init__(self):
        self.df: pd.DataFrame = None
        self.filepath: str = None
        self.custom_export = {
            "standard_categories": set(),
            "other_sources": set()
        }
        # Temporary storage for export operations
        self.export_df: pd.DataFrame = None
