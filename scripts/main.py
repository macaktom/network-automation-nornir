import datetime
from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.filter import F
from nornir_netmiko import netmiko_send_command
from nornir_utils.plugins.functions import print_result
from scripts.tasks.delete_configuration import DeleteConfiguration
from scripts.tasks.eigrp_configuration import EIGRPConfiguration
from scripts.tasks.interfaces_configuration import InterfacesConfiguration
from scripts.tasks.linux_configuration import LinuxConfiguration
from scripts.tasks.nat_configuration import NATConfiguration
from scripts.tasks.ospf_configuration import OSPFConfiguration
from scripts.tasks.packet_filter_configuration import PacketFilterConfiguration
from scripts.tasks.static_configuration import StaticRoutingConfiguration
from scripts.utility.credential_handler import CredentialHandler
from scripts.utility.network_info_collector import NetworkInfoCollector
from scripts.utility.network_info_exporter import NetworkInfoExporter
from scripts.utility.network_info_viewer import NetworkUtilityViewer


def setup_inventory():
    creds_handler = CredentialHandler()
    nr = InitNornir(config_file="config.yml")  # Nornir objekt, který přeskočí hosty, které nezvládli požadovaný (sub)task - více o chybě v nornir.log
    creds_handler.insert_creds(nr)
    return nr


def configure_linux_servers(nornir_devices: Nornir, task_func: callable, task_name: str, enable: bool = True) -> None:
    result = nornir_devices.run(task=task_func, name=task_name, enable=enable)
    print_result(result)


def configure_network_devices(nornir_devices: Nornir, task_func: callable, task_name: str, dry_run: bool) -> None:
    result = nornir_devices.run(task=task_func, name=task_name, dry_run=dry_run)
    print_result(result)


def send_command(nornir_devices: Nornir, command_string: str, task_name: str, enable=False) -> None:
    result = nornir_devices.run(task=netmiko_send_command, command_string=command_string, name=task_name, enable=enable)
    print_result(result)


def main() -> None:
    """
    Hlavní funkce skriptu, která se zavolá po spuštění skriptu main.py

    Returns:
        None
    """
    nornir_obj = setup_inventory()
    routers = nornir_obj.filter(F(dev_type="router"))
    juniper_devices = nornir_obj.filter(F(groups__contains="juniper"))
    l3_switches = nornir_obj.filter(F(dev_type="L3_switch"))
    cisco_routers = nornir_obj.filter(F(groups__contains="cisco") & F(dev_type="router"))
    l3_cisco = nornir_obj.filter(F(groups__contains="cisco") & F(dev_type="router") | F(dev_type="L3_switch"))
    all_devices = nornir_obj.filter(F(dev_type="router") | F(dev_type="L3_switch"))
    ubuntu_servers = nornir_obj.filter(F(dev_type="ubuntu_server") | F(groups__contains="linux"))
    viewer = NetworkUtilityViewer()
    exporter = NetworkInfoExporter(NetworkInfoCollector())
    ospf_config = OSPFConfiguration()
    eigrp_config = EIGRPConfiguration()
    static_routing_config = StaticRoutingConfiguration()
    interfaces_configuration = InterfacesConfiguration()
    packet_filter = PacketFilterConfiguration()
    nat_config = NATConfiguration()
    delete_config = DeleteConfiguration()
    linux_config = LinuxConfiguration()

    #all_devices.run(task=viewer.show_device_facts, json_out=True)
    #all_devices.run(task=viewer.show_packet_filter_info)
    #all_devices.run(task=viewer.show_ipv6_routes)
    #all_devices.run(task=viewer.show_ospf_neighbors, ipv6=False)
    #configure_network_devices(all_devices, interfaces_configuration.configure_ipv4_interfaces, "IPv4 interfaces config", dry_run=False)
    #configure_network_devices(all_devices, interfaces_configuration.configure_ipv6_interfaces, "IPv6 interfaces config", dry_run=False)
    #configure_network_devices(l3_switches, interfaces_configuration.configure_switching_interfaces, "Switching interfaces config", dry_run=False)
    #configure_network_devices(all_devices, static_routing_config.configure_static_routing_ipv4, "Static routing config",dry_run=False)
    #configure_network_devices(all_devices, ospf_config.configure_ospf, "OSPFv2 config", dry_run=False)
    #configure_network_devices(l3_cisco, eigrp_config.configure_eigrp_ipv4, "EIGRP config", dry_run=False)
    #configure_network_devices(all_devices, packet_filter.configure_ipv4_packet_filters, "IPv4 packet filter config",dry_run=False)
    #configure_network_devices(l3_cisco, nat_config.configure_source_nat_overload, "NAT Overload config", dry_run=False)
    #configure_network_devices(routers, ospf_config.configure_ospfv3, "OSPFv3 config", dry_run=False)
    #configure_network_devices(l3_cisco, eigrp_config.configure_eigrp_ipv6, "EIGRP IPV6 config", dry_run=False)
    #configure_network_devices(all_devices, static_routing_config.configure_static_routing_ipv6,"IPv6 Static Routing config", dry_run=False)
    #configure_network_devices(all_devices, packet_filter.configure_ipv6_packet_filters, "IPv6 packet filter config",dry_run=False)
    #configure_network_devices(all_devices, delete_config.delete_configuration, "Delete Configuration", dry_run=False)

    #all_devices.run(task=exporter.export_device_configuration)
    #all_devices.run(task=exporter.export_packet_filter_info)
    #all_devices.run(task=exporter.export_ipv4_routes)
    #all_devices.run(task=exporter.export_ipv6_routes)
    #exporter.export_device_facts(all_devices)
    #exporter.export_interfaces_packet_counters(all_devices)

    #configure_linux_servers(ubuntu_servers, linux_config.send_commands, task_name="Running commands", enable=True)
    #configure_linux_servers(ubuntu_servers, linux_config.configure_vsftpd, "VSFTPD Configuration", enable=True)
    # TODO show funkce (bez facts atd.), dokumentace (Linux, credentials handler, main), komentare a dokumentace k yamlum


if __name__ == "__main__":
    start = datetime.datetime.now()
    main()
    print("Time elapsed: " + str((datetime.datetime.now() - start)))
