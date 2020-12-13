from pathlib import Path


class TextFileExporter:
    """
    Třida pro exportování dat do formátu .txt.

    Args:
        file_path (Path): argument metody, obsahující cestu k exportovanému .txt souboru.
        content (str): argument metody, obsahující data, která budou exportována do .txt souboru.

    Attributes:
         dest_file (Path): instanční proměnná, definující cestu k exportovanému .txt souboru.
         content (str): instanční proměnná, definující data, která budou exportována do .txt souboru.

    """
    def __init__(self, file_path: Path, content: str):
        self._dest_file = file_path
        self._content = content
        self._check_full_file_path()

    def _create_parent_folders(self, folder_path: Path) -> None:
        """
        Metoda pro vytvoření všech nadřazených složek k definované instanční proměnné dest_file.
        Složky jsou vytvořeny pouze tehdy, pokud nebyly dříve uživatelem vytvořeny.

        Args:
            folder_path (Path): cesta obsahující všechny nadřazené složky, které jsou nutné pro nalezení výsledného .txt souboru

        Raises:
            OSError: Výjimka, která nastane pokud došlo k chybě při vytváření složek z definované cesty folder_path.

        Returns:
            None
        """
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except OSError:
            print(f"Error: Creating directories for specified path {folder_path} failed.")

    def _check_full_file_path(self) -> None:
        """
        Metoda, která zkontroluje, jestli je k instanční proměnné dest_file přiřazena validní cesta k .txt souboru.
        Dodatečně vytvoří požadované nadřazené složky, pokud už nejsou vytvořené za pomocí metody _create_parent_folders.

        Raises:
            ValueError: Výjimka, která nastane pokud atribut dest_file není validní cestou k .txt souboru.

        Returns:
            None
        """
        if self._dest_file.suffix == ".txt":
            folder_path = self._dest_file.parent
            self._create_parent_folders(folder_path)
        else:
            raise ValueError("Not valid file path.")

    def export_to_file(self, append: bool = False) -> None:
        """
        Metoda, která provádí export dat do souboru.

        Args:
            append (bool): argument, který rozlišuje, jestli se mají data přidávat na konec existujícího souboru (True) nebo se má vytvořit zcela nový soubor (False).
                           Defaultně nastaveno jako False (vytvoření nového souboru).

        Returns:
            None
        """
        mode = "a" if append else "w"
        with open(self._dest_file, mode) as file:
            file.write(self._content)
            print(f"{self._dest_file.name} was exported successfully.")
