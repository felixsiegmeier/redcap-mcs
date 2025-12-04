import flet as ft
from ui.app_state import AppState

class OverviewTab(ft.Container):
    def __init__(self, app_state: AppState):
        super().__init__(padding=20)
        self.app_state = app_state
        self.content_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.content = self.content_col
    
    def update_data(self):
        df = self.app_state.df
        if df is None: return
        
        # Statistiken berechnen
        total_rows = len(df)
        sources = df['source_type'].unique()
        categories = df['category'].nunique()
        parameters = df['parameter'].nunique()
        
        # Inhalt neu bauen
        self.content_col.controls = [
            ft.Text("Datensatz Zusammenfassung", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                self.stat_card("Zeilen", str(total_rows), ft.Icons.LIST),
                self.stat_card("Quellen", str(len(sources)), ft.Icons.SOURCE),
                self.stat_card("Parameter", str(parameters), ft.Icons.ANALYTICS),
            ]),
            ft.Divider(),
            ft.Text("Gefundene Quell-Typen:", weight=ft.FontWeight.BOLD),
            ft.Text(", ".join([str(s) for s in sources])),
        ]
        self.update()

    def stat_card(self, title, value, icon):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=30, color=ft.Colors.BLUE),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(title, size=14, color=ft.Colors.GREY)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            width=150
        )
