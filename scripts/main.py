import datetime
from pathlib import Path
from pprint import pprint
from nornir import InitNornir
from nornir.core import Task, Nornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_cli
from nornir_netmiko import netmiko_send_command
from nornir_utils.plugins.functions import print_result

from scripts.tasks.delete_configuration import DeleteConfiguration
from scripts.tasks.eigrp_configuration import EIGRPConfiguration
from scripts.tasks.interfaces_configuration import InterfacesConfiguration
from scripts.tasks.nat_configuration import NATConfiguration
from scripts.tasks.ospf_configuration import OSPFConfiguration
from scripts.tasks.packet_filter_configuration import PacketFilterConfiguration
from scripts.tasks.static_configuration import StaticRoutingConfiguration
from scripts.utility.network_info_collector import NetworkInfoCollector
from scripts.utility.network_info_exporter import NetworkInfoExporter
from scripts.utility.network_info_viewer import NetworkUtilityViewer


# Rozdelit SHOW commandy:
# 1) Ty ktere jsou podporovany NAPALMem u OBOU vendoru (nutne udelat specialni tabulku pro printovani) - lze provest export do JSONu, .txt
# 2) Ty ktere NAPALM nema nebo jsou podporovany pouze u nektereho vendora - print pouze neupraveneho textu do konzole + export .txt
# Tři druhy metod teď budou (kromě potom Jinja2): GET, SHOW, EXPORT. Show commandy je ted nutne prepsat na GET commandy, vraci Resulty

def std_print(agg_result):
    print()
    for k, multi_result in agg_result.items():
        print("-" * 50)
        print(k)
        for result_obj in multi_result:
            if isinstance(result_obj.result, str):
                print(result_obj.result)
            else:
                pprint(result_obj.result)
        print("-" * 50)
        print()
    print()


def configure_devices(nornir_devices: Nornir, task_func: callable, task_name: str, dry_run: bool) -> None:
    result = nornir_devices.run(task=task_func, name=task_name, dry_run=dry_run)
    print_result(result)


def send_command(nornir_devices: Nornir, task_name: str, dry_run: bool) -> None:
    result = nornir_devices.run(task=netmiko_send_command, name=task_name, dry_run=dry_run)
    print_result(result)


def main() -> None:
    """
    Hlavní funkce skriptu, která se zavolá po spuštění skriptu main.py

    Returns:
        None
    """
    # nr = InitNornir(config_file="config.yml", core = {"raise_on_error": True}) # Nornir objekt, který upozorní na chybu při provedení tasku
    nr = InitNornir(
        config_file="config.yml")  # Nornir objekt, který přeskočí hosty, které nezvládli požadovaný task - více o chybě v nornir.log
    routers = nr.filter(F(dev_type="router"))
    juniper_devices = nr.filter(F(groups__contains="junos_group"))
    l3_switches = nr.filter(F(dev_type="L3_switch"))
    cisco_router = nr.filter(F(groups__contains="cisco_group") & F(dev_type="router"))
    l3_cisco = nr.filter(F(groups__contains="cisco_group") & F(dev_type="router") | F(dev_type="L3_switch"))
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch"))
    viewer = NetworkUtilityViewer()
    exporter = NetworkInfoExporter(NetworkInfoCollector())
    ospf_config = OSPFConfiguration()
    eigrp_config = EIGRPConfiguration()
    static_routing_config = StaticRoutingConfiguration()
    interfaces_configuration = InterfacesConfiguration()
    packet_filter = PacketFilterConfiguration()
    nat_config = NATConfiguration()
    delete_config = DeleteConfiguration()
    # juniper_devices.run(task=viewer.show_device_configuration)
    #all_devices.run(task=viewer.show_device_facts)

    configure_devices(all_devices, interfaces_configuration.configure_ipv4_interfaces, "IPv4 interfaces config", False)
    configure_devices(all_devices, interfaces_configuration.configure_ipv6_interfaces, "IPv6 interfaces config", False)
    configure_devices(l3_switches, interfaces_configuration.configure_switching_interfaces,"Switching interfaces config", False)
    configure_devices(all_devices, static_routing_config.configure_static_routing_ipv4, "Static routing config", False)
    configure_devices(all_devices, ospf_config.configure_ospf, "OSPFv2 config", False)
    configure_devices(l3_cisco, eigrp_config.configure_eigrp_ipv4, "EIGRP config", False)
    configure_devices(all_devices, packet_filter.configure_ipv4_packet_filters, "IPv4 packet filter config", False)
    configure_devices(l3_cisco, nat_config.configure_source_nat_overload, "NAT Overload config", False)
    configure_devices(routers, ospf_config.configure_ospfv3, "OSPFv3 config", False)
    configure_devices(l3_cisco, eigrp_config.configure_eigrp_ipv6, "EIGRP IPV6 config", False)
    configure_devices(all_devices, static_routing_config.configure_static_routing_ipv6, "IPv6 Static Routing config",False)
    configure_devices(all_devices, packet_filter.configure_ipv6_packet_filters, "IPv6 packet filter config", False)
    configure_devices(all_devices, delete_config.delete_configuration, "Delete Configuration", dry_run=False)

    # configure_devices(juniper_devices, static_routing_config.configure_static_routing_ipv4, "Static routing config", False)
    # configure_devices(juniper_devices, ospf_config.configure_ospf, "OSPFv2 config", False)
    #configure_devices(routers, ospf_config.configure_ospfv3, "OSPFv3 config", False)
    # configure_devices(juniper_devices, static_routing_config.configure_static_routing_ipv6, "IPv6 Static Routing config", False)
    # configure_devices(juniper_devices, interfaces_configuration.configure_ipv4_interfaces, "IPv4 interfaces config", False)
    # configure_devices(juniper_devices, interfaces_configuration.configure_ipv6_interfaces, "IPv6 interfaces config", False)
    # configure_devices(juniper_devices, packet_filter.configure_ipv4_packet_filters, "IPv4 packet filter config", False)
    # configure_devices(juniper_devices, packet_filter.configure_ipv6_packet_filters, "IPv6 packet filter config", False)
    all_devices.run(task=exporter.export_device_configuration)
    # all_devices.run(task=exporter.export_packet_filter_info)
    # all_devices.run(task=exporter.export_ipv4_routes)
    # all_devices.run(task=exporter.export_ipv6_routes)
    # exporter.export_device_facts(all_devices)
    # exporter.export_interfaces_packet_counters(all_devices)

    # print(z['R1'][1].result['facts'])
    # print(z['R1'][2].result)
    # all_devices.run(task=viewer.show_interfaces_packet_counters, json_out=True)


if __name__ == "__main__":
    start = datetime.datetime.now()
    main()
    print("Time elapsed: " + str((datetime.datetime.now() - start)))
