import datetime
import re
from typing import Tuple, List, Dict
import copy
from nornir.core.task import AggregatedResult, MultiResult


class NetworkInfoParser:
    """
    Třída, která obsahuje metody pro parsování specifických dat (např. pro export do .xlsx formátu, parsování
    nestrukturovaného stringu atd.).
    """

    def parse_interfaces_packet_counters_data(self, aggregated_dict_result: AggregatedResult) -> None:
        """
        Metoda, která zparsuje statistiky týkající se přijímání a vysílání paketů pro jednotlivá rozhraní síťových zařízení (ty které jsou podporovány
        knihovnou NAPALM).

        Args:
            aggregated_dict_result (AggregatedResult): objekt, který seskupuje data z více nornir úkolů (v tomto případě pouze jednoho tasku). AggregatedResult si lze představit jako slovník, jejichž klíčem jsou
                                                       jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků. Tento objekt bude zparsován a modifikován.

        Returns:
            None
        """
        dict_rename = {"rx_broadcast_packets": "rx_broadcast", "rx_multicast_packets": "rx_multicast",
                       "rx_unicast_packets": "rx_unicast", "tx_broadcast_packets": "tx_broadcast",
                       "tx_multicast_packets": "tx_multicast", "tx_unicast_packets": "tx_unicast"}
        if aggregated_dict_result:
            for host in aggregated_dict_result:
                interfaces_data = aggregated_dict_result[host][1].result['interfaces_counters']
                for interface in interfaces_data:
                    interface_dict = interfaces_data[interface]
                    interface_dict['interface'] = interface
                    for key in dict_rename:
                        rename_value = dict_rename[key]
                        interface_dict[rename_value] = interface_dict.pop(key)

    def get_parsed_facts_data(self, aggregated_dict_result: AggregatedResult) -> List[Dict[str, str]]:
        """
        Metoda, která zparsuje základní údaje o zařízení (pro zařízení všech výrobců, které jsou podporovány
        knihovnou NAPALM).

        Args:
            aggregated_dict_result (AggregatedResult): Objekt, který seskupuje data z více nornir úkolů (stav
                                                       připojení + základní údaje o zařízení). AggregatedResult si lze představit jako slovník, jejichž klíčem jsou
                                                       jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků

        Returns:
            Vrací list slovníků data.\n
            data (List[Dict[str, str]]): list slovníků, přičemž každý slovník obsahuje základní údaje o daném síťovém prvku.
        """
        data = []
        if aggregated_dict_result:
            for host in aggregated_dict_result:
                data_dict = aggregated_dict_result[host][1].result['facts']
                data_dict['connection'] = "OK" if aggregated_dict_result[host][2].result else "Failed"
                data_dict['uptime'] = str(datetime.timedelta(seconds=data_dict['uptime']))
                data_dict["FQDN"] = data_dict.pop("fqdn")
                version = data_dict['os_version']
                if data_dict['vendor'].lower() == "cisco":
                    parsed_version = version.split(",")[1].strip()
                    data_dict['os_version'] = parsed_version
                data.append(data_dict)
            return data

    def get_parsed_juniper_routes(self, result: MultiResult, ipv6_routes: bool = False) -> str:
        """
        Metoda, která zparsuje string obsahující IPv4 i IPv6 směrovací tabulku (pouze u Juniper routerů). Metoda
        oddělí obě tabulky a uživateli vrátí string se směrovací tabulkou, kterou právě potřebuje (dle nastaveného argumentu ipv6_routes).

        Args:
            result (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje Result objekt s neparsovaným stringem.
            ipv6_routes (bool): Parametr, který definuje, jestli metoda má vrátit string obsahující IPv4 (False) nebo IPv6 (True) směrovací tabulku. Ve výchozím stavu je nastavena na False.

        Returns:
            Vrátí string parsed_data, který obsahuje zparsovanou směrovací tabulku daného Juniper routeru.
        """

        result_string = result[0].result
        parsed_data = ""
        split_inet6_part = re.split(f"inet6.0:", result_string)
        if split_inet6_part:
            if ipv6_routes:
                parsed_data = "inet6.0: " + split_inet6_part[1].strip()
            else:
                parsed_data = split_inet6_part[0].strip()
        return parsed_data

    def get_parsed_packet_filter_data(self, vendor: str, result: MultiResult) -> str:
        """
        Metoda, která zparsuje string obsahující definované paketové filtry.

        Args:
            vendor (str): String obsahující informaci o výrobci daného zařízení.
            result (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje Result objekt s neparsovaným stringem.

        Returns:
            Vrátí string parsed_result, který obsahuje zparsované paketové filtry daného zařízení. V případě nepodporovaného vendora vrací prázdný string.
        """
        result_string = result[0].result
        parsed_result = ""
        if vendor.strip().lower() == "cisco":
            split_access_command = re.split(r"do show access-lists\n", result_string)[1]
            parsed_result = "" if "access list" not in split_access_command else \
                re.split(f"\n{result[0].host}\(config\)\#end", split_access_command)[0]
        elif vendor.strip().lower() == "juniper":
            split_show_firewall_part = re.split(f"show firewall", result_string)[1]
            parsed_result = "" if "inet" not in split_show_firewall_part else \
                re.split(r"\n\[edit\]\n", split_show_firewall_part)[0].strip()
        return parsed_result
