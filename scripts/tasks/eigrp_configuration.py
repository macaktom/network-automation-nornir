import logging

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.tasks.data import load_yaml


class EIGRPConfiguration:
    """
    Třída pro konfiguraci EIGRP (IPv4 i IPv6).
    """

    def configure_eigrp_ipv4(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 EIGRP.

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
            task.host["eigrp_config"] = data[0].result["eigrp_config"]

            r = task.run(task=template_file,
                         name="EIGRP IPv4 Template Loading",
                         template="eigrp_ipv4.j2",
                         path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

            task.host["ipv4_eigrp"] = r.result

            task.run(task=napalm_configure,
                     name="Loading EIGRP IPv4 Configuration on the device",
                     replace=False,
                     configuration=task.host["ipv4_eigrp"],
                     dry_run=dry_run)
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only cisco routers and L3 switches are supported.", task)

    def configure_eigrp_ipv6(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 EIGRP.

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
            task.host["eigrp_ipv6_config"] = data[0].result["eigrp_ipv6_config"]

            r = task.run(task=template_file,
                         name="EIGRP IPv6 Template Loading",
                         template="eigrp_ipv6.j2",
                         path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

            task.host["ipv6_eigrp"] = r.result

            task.run(task=napalm_configure,
                     name="Loading EIGRP IPv6 Configuration on the device",
                     replace=False,
                     configuration=task.host["ipv6_eigrp"],
                     dry_run=dry_run)
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only cisco routers and L3 switches are supported.", task)