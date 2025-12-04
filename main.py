import flet as ft
import os
from mlife_core.services.pipeline import run_parsing_pipeline
from ui.app_state import AppState
from ui.tabs.overview import OverviewTab
from ui.tabs.quick_export import QuickExportTab
from ui.tabs.custom_export import CustomExportTab

def main(page: ft.Page):
    # --- Grundeinstellungen der Seite ---
    page.title = "Medical Data Pipeline & Export"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.height = 900
    page.window.width = 1200

    # --- App State ---
    app_state = AppState()

    # --- UI Komponenten ---

    # 1. Header & Datei-Auswahl
    header_text = ft.Text("Medical Data Parser", size=30, weight=ft.FontWeight.BOLD)
    status_text = ft.Text("Bitte wähle eine CSV-Datei aus.", color=ft.Colors.GREY_700)
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
    selected_file_text = ft.Text("Keine Datei ausgewählt", italic=True)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            app_state.filepath = path
            selected_file_text.value = f"Datei: {os.path.basename(path)}"
            process_btn.disabled = False
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    select_file_btn = ft.ElevatedButton(
        "Datei auswählen",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["csv", "txt"])
    )

    # Tabs initialisieren
    overview_tab = OverviewTab(app_state)
    quick_export_tab = QuickExportTab(page, app_state)
    custom_export_tab = CustomExportTab(page, app_state)

    tabs_control = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        visible=False,
        tabs=[
            ft.Tab(
                text="Übersicht",
                icon=ft.Icons.DASHBOARD,
                content=overview_tab
            ),
            ft.Tab(
                text="Quick Export",
                icon=ft.Icons.FLASH_ON,
                content=quick_export_tab
            ),
            ft.Tab(
                text="Custom Export",
                icon=ft.Icons.BUILD,
                content=custom_export_tab
            ),
        ],
        expand=True
    )

    # 2. Pipeline Ausführung
    def run_pipeline_click(e):
        if not app_state.filepath:
            return
        
        # UI auf "Laden" setzen
        process_btn.disabled = True
        select_file_btn.disabled = True
        progress_ring.visible = True
        status_text.value = "Pipeline läuft... Daten werden verarbeitet."
        status_text.color = ft.Colors.BLUE
        page.update()

        try:
            # Pipeline ausführen
            df = run_parsing_pipeline(app_state.filepath)
            app_state.df = df
            
            # Erfolgsfall
            status_text.value = f"Erfolg! {len(df)} Datenpunkte geladen."
            status_text.color = ft.Colors.GREEN
            
            # Tabs aktivieren und Daten laden
            tabs_control.visible = True
            overview_tab.update_data()
            custom_export_tab.update_filter_options()
            
        except Exception as ex:
            # Fehlerfall
            status_text.value = f"Fehler: {str(ex)}"
            status_text.color = ft.Colors.RED
            import traceback
            traceback.print_exc()
        
        # UI zurücksetzen
        progress_ring.visible = False
        process_btn.disabled = False
        select_file_btn.disabled = False
        page.update()

    process_btn = ft.ElevatedButton(
        "Daten verarbeiten",
        icon=ft.Icons.PLAY_ARROW,
        on_click=run_pipeline_click,
        disabled=True
    )

    # Haupt-Layout der Seite
    page.add(
        ft.Column([
            # Header Bereich
            ft.Row([header_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            
            # Control Bereich (Datei & Run)
            ft.Row([
                select_file_btn,
                selected_file_text,
                ft.VerticalDivider(width=20),
                process_btn,
                progress_ring
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            
            # Hauptinhalt (Tabs)
            tabs_control
            
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)