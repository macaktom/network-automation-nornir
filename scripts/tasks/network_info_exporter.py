import json
import os
import re
from pathlib import Path
from os import path
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import AggregatedResult, Result, Task, MultiResult
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result

from scripts.tasks.excel_exporter import ExcelExporter
from scripts.tasks.text_file_exporter import TextFileExporter


class NetworkInfoExporter:
    def __init__(self, txt_exporter: TextFileExporter, excel_exporter: ExcelExporter):
        self.txt_exporter = txt_exporter
        self.excel_exporter = excel_exporter

    def get_conn_state_result(self, task: Task) -> Result:
        napalm = task.host.get_connection("napalm", task.nornir.config)
        result = napalm.is_alive()
        return Result(host=task.host, result=result)

    def get_conn_state_and_device_facts(self, task: Task) -> AggregatedResult:
        result = task.run(task=napalm_get, name="Get device basic facts", getters=["facts"])
        result += task.run(task=self.get_conn_state_result, name="Get conn status")
        return AggregatedResult(*result)

    def _export_to_file(self, full_file_path: Path, data) -> None:
        if path.isfile:
            folder_path = full_file_path.parent
            folder_path.mkdir(parents=True, exist_ok=True)
            with open(full_file_path, 'w') as file:
                file.write(data)
                print(f"{full_file_path.name} was created successfully.")
        else:
            print("Provided filepath is not valid.")

    def _get_parsed_juniper_routes(self, result: MultiResult, ipv6_routes: bool = False) -> str:
        result_string = result[0].result
        parsed_data = ""
        split_inet6_part = re.split(f"inet6.0:", result_string)
        if ipv6_routes:
            parsed_data = "inet6.0: " + split_inet6_part[1].strip()
        else:
            parsed_data = split_inet6_part[0].strip()
        return parsed_data

    def export_device_configuration(self, task: Task) -> None:
        result = task.run(task=napalm_get, name="Get running configuration", getters=["config"])
        if not result.failed:
            running_configuration = result[0].result["config"]['running'].strip()
            host = result[0].host
            file_path = Path(Path.cwd() / 'export' / "running_configuration" / f"{host}.txt")
            self._export_to_file(file_path, running_configuration)
        else:
            print("Export failed - more in nornir.log")

    def export_ipv4_routes(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ip route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Get IP routes", command_string=command)
        if not result.failed:
            ipv4_routes = result[0].result
            host = result[0].host
            if task.host['vendor'] == "juniper":
                ipv4_routes = self._get_parsed_juniper_routes(result)
            file_path = Path(Path.cwd() / 'export' / "ip_routes" / f"{host}_ipv4.txt")
            self._export_to_file(file_path, ipv4_routes)
        else:
            print("Export failed - more in nornir.log")

    def export_ipv6_routes(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ipv6 route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Get IP routes", command_string=command)
        if not result.failed:
            ipv6_routes = result[0].result
            host = result[0].host
            if task.host['vendor'] == "juniper":
                ipv6_routes = self._get_parsed_juniper_routes(result, ipv6_routes=True)
            file_path = Path(Path.cwd() / 'export' / "ip_routes" / f"{host}_ipv6.txt")
            self._export_to_file(file_path, ipv6_routes)
        else:
            print("Export failed - more in nornir.log")

    def export_packet_filter_info(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "do show access-lists"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show firewall"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_config, name="Get packet filters info", config_commands=[command])
        if not result.failed:
            packet_filter_info = self._get_parsed_packet_filter_data(task.host['vendor'], result)
            host = result[0].host
            if packet_filter_info != "":
                file_path = Path(Path.cwd() / 'export' / "packet_filter" / f"{host}.txt")
                self._export_to_file(file_path, packet_filter_info)
            else:
                print(f"{host}: No ACL defined.")
        else:
            print("Export failed - more in nornir.log")

    def _get_parsed_packet_filter_data(self, vendor: str, result: MultiResult) -> str:
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

    def export_device_facts(self, task: Task):
        result = task.run(task=napalm_get, name="Show device basic facts", getters=["facts"])
        self._print_info_to_console(result)

    def export_interfaces_packet_counters(self, task):
        result = task.run(task=napalm_get, name="Show interfaces packet counters", getters=["interfaces_counters"])
        self._print_info_to_console(result)

    def _print_info_to_console(self, result_dict: MultiResult):
        if not result_dict.failed:
            print(f"Device: {result_dict.host}")
            for result in result_dict:
                print(json.dumps(result.result, sort_keys=True, indent=4))
