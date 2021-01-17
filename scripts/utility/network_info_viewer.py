import datetime
import json
from colorama import Fore
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import MultiResult, Task
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result, print_title
from scripts.utility.network_info_parser import NetworkInfoParser


class NetworkUtilityViewer:
    """
    Třída, která slouží pro zobrazení informací ze síťových zařízení.
    Data jsou zobrazována v konzoli (buď jako strukturovaný JSON string nebo nestrukturovaný string - podle NAPALM nebo TextFSM podpory)
    """

    def show_device_configuration(self, task: Task) -> None:
        """
        Metoda pro zobrazení současné (running) konfigurace u jednotlivých síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show running configuration", getters=["config"])
        if result[0].result and not result.failed:
            result[0].result = result[0].result["config"]['running'].strip()
        self._print_info_default(result)

    def show_ntp_info(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení NTP (Network Time Protocol) informací (NTP synchronizační statistiky, IP adresy NTP
        serverů a peerů - zobrazení konfigurace není ještě implementované komunitou, pouze IP adresy).

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show NTP info (servers, peers, statistics)",
                          getters=["ntp_servers", "ntp_peers", "ntp_stats"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_snmp_info(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení SNMP (Simple Network Management Protocol) údajů.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show SNMP info", getters=["snmp_information"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_users(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení vytvořených uživatelů na jednotlivých zařízeních.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        if not task.host['image'] == "olive":
            result = task.run(task=napalm_get, name="Show created users on device", getters=["users"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            print(f"{Fore.RED}Device {task.host.name}: Method is not supported by Juniper Olive - more in nornir.log.") #NAPALM metoda get_users nepodporuje Juniper Olive (Juniper zařízení řady SRX, MX by měly být podle komunity v pořádku).
            raise NornirSubTaskError("NAPALM get_users is not supported by Juniper Olive - bad parsing (Juniper SRX and MX devices were tested by community and should be fine).", task)

    def show_connection_state(self, task: Task) -> None:
        """
        Metoda pro zobrazení stavu připojení k jednotlivým zařízením.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            None
        """
        napalm_conn = task.host.get_connection("napalm", task.nornir.config)
        device_status = "OK" if napalm_conn.is_alive()['is_alive'] else "not OK"
        text_color = Fore.GREEN if device_status == "OK" else Fore.RED
        print(f"{text_color}Connection to device {task.host.name} is {device_status}.")

    def show_hardware_details(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení HW vytížení síťových prvků.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        if task.host['image'] != "olive":
            result = task.run(task=napalm_get, name="Show HW details", getters=["environment"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            print(f"{Fore.RED}Device {task.host.name}: Method isn't supported by Juniper Olive. - show chassis commands aren't functional.") # příkazy show chassis nejsou podporovány Juniper Olive - tzn. NAPALM metoda get_environment není podporována.

    def show_ipv4_routes(self, task: Task) -> None:
        """
        Metoda pro zobrazení IPv4 směrovací tabulky jednotlivých zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu (např. nepodporovaný vendor).

        Returns:
            None
        """
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ip route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show IPv4 routes", command_string=command)
        if task.host['vendor'] == "juniper" and result[0].result:
            parser = NetworkInfoParser()
            parsed_routes = parser.get_parsed_juniper_routes(result)
            result[0].result = parsed_routes if parsed_routes else f"{Fore.RED}Device {task.host.name}: No IPv4 routes were found."
        self._print_info_default(result)

    def show_packet_filter_info(self, task: Task) -> None:
        """
        Metoda pro zobrazení definovaných paketových filtrů.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu (např. nepodporovaný vendor).

        Returns:
            None
        """
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show access-lists"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show configuration firewall"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show packet filters info", command_string=command)
        self._print_info_default(result)

    def show_ipv6_routes(self, task: Task) -> None:
        """
        Metoda pro zobrazení IPv6 směrovací tabulky jednotlivých zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu (např. nepodporovaný vendor).

        Returns:
            None
        """
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ipv6 route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show IPv6 routes", command_string=command)
        if task.host['vendor'] == "juniper" and result[0].result:
            parser = NetworkInfoParser()
            parsed_routes = parser.get_parsed_juniper_routes(result, ipv6_routes=True)
            result[0].result = parsed_routes if parsed_routes else f"{Fore.RED}Device {task.host.name}: No IPv6 routes were found."
        self._print_info_default(result)

    def show_vlans(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení konfigurovaných VLAN.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        if task.host['dev_type'] == "switch" or task.host['dev_type'] == "L3_switch":
            result = task.run(task=napalm_get, name="Show configured VLANs", getters=["vlans"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            print(f"{Fore.RED}Device {task.host.name}: Invalid device type. Only switches and L3_switches are supported.")

    def show_device_facts(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení základní údajů o síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show device basic facts", getters=["facts"])

        if not result.failed:
            uptime = result[0].result['facts']['uptime']
            result[0].result['facts']['uptime'] = str(datetime.timedelta(seconds=uptime))

        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_basic_info(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení základních informací o rozhraních jednotlivých síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show interfaces basic info", getters=["interfaces"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_ip_info(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení konfigurovaných IP adres na rozhraních jednotlivých síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show IP addresses assigned to interfaces", getters=["interfaces_ip"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_packet_counters(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení statistik týkající se přijímání a vysílání paketů pro jednotlivá rozhraní síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show interfaces packet counters", getters=["interfaces_counters"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_ospf_neighbors(self, task: Task, ipv6=False) -> None:
        """
        Metoda pro zobrazení OSPF (nebo OSPFv3) sousedů.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            ipv6 (bool): Parametr, který definuje, jestli mají být zobrazeni OSPF (False) nebo OSPFv3 (True) sousedé.

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu (např. nepodporovaný vendor).

        Returns:
            None
        """
        command = ""
        if task.host['vendor'] == "cisco" and task.host['dev_type'] == "router":
            if ipv6:
                command = "show ipv6 ospf neighbor"
            else:
                command = "show ip ospf neighbor"
        elif task.host['vendor'] == "cisco" and task.host['dev_type'] == "L3_switch":
            if ipv6:
                print(f"{Fore.RED}Device {task.host.name}: OSPFv3 is not supported for {task.host['image']}.")
                raise NornirSubTaskError("Function was not implemented for particular device.", task)
            else:
                command = "show ip ospf neighbor"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            if ipv6:
                command = "show ospf3 neighbor"
            else:
                command = "show ospf neighbor"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        if ipv6:
            result = task.run(task=netmiko_send_command, name="Show OSPFv3 neighbors", command_string=command)
        else:
            result = task.run(task=netmiko_send_command, name="Show OSPF neighbors", command_string=command)
        self._print_info_default(result)

    def _print_info_default(self, result_list: MultiResult) -> None:
        """
        Upravená defaultní nornir metoda, pro přehledné zobrazení Nornir objektů v konzoli.

        Args:
            result_list (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje výsledky několika nornir úkolů konkrétního síťového zařízení.

        Returns:
            None
        """
        if not result_list.failed:
            print_title(f"Device {result_list.host}:")
            for result in result_list:
                print_result(result)
                print()
        else:
            print(f"{Fore.RED}Task failed for host {result_list.host}")

    def _print_info_json(self, result_list: MultiResult) -> None:
        """
         Metoda, pro přehledné zobrazení Nornir objektů v konzoli. Nornir objekty jsou zobrazeny jako formátovaný JSON string.

         Args:
             result_list (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje výsledky několika nornir úkolů konkrétního síťového zařízení.

         Returns:
             None
         """
        if not result_list.failed:
            print_title(f"Device {result_list.host}:")
            for result in result_list:
                print(json.dumps(result.result, sort_keys=True, indent=4))
        else:
            print(f"{Fore.RED}Task failed for host {result_list.host}")
