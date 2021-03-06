import logging

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.tasks.data import load_yaml


class InterfacesConfiguration:
    """
    Třída pro konfiguraci jednotlivých rozhraní daných zařízení (např: přidělení IPv4, IPv6 adres, popisu,
    konfigurace switchovaných a routovaných portů).
    """

    def configure_ipv4_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci rozhraní (IPv4).

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """

        data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                        severity_level=logging.DEBUG)
        interface_key = "interfaces_ipv4"

        if interface_key in data[0].result:
            task.host[interface_key] = data[0].result[interface_key]

            result = task.run(task=template_file,
                              name="IPv4 Interfaces Configuration",
                              template="interfaces_ipv4.j2",
                              path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

            task.host["ipv4_interfaces"] = result.result

            task.run(task=napalm_configure,
                     name="Loading IPv4 interfaces Configuration on the device",
                     replace=False,
                     configuration=task.host["ipv4_interfaces"],
                     dry_run=dry_run)
        else:
            print(f"{Fore.RED}Device {task.host.name}: No {interface_key} key was found in host data.")

    def configure_ipv6_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci rozhraní (IPv6).

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                        severity_level=logging.DEBUG)
        interface_key = "interfaces_ipv6"
        if interface_key in data[0].result:
            task.host[interface_key] = data[0].result[interface_key]

            r = task.run(task=template_file,
                         name="IPv6 Interfaces Configuration",
                         template="interfaces_ipv6.j2",
                         path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

            task.host["ipv6_interfaces"] = r.result

            task.run(task=napalm_configure,
                     name="Loading IPv6 interfaces Configuration on the device",
                     replace=False,
                     configuration=task.host["ipv6_interfaces"],
                     dry_run=dry_run)
        else:
            print(f"{Fore.RED}Device {task.host.name}: No {interface_key} key was found in host data.")


    def configure_switching_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci přepínacích portů.

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
        if task.host["dev_type"] == "L3_switch" or task.host["dev_type"] == "switch":

            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            switching_interface_key = "switching_interfaces"
            vlans_key = "vlans_config"

            if switching_interface_key in data[0].result and vlans_key in data[0].result:
                task.host[switching_interface_key] = data[0].result[switching_interface_key]
                task.host[vlans_key] = data[0].result[vlans_key]

                interfaces_result = task.run(task=template_file,
                                             name="Switching Interfaces Configuration",
                                             template="switching_interfaces.j2",
                                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

                task.host["switching_interfaces_config"] = interfaces_result.result

                task.run(task=napalm_configure,
                         name="Loading Switching Interfaces Configuration on the device",
                         replace=False,
                         configuration=task.host["switching_interfaces_config"],
                         dry_run=dry_run)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {switching_interface_key} or {vlans_key} key was found in host data.")
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only switches are supported.", task)
