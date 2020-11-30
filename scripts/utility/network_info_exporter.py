import json
from pathlib import Path

from nornir.core import Nornir
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import Task, MultiResult
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko import netmiko_send_command, netmiko_send_config

from scripts.utility.network_info_parser import NetworkInfoParser
from scripts.utility.text_file_exporter import TextFileExporter


class NetworkInfoExporter:

    def export_device_facts(self, nornir_device: Nornir):
        pass

    def export_device_configuration(self, task: Task) -> None:
        result = task.run(task=napalm_get, name="Get running configuration", getters=["config"])
        if not result.failed:
            running_configuration = result[0].result["config"]['running'].strip()
            host = result[0].host
            file_path = Path(Path.cwd() / 'export' / "running_configuration" / f"{host}.txt")
            exporter = TextFileExporter(file_path)
            exporter.export_to_file(running_configuration)
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
                parser = NetworkInfoParser()
                ipv4_routes = parser.get_parsed_juniper_routes(result)
            file_path = Path(Path.cwd() / 'export' / "ip_routes" / f"{host}_ipv4.txt")
            exporter = TextFileExporter(file_path)
            exporter.export_to_file(ipv4_routes)
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
                parser = NetworkInfoParser()
                ipv6_routes = parser.get_parsed_juniper_routes(result, ipv6_routes=True)
            file_path = Path(Path.cwd() / 'export' / "ip_routes" / f"{host}_ipv6.txt")
            exporter = TextFileExporter(file_path)
            exporter.export_to_file(ipv6_routes)
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
            parser = NetworkInfoParser()
            packet_filter_info = parser.get_parsed_packet_filter_data(task.host['vendor'], result)
            host = result[0].host
            if packet_filter_info != "":
                file_path = Path(Path.cwd() / 'export' / "packet_filter" / f"{host}.txt")
                exporter = TextFileExporter(file_path)
                exporter.export_to_file(packet_filter_info)
            else:
                print(f"{host}: No ACL defined.")
        else:
            print("Export failed - more in nornir.log")

    def _print_info_to_console(self, result_dict: MultiResult):
        if not result_dict.failed:
            print(f"Device: {result_dict.host}")
            for result in result_dict:
                print(json.dumps(result.result, sort_keys=True, indent=4))
