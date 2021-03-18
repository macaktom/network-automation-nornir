import logging

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.tasks.data import load_yaml


class PacketFilterConfiguration:
    """
    Třída pro konfiguraci paketových filtrů.
    """

    def configure_ipv4_packet_filters(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 paketového filtru.

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

            packet_filter_key = "packet_filter_config"

            if packet_filter_key in data[0].result:
                task.host[packet_filter_key] = data[0].result[packet_filter_key]

                r = task.run(task=template_file,
                             name="IPv4 Packet filter Configuration",
                             template="packet_filter_ipv4.j2",
                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

                task.host["ipv4_packet_filter"] = r.result

                task.run(task=napalm_configure,
                         name="Loading IPv4 Packet Filter Configuration on the device",
                         replace=False,
                         configuration=task.host["ipv4_packet_filter"],
                         dry_run=dry_run)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {packet_filter_key} key was found in host data.")
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only routers and L3_devices are supported.", task)

    def configure_ipv6_packet_filters(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 paketového filtru.

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
            packet_filter_key = "packet_filter_ipv6_config"

            if packet_filter_key in data[0].result:
                task.host[packet_filter_key] = data[0].result[packet_filter_key]

                r = task.run(task=template_file,
                             name="IPv6 Packet filter Configuration",
                             template="packet_filter_ipv6.j2",
                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}")

                task.host["ipv6_packet_filter"] = r.result

                task.run(task=napalm_configure,
                         name="Loading IPv6 Packet Filter Configuration on the device",
                         replace=False,
                         configuration=task.host["ipv6_packet_filter"],
                         dry_run=dry_run)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {packet_filter_key} key was found in host data.")

        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only routers and L3_devices are supported.", task)