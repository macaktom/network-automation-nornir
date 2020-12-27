import logging

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.tasks.data import load_yaml


class NATConfiguration:
    """
    Třída pro konfiguraci překládání síťových adres (NAT).
    """

    def configure_source_nat_overload(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci zdrojového NAT Overloadu.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud nastana chyba v nornir úkolu nebo pokud provádíte
                konfiguraci na nepodporovaných zařízeních.

        Returns:
            None
        """

        if task.host["vendor"] == "cisco" and not task.host["dev_type"] == "switch":

            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            task.host["nat_overload_config"] = data[0].result["nat_overload_config"]

            r = task.run(task=template_file,
                         name="NAT Overload Configuration",
                         template="source_nat_overload.j2",
                         path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                         nat_overload_config=task.host["nat_overload_config"])

            task.host["nat_overload"] = r.result

            task.run(task=napalm_configure,
                     name="Loading NAT Overload Configuration on the device",
                     replace=False,
                     configuration=task.host["nat_overload"],
                     dry_run=dry_run)
        else:
            print(f"{Fore.RED} Device {task.host.name}: method is not implemented.")
            raise NornirSubTaskError("Invalid device type or vendor. Method is not implemented for particular device/vendor.", task)
