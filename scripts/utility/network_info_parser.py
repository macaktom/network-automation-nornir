import datetime
import re
from typing import Tuple, List, Dict

from nornir.core.task import AggregatedResult, MultiResult


class NetworkInfoParser:
    """
    Třída, která obsahuje metody pro parsování specifických dat (např. pro export do .xlsx formátu, parsování
    nestrukturovaného stringu atd.).
    """

    def parse_interfaces_packet_counters_data(self, aggregated_dict_result: AggregatedResult) -> Tuple[
        List[str], List[Dict[str, str]]]:
        """
        Metoda, která zparsuje statistiky týkající se přijímaní a vysílaní paketů pro jednotlivá rozhraní síťových zařízení (ty které jsou podporovány
        knihovnou NAPALM).

        Args:
            aggregated_dict_result (AggregatedResult): objekt, který seskupuje data z více nornir úkolů (v tomto případě pouze jednoho tasku). AggregatedResult si lze představit jako slovník, jejichž klíčem jsou
                                                       jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků.

        Returns:
            Vrací tuple, který obsahuje seřazené nadpisy pro export do Excelu (sorted_headers_export) a samotné data (data).\n
            sorted_headers_export (List[str]): list seřazených nadpisů.\n
            data (List[Dict[str, str]]): - list slovníků, přičemž každý slovník obsahuje základní údaje daného síťového prvku.
        """
        data = []
        interface_data = {}
        sorted_headers_export = ["interface", "rx_broadcast_packets", "rx_discards", "rx_errors",
                                 "rx_multicast_packets", "rx_octets", "rx_unicast_packets", "tx_broadcast_packets",
                                 "tx_discards", "tx_errors", "tx_multicast_packets", "tx_octets", "tx_unicast_packets"]
        if aggregated_dict_result:
            for host in aggregated_dict_result:
                data_dict = aggregated_dict_result[host][1].result['interfaces_counters']
                data.append(data_dict)
            print(data)
            return sorted_headers_export, data

    def parse_facts_data(self, aggregated_dict_result: AggregatedResult) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Metoda, která zparsuje základní údaje o zařízení (pro zařízení všech výrobců, které jsou podporování
        knihovnou NAPALM).

        Args:
            aggregated_dict_result (AggregatedResult): Objekt, který seskupuje data z více nornir úkolů (stav
                                                       připojení + základní údaje o zařízení). AggregatedResult si lze představit jako slovník, jejichž klíčem jsou
                                                       jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků

        Returns:
            Vrací tuple, který obsahuje seřazené nadpisy pro export do Excelu (sorted_headers_export) a samotné data (data).\n
            sorted_headers_export (List[str]): list seřazených nadpisů.\n
            data (List[Dict[str, str]]): - list slovníků, přičemž každý slovník obsahuje základní údaje daného síťového prvku.
        """
        data = []
        sorted_headers_export = ["hostname", "FQDN", "vendor", "serial_number", "os_version", "uptime", "connection"]
        if aggregated_dict_result:
            for host in aggregated_dict_result:
                data_dict = aggregated_dict_result[host][1].result['facts']
                data_dict['connection'] = "OK" if aggregated_dict_result[host][2].result else "Failed"
                data_dict['uptime'] = str(datetime.timedelta(seconds=data_dict['uptime']))
                data_dict["FQDN"] = data_dict["fqdn"]
                del data_dict["fqdn"]
                del data_dict["interface_list"]
                version = data_dict['os_version']
                if data_dict['vendor'].lower() == "cisco":
                    parsed_version = version.split(",")[1].strip()
                    data_dict['os_version'] = parsed_version
                data.append(data_dict)
            print(data)
            return sorted_headers_export, data

    def get_parsed_juniper_routes(self, result: AggregatedResult, ipv6_routes: bool = False) -> str:
        """
        Metoda, která zparsuje string obsahující IPv4 i IPv6 směrovací tabulku (pouze u Juniper routerů). Metoda
        oddělí obě tabulky a uživateli vrátí string se směrovací tabulkou, kterou právě potřebuje (dle nastaveného argumentu ipv6_routes).

        Args:
            result (MultiResult): Speciální nornir objekt (připomínající Python list), který obsahuje Result objekt s neparsovaným stringem.
            ipv6_routes (bool): Parametr, který definuje, jestli metoda má vrátit string obsahující IPv4 (False) nebo IPv6 (True) směrovací tabulku. Ve výchozím stavu je nastavena na False.

        Returns:
            Vrátí string parsed_data, který obsahuje zparsovanou směrovací tabulku daného Juniper zařízení.
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
