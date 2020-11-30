from pathlib import Path
from typing import List, Dict

from nornir.core.task import AggregatedResult, Result, Task
from nornir_napalm.plugins.tasks import napalm_get
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from os import path
import datetime


class ExcelExporter:

    def __init__(self, workbook: Workbook, sheet_title: str, dest_file: Path):
        self._workbook = workbook
        self._dest_file = dest_file
        self._setup_export(sheet_title)

    def _create_parent_folders(self, folder_path: Path) -> None:
        folder_path.mkdir(parents=True, exist_ok=True)

    def _check_file_dest(self) -> None:
        if path.isfile and self._dest_file.suffix == '.xlsx':
            self._create_parent_folders(self._dest_file.parent)
        else:
            raise ValueError("Not valid filepath or extension")

    def _write_data(self, lst_data: List[Dict[str, str]], sorted_headers: List[str], row_start: int, column_start: int) -> None:
        current_column = column_start
        for host_data in lst_data:
            row_start += 1
            for header in sorted_headers:
                if host_data[header] is None or host_data[header] == "None" or host_data[header] == "":
                    self.ws1.cell(row=row_start, column=current_column).value = "-"
                else:
                    self.ws1.cell(row=row_start, column=current_column).value = host_data[header]
                self.ws1.cell(row=row_start, column=current_column).alignment = Alignment(horizontal='center',
                                                                                          vertical='center')
                current_column += 1
            current_column = column_start

    def _write_header(self, headers: List[str], row_start: int, column_start: int) -> None:
        for header in headers:
            self.ws1.cell(row=row_start, column=column_start).value = header
            self.ws1.cell(row=row_start, column=column_start).alignment = Alignment(horizontal='center',
                                                                                    vertical='center')
            if header.lower() == "os_version" or header.lower() == "fqdn":
                self.ws1.column_dimensions[get_column_letter(column_start)].width = 40
            else:
                self.ws1.column_dimensions[get_column_letter(column_start)].width = 15
            column_start += 1

    def export_to_xlsx(self, sorted_headers: List[str], data: List[Dict[str, str]], row_start: int = 2,
                       column_start: int = 2) -> None:
        if row_start > 0 and column_start > 0:
            self._write_header(sorted_headers, row_start, column_start)
            self._write_data(data, sorted_headers, row_start, column_start)
            self._workbook.save(self._dest_file)
        else:
            print("Data were not exported - check specified row_start and column_start (both must be > 0).")

    def _setup_export(self, sheet_title: str) -> None:
        self._check_file_dest()
        self.ws1 = self._workbook.active
        self.ws1.title = sheet_title
