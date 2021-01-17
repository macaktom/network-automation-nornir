from datetime import datetime, date
from pathlib import Path

from colorama import Fore
from nornir import InitNornir
from nornir.core import Nornir, Task
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.tasks.files import write_file

from scripts.utility.credential_handler import CredentialHandler


class BackupConfiguration:
    """
    Třida určená pro pravidelný backup konfigurace síťových zařízení (využití pro automatický backup např. pomocí nástroje cron).

    Attributes:
        date (datetime.date): datum provedení backupu

    """

    def __init__(self):
        self._date = datetime.now().date()

    def setup_inventory(self) -> Nornir:
        """
        Funkce, která umožňuje načíst veškeré informace o hostech a využívaných skupinách (groups). Podporuje dynamické načítání citlivých údajů (pouze pro citlivé údaje skupin).

        Returns:
            Nornir - nornir objekt, který obsahuje zparsované informace o hostech, skupinách. Dále zajišťuje multithreading funkcionalitu.
        """
        creds_handler = CredentialHandler()
        nr = InitNornir(config_file="config.yml")  # Nornir objekt, který přeskočí hosty, které nezvládli požadovaný (sub)task - více o chybě v nornir.log
        creds_handler.insert_creds(nr)
        return nr

    def _create_parent_folders(self, folder_path: Path) -> None:
        """
        Metoda pro vytvoření všech nadřazených složek k definované instanční proměnné dest_file.
        Složky jsou vytvořeny pouze tehdy, pokud nebyly dříve uživatelem vytvořeny.

        Args:
            folder_path (Path): cesta obsahující všechny nadřazené složky, které jsou nutné pro nalezení výsledného .conf souboru

        Returns:
            None
        """
        folder_path.mkdir(parents=True, exist_ok=True)

    def backup_device_running_configuration(self, task: Task) -> None:
        """
        Metoda, která slouží k paralelnímu backupu running (současné) konfigurace daných zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Get configuration", getters=["config"])
        if not result.failed:
            running_configuration = result[0].result["config"]['running'].strip()
            file_path = Path(Path.cwd() / 'backups' / f"{task.host.name}" / f"{task.host.name}_{str(self._date)}.conf")
            self._create_parent_folders(file_path.parent)
            res = task.run(write_file, filename=str(file_path), content=running_configuration, append=False)
            if not res.failed:
                print(f"Backup {file_path.name} of running configuration was successful for host {task.host.name}.")
            else:
                print(f"{Fore.RED}Backup of running configuration failed for host {task.host.name} - more info in nornir.log")
        else:
            print(f"{Fore.RED}Backup of running configuration failed for host {task.host.name} - more info in nornir.log")


if __name__ == '__main__':
    backup_configuration = BackupConfiguration()
    nr = backup_configuration.setup_inventory()
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch") | F(dev_type="switch"))
    all_devices.run(backup_configuration.backup_device_running_configuration, name="Backup running configuration")
