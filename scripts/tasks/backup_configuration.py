from datetime import datetime, date
from pathlib import Path

from colorama import Fore
from nornir import InitNornir
from nornir.core import Nornir, Task
from nornir.core.filter import F
from nornir_utils.plugins.tasks.files import write_file
from scripts.utility.network_info_collector import NetworkInfoCollector


class BackupConfiguration:
    """
    Třida určená pro pravidelný backup konfigurace síťových zařízení (využití pro automatický backup pomocí nástroje cron).

    Args:
        collector (NetworkInfoCollector): objekt určený pro paralelní sbírání dat ze síťových zařízení.

    Attributes:
        network_info_Collector (NetworkInfoCollector): objekt určený pro paralelní sbírání dat ze síťových zařízení.
        date (datetime.date): datum provedení backupu
        folder_path (Path): statická proměnná, která obsahuje společnou cestu pro všechny backupy (zbytek cesty je určen typem backupu a daným hostem).

    """
    folder_path = Path(Path.cwd() / 'backups')

    def __init__(self, collector: NetworkInfoCollector):
        self._network_info_collector = collector
        self._date = datetime.now().date()

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
            print(f"{Fore.RED}Error: Creating directories for specified path {folder_path} failed.")

    def backup_device_running_configuration(self, task: Task) -> None:
        """
        Metoda, která slouží k paralelnímu backupu running (současné) konfigurace daných zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            None
        """
        result = self._network_info_collector.get_device_configuration(task)
        if not result.failed:
            running_configuration = result[0].result["config"]['running'].strip()
            file_path = BackupConfiguration.folder_path / "running_configuration" / f"{task.host.name}" / f"{task.host.name}_{str(self._date)}.txt"
            self._create_parent_folders(file_path.parent)
            res = task.run(write_file, filename=str(file_path), content=running_configuration, append=False)
            if not res.failed:
                print(f"Backup of running configuration was successful for host {task.host.name}.")
            else:
                print(f"{Fore.RED}Backup of running configuration failed for host {task.host.name} - more info in nornir.log")
        else:
            print(f"{Fore.RED}Backup of running configuration failed for host {task.host.name} - more info in nornir.log")


if __name__ == '__main__':
    nr = InitNornir(config_file="config.yml")
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch") | F(dev_type="switch"))
    backup_configuration = BackupConfiguration(NetworkInfoCollector())
    all_devices.run(backup_configuration.backup_device_running_configuration, name="Backup running configuration")
