import json
import re
import pandas as pd
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import AggregatedResult, Result, MultiResult, Task
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result
from prettytable import PrettyTable


class NetworkUtilityViewer:

    def show_device_configuration(self, task: Task) -> None:
        result = task.run(task=napalm_get, name="Show running configuration", getters=["config"])
        result[0].result = result[0].result["config"]['running'].strip()
        self._print_info_default(result)

    def show_ntp_info(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show ntp info (servers, peers, statistics)",
                          getters=["ntp_servers", "ntp_peers", "ntp_stats"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_snmp_info(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show SNMP info", getters=["snmp_information"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_users(self, task: Task, json_out: bool = False) -> None:
        if task.host['vendor'] == "cisco":
            result = task.run(task=napalm_get, name="Show created users on device", getters=["users"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            raise NornirSubTaskError("Invalid vendor to execute this task. Only Cisco is supported.", task)

    def show_connection_state(self, task: Task) -> None:
        try:
            napalm = task.host.get_connection("napalm", task.nornir.config)
            device_status = "OK" if napalm.is_alive()['is_alive'] else "is not OK"
            print(f"Connection to device {task.host} is {device_status}.")
        except Exception:
            raise

    def show_hardware_details(self, task: Task, json_out: bool = False) -> None:
        if task.host['image'] != "olive":
            result = task.run(task=napalm_get, name="Show HW details", getters=["environment"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            raise NornirSubTaskError("Command is not supported for Juniper Olive", task)

    def _get_parsed_juniper_routes(self, result: MultiResult, ipv6_routes: bool = False) -> str:
        result_string = result[0].result
        parsed_data = ""
        split_inet6_part = re.split(f"inet6.0:", result_string)
        if ipv6_routes:
            parsed_data = "inet6.0: " + split_inet6_part[1].strip()
        else:
            parsed_data = split_inet6_part[0].strip()
        return parsed_data

    def show_ipv4_routes(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ip route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show IP routes", command_string=command)
        if task.host['vendor'] == "juniper":
            result[0].result = self._get_parsed_juniper_routes(result)
        self._print_info_default(result)

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

    def show_packet_filter_info(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "do show access-lists"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show firewall"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_config, name="Show packet filters info", config_commands=[command])
        result[0].result = self._get_parsed_packet_filter_data(task.host['vendor'], result)
        self._print_info_default(result)

    def show_ipv6_routes(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ipv6 route"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show route"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show IP routes", command_string=command)
        if task.host['vendor'] == "juniper":
            result[0].result = self._get_parsed_juniper_routes(result, ipv6_routes=True)
        self._print_info_default(result)

    def show_vlans(self, task: Task, json_out: bool = False) -> None:
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "switch" or task.host['dev_type'] == "L3_switch"):
            result = task.run(task=napalm_get, name="Show configured VLANs", getters=["vlans"])
            if json_out:
                self._print_info_json(result)
            else:
                self._print_info_default(result)
        else:
            raise NornirSubTaskError("Invalid device type to execute this task. Only switches are allowed", task)

    def show_device_facts(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show device basic facts", getters=["facts"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_basic_info(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show interfaces basic info", getters=["interfaces"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_ip_info(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show IP addresses assigned to interfaces", getters=["interfaces_ip"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_interfaces_packet_counters(self, task: Task, json_out: bool = False) -> None:
        result = task.run(task=napalm_get, name="Show interfaces packet counters", getters=["interfaces_counters"])
        if json_out:
            self._print_info_json(result)
        else:
            self._print_info_default(result)

    def show_ospf_neighbors(self, task: Task) -> None:
        command = ""
        if task.host['vendor'] == "cisco" and (
                task.host['dev_type'] == "router" or task.host['dev_type'] == "L3_switch"):
            command = "show ip ospf neighbor"
        elif task.host['vendor'] == "juniper" and task.host['dev_type'] == "router":
            command = "show ospf neighbor"
        else:
            raise NornirSubTaskError("Function was not implemented for particular vendor.", task)
        result = task.run(task=netmiko_send_command, name="Show OSPF neighbors", command_string=command,
                          use_textfsm=True)
        self._print_info_default(result)

    def _print_info_default(self, result_dict: MultiResult) -> None:
        if not result_dict.failed:
            print(f"Device: {result_dict.host}")
            for result in result_dict:
                print_result(result)

    def _print_info_json(self, result_dict: MultiResult) -> None:
        if not result_dict.failed:
            print(f"Device: {result_dict.host}")
            for result in result_dict:
                print(json.dumps(result.result, sort_keys=True, indent=4))
