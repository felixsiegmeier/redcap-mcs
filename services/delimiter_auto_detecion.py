def detect_delimiter(text: str) -> str | None:
    """
    Ermittelt den Delimiter einer CSV-Datei basierend auf der Häufigkeit von ';' und '|'.
    Gibt den Delimiter zurück, wenn er mehr als 20 Mal vorkommt und häufiger als der andere ist.
    Bei Gleichheit oder weniger als 21 Vorkommen gibt None zurück.
    """
    count_semicolon = text.count(';')
    count_pipe = text.count('|')
    
    if count_semicolon > count_pipe:
        delimiter = ";"
        count = count_semicolon
    elif count_pipe > count_semicolon:
        delimiter = "|"
        count = count_pipe
    else:
        return None  # Gleichheit
    
    if count > 20:
        return delimiter
    else:
        return None
