from pathlib import Path

from colorama import Fore
from nornir import InitNornir
from nornir.core import Task
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result


class RestoreConfiguration:
    """
    Třída umožňující nahradit konfiguraci za úplně novou konfigurací (např. při obnovení zálohované konfigurace).
    """

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
            date = task.host["restore_config"]["running_config_date"]
            file_path = Path(Path.cwd() / 'backups' / "running_configuration" / f"{task.host.name}" / f"{task.host.name}_{str(date)}.txt")
            task.host["restore_running_conf"] = self._get_data_from_file(file_path)
            task.run(task=napalm_configure,
                     name="Loading Running Configuration on the device",
                     replace=True,
                     configuration=task.host["restore_running_conf"],
                     dry_run=dry_run)
        except KeyError as err:
            print(f"{Fore.RED}Device {task.host.name} was not restored - key (restore_config or running_config_date) is not "
                  f"defined in config.yml for particular device.")
        except Exception as err:
            print(f"{Fore.RED}Device {task.host.name} was not restored - check nornir.log")


if __name__ == '__main__':
    restore_conf = RestoreConfiguration()
    nr = InitNornir(config_file="config.yml")
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch") | F(dev_type="switch"))
    res = all_devices.run(restore_conf.restore_running_configuration, name="Restore backed up configuration",
                          dry_run=False)
    print_result(res)
