import json
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import MultiResult, Task
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result
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
        if result[0].result:
            result[0].result = result[0].result["config"]['running'].strip()
        self._print_info_default(result)

    def show_ntp_info(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení NTP (Network Time Protocol) informací.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Returns:
            None
        """
        result = task.run(task=napalm_get, name="Show ntp info (servers, peers, statistics)",
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

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních (např. NAPALM metoda get_users není podporována obrazem Juniper Olive.

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
            raise NornirSubTaskError("Not supported for Juniper Olive image.", task)

    def show_connection_state(self, task: Task) -> None:
        """
        Metoda pro zobrazení stavu připojení k jednotlivým zařízením.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            None
        """
        napalm = task.host.get_connection("napalm", task.nornir.config)
        device_status = "OK" if napalm.is_alive()['is_alive'] else "is not OK"
        print(f"Connection to device {task.host} is {device_status}.")

    def show_hardware_details(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení HW vytížení síťových prvků.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních (např. NAPALM metoda get_environment není podporována obrazem Juniper Olive.

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
            raise NornirSubTaskError("Command is not supported for Juniper Olive", task)

    def show_ipv4_routes(self, task: Task) -> None:
        """
        Metoda pro zobrazení IPv4 směrovací tabulky jednotlivých zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních (podporuje pouze Juniper a Cisco zařízení).

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
        result = task.run(task=netmiko_send_command, name="Show IP routes", command_string=command)
        if task.host['vendor'] == "juniper" and result[0].result:
            parser = NetworkInfoParser()
            result[0].result = parser.get_parsed_juniper_routes(result)
        self._print_info_default(result)

    def show_packet_filter_info(self, task: Task) -> None:
        """
        Metoda pro zobrazení definovaných paketových filtrů.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních (podporuje pouze Juniper a Cisco zařízení).

        Returns:
            None
        """
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "do show access-lists"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show firewall"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_config, name="Show packet filters info", config_commands=[command])
        parser = NetworkInfoParser()
        if result[0].result:
            result[0].result = parser.get_parsed_packet_filter_data(task.host['vendor'], result)
        self._print_info_default(result)

    def show_ipv6_routes(self, task: Task) -> None:
        """
        Metoda pro zobrazení IPv6 směrovací tabulky jednotlivých zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních (podporuje pouze Juniper a Cisco zařízení).

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
        result = task.run(task=netmiko_send_command, name="Show IP routes", command_string=command)
        if task.host['vendor'] == "juniper" and result[0].result:
            parser = NetworkInfoParser()
            result[0].result = parser.get_parsed_juniper_routes(result, ipv6_routes=True)
        self._print_info_default(result)

    def show_vlans(self, task: Task, json_out: bool = False) -> None:
        """
        Metoda pro zobrazení konfigurovaných VLAN.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            json_out (bool): Parametr, který určuje, jestli se má pro zobrazení použít JSON string (True) nebo výchozí Nornir funkce (False). Defaultně je nastaven False.

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních.

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
            raise NornirSubTaskError("Invalid device type to execute this task. Only switches are allowed", task)

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
        Metoda pro zobrazení statistik týkající se přijímaní a vysílaní paketů pro jednotlivá rozhraní síťových zařízení.

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
            NornirSubTaskError: Výjimka, která nastane, pokud se objeví chyba v nornir úkolu nebo pokud provádíte
                                export na nepodporovaných zařízeních.

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
        result = task.run(task=netmiko_send_command, name="Show OSPF neighbors", command_string=command,
                          use_textfsm=True)
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
            print(f"Device: {result_list.host}")
            for result in result_list:
                print_result(result)
                print()

    def _print_info_json(self, result_list: MultiResult) -> None:
        """
         Metoda, pro přehledné zobrazení Nornir objektů v konzoli. Nornir objekty jsou zobrazeny jako formátovaný JSON string.

         Args:
             result_list (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje výsledky několika nornir úkolů konkrétního síťového zařízení.

         Returns:
             None
         """
        if not result_list.failed:
            print(f"Device: {result_list.host}")
            for result in result_list:
                print(json.dumps(result.result, sort_keys=True, indent=4))
