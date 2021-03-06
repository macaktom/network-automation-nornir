import logging
from pathlib import Path

from colorama import Fore
from nornir import InitNornir
from nornir.core import Task, Nornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result
from nornir_utils.plugins.tasks.data import load_yaml

from modules.utility.credential_handler import CredentialHandler


class RestoreConfiguration:
    """
    Třída umožňující nahradit konfiguraci za úplně novou konfigurací (např. při obnovení zálohované konfigurace).
    """

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


    def _get_data_from_file(self, file_path: Path) -> str:
        """

        Args:
            file_path (Path): cesta k souboru, ze kterého se přečtou data

        Returns:
            Vrací obsah souboru ve stringu.
        """
        with open(file_path, 'r') as reader:
            return reader.read()

    def restore_running_configuration(self, task: Task, dry_run: bool = False):
        """
        Metoda pro paralelní nahrazení stávající running konfigurace za již dříve zálohovanou running konfiguraci.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        try:
            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data", severity_level=logging.DEBUG)
            date = data[0].result["restore_config"]["running_config_date"]
            file_path = Path(Path.cwd() / 'backups' / f"{task.host.name}" / f"{task.host.name}_{str(date)}.conf")
            task.host["restore_running_conf"] = self._get_data_from_file(file_path)
            task.run(task=napalm_configure,
                     name="Loading Running Configuration on the device",
                     replace=True,
                     configuration=task.host["restore_running_conf"],
                     dry_run=dry_run)
        except KeyError as err:
            print(
                f"{Fore.RED}Device {task.host.name} was not restored - key (restore_config or running_config_date) is not "
                f"defined in host inventory for that device.")
        except FileNotFoundError as err:
            print(
                f"{Fore.RED}Device {task.host.name} was not restored - specified .conf file was not found.")
        except Exception as err:
            print(f"{Fore.RED}Device {task.host.name} was not restored - check nornir.log")


if __name__ == '__main__':
    restore_conf = RestoreConfiguration()
    nr = restore_conf.setup_inventory()
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch") | F(dev_type="switch"))
    res = all_devices.run(restore_conf.restore_running_configuration, name="Restore backed up configuration",dry_run=True)
    print_result(res)
