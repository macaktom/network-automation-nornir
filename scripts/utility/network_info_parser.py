import datetime
import re
from typing import Tuple, List, Dict

from nornir.core.task import AggregatedResult, MultiResult


class NetworkInfoParser:

    def _parse_facts_data(self, aggregated_dict_result: AggregatedResult) -> Tuple[List[str], List[Dict[str, str]]]:
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

    def get_parsed_juniper_routes(self, result: MultiResult, ipv6_routes: bool = False) -> str:
        result_string = result[0].result
        parsed_data = ""
        split_inet6_part = re.split(f"inet6.0:", result_string)
        if ipv6_routes:
            parsed_data = "inet6.0: " + split_inet6_part[1].strip()
        else:
            parsed_data = split_inet6_part[0].strip()
        return parsed_data

    def get_parsed_packet_filter_data(self, vendor: str, result: MultiResult) -> str:
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
