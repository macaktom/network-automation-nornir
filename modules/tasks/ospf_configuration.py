import logging

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result
from nornir_utils.plugins.tasks.data import load_yaml


class OSPFConfiguration:
    """
    Třída pro konfiguraci OSPF a OSPFv3.
    """

    def configure_ospf(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci OSPFv2.

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

        if not task.host["dev_type"] == "switch":
            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)

            ospf_key = "ospf_config"

            if ospf_key in data[0].result:
                task.host[ospf_key] = data[0].result[ospf_key]

                r = task.run(task=template_file,
                             name="OSPF Template Loading",
                             template="ospf_ipv4.j2",
                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

                task.host["ipv4_ospf"] = r.result

                task.run(task=napalm_configure,
                         name="Loading OSPFv2 Configuration on the device",
                         replace=False,
                         configuration=task.host["ipv4_ospf"],
                         dry_run=dry_run)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {ospf_key} key was found in host data.")
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only routers and L3_switches are supported.", task)


    def configure_ospfv3(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci OSPFv3.

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

        if task.host["dev_type"] == "router":

            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            ospfv3_key = "ospfv3_config"

            if ospfv3_key in data[0].result:
                task.host[ospfv3_key] = data[0].result[ospfv3_key]

                r = task.run(task=template_file,
                             name="OSPF Template Loading",
                             template="ospfv3.j2",
                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

                task.host["ipv6_ospf"] = r.result

                task.run(task=napalm_configure,
                         name="Loading OSPFv3 Configuration on the device",
                         replace=False,
                         configuration=task.host["ipv6_ospf"],
                         dry_run=dry_run)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {ospfv3_key} key was found in host data.")
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only routers are supported.", task)
