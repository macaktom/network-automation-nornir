from os import path
from pathlib import Path


class TextFileExporter:
    def __init__(self, full_file_path: Path):
        self.dest_file_absolute_path = full_file_path

    def _create_parent_folders(self, folder_path: Path) -> None:
        folder_path.mkdir(parents=True, exist_ok=True)

    def _check_full_file_patch(self) -> None:
        if path.isfile and self.dest_file_absolute_path.suffix == ".txt":
            folder_path = self.dest_file_absolute_path.parent
            self._create_parent_folders(folder_path)
        else:
            raise ValueError("Not valid file path.")

    def export_to_file(self, data: str) -> None:
        if path.isfile:
            folder_path = self.dest_file_absolute_path.parent
            folder_path.mkdir(parents=True, exist_ok=True)
            with open(self.dest_file_absolute_path, 'w') as file:
                file.write(data)
                print(f"{self.dest_file_absolute_path.name} was created successfully.")
        else:
            print("Provided filepath is not valid.")
