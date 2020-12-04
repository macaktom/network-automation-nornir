from pathlib import Path


class TextFileExporter:
    """
    Třida pro exportování dat do formátu .txt.

    Args:
        full_file_path (Path): argument metody, obsahující cestu k exportovanému .txt souboru.
        data (str): argument metody, obsahující data, která budou exportována do .txt souboru.

    Attributes:
         dest_file_absolute_path (Path): instanční proměnná, definující cestu k exportovanému .txt souboru.
         data (str): instanční proměnná, definující data, která budou exportována do .txt souboru.

    """
    def __init__(self, full_file_path: Path, data: str):
        self.dest_file_absolute_path = full_file_path
        self.data = data
        self._check_full_file_path()

    def _create_parent_folders(self, folder_path: Path) -> None:
        """
        Metoda pro vytvoření všech nadřazených složek k definované instanční proměnné dest_file_absolute_path.
        Složky jsou vytvořeny pouze tehdy, pokud nebyly dříve uživatelem vytvořeny.

        Args:
            folder_path (Path): cesta obsahující všechny nadřazené složky, které jsou nutné pro nalezení výsledného .txt souboru

        Returns:
            None
        """
        folder_path.mkdir(parents=True, exist_ok=True)

    def _check_full_file_path(self) -> None:
        """
        Metoda, která zkontroluje, jestli je k instanční proměnné dest_file_absolute_path přiřazena validní cesta k .txt souboru.
        Dodatečně vytvoří požadované nadřazené složky, pokud už nejsou vytvořené za pomocí metody _create_parent_folders.

        Raises:
            ValueError: Výjimka, která nastane pokud atribut dest_file_absolute_path není validní cestou k .txt souboru.

        Returns:
            None
        """
        if self.dest_file_absolute_path.suffix == ".txt":
            folder_path = self.dest_file_absolute_path.parent
            self._create_parent_folders(folder_path)
        else:
            raise ValueError("Not valid file path.")

    def export_to_file(self) -> None:
        """
        Metoda, která provádí export dat do souboru.

        Returns:
            None
        """
        with open(self.dest_file_absolute_path, 'w') as file:
            file.write(self.data)
            print(f"{self.dest_file_absolute_path.name} was created successfully.")
