import datetime
import time

from colorama import Fore
from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.exceptions import NornirSubTaskError, NornirExecutionError
from nornir.core.filter import F
from nornir_netmiko import netmiko_send_command
from nornir_utils.plugins.functions import print_result, print_title
from modules.tasks.delete_configuration import DeleteConfiguration
from modules.tasks.eigrp_configuration import EIGRPConfiguration
from modules.tasks.interfaces_configuration import InterfacesConfiguration
from modules.tasks.linux_configuration import LinuxConfiguration
from modules.tasks.nat_configuration import NATConfiguration
from modules.tasks.ospf_configuration import OSPFConfiguration
from modules.tasks.packet_filter_configuration import PacketFilterConfiguration
from modules.tasks.static_configuration import StaticRoutingConfiguration
from modules.utility.credential_handler import CredentialHandler
from modules.utility.network_info_collector import NetworkInfoCollector
from modules.utility.network_info_exporter import NetworkInfoExporter
from modules.utility.network_info_viewer import NetworkUtilityViewer


def setup_inventory() -> Nornir:
    """
    Funkce, která umožňuje načíst veškeré informace o hostech a využívaných skupinách (groups). Podporuje dynamické načítání citlivých údajů (pouze pro citlivé údaje skupin).

    Returns:
        Nornir - nornir objekt, který obsahuje zparsované informace o hostech, skupinách. Dále zajišťuje multithreading funkcionalitu.
    """
    nr = InitNornir(config_file="config.yml")  # Nornir objekt, který přeskočí zařízení, které nezvládly požadovaný (sub)task. více o chybě v nornir.log

    # Nornir objekt, který zastavení všechny následující tasky, v případě, že došlo k chybě u tasku předchozího.
    # nr = InitNornir(config_file="config.yml", core={"raise_on_error": True})  # Nornir objekt, který přeskočí hosty, které nezvládli požadovaný (sub)task - více o chybě v nornir.log
    creds_handler = CredentialHandler()
    creds_handler.insert_creds(nr)
    return nr


def configure_network_devices(nornir_devices: Nornir, task_func: callable, task_name: str, dry_run: bool) -> None:
    """
    Wrapper funkce, která slouží pro konfiguraci síťových zařízení (routerů, switchů). Funkce obaluje specifikovaný nornir úkol (task_func), který se týká konfigurace síťových prvků.

    Args:
        nornir_devices (Nornir): Nornir objekt, umožňující volat paralelně nornir úkoly (tasky) a agregovat výsledky z jednotlivých tasků pro daná zařízení. Obsahuje zparsovaný inventář.
        task_func (callable): Funkce, která bude paralelně vykonávaná nornirem.
        task_name (str): Název nornir úkolu
        dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.
    Returns:
        None
    """
    result = nornir_devices.run(task=task_func, name=task_name, dry_run=dry_run)
    print_result(result)


def main() -> None:
    """
    Hlavní funkce skriptu, která se zavolá po spuštění skriptu main.py

    Returns:
        None
    """
    # Parsování inventáře
    nornir_obj = setup_inventory()

    # Filtrování Nornir objektů
    routers = nornir_obj.filter(F(dev_type="router"))
    juniper_devices = nornir_obj.filter(F(groups__contains="juniper"))
    l3_switches = nornir_obj.filter(F(dev_type="L3_switch"))
    cisco_routers = nornir_obj.filter(F(groups__contains="cisco") & F(dev_type="router"))
    l3_cisco = nornir_obj.filter(F(groups__contains="cisco") & F(dev_type="router") | F(dev_type="L3_switch"))
    l3_devices = nornir_obj.filter(F(dev_type="router") | F(dev_type="L3_switch"))
    ubuntu_servers = nornir_obj.filter(F(dev_type="ubuntu_server") | F(groups__contains="linux"))
    mls1 = nornir_obj.filter(F(name__contains="MLS1"))
    mls1_r3 = nornir_obj.filter(F(name__contains="MLS1") | F(name__contains="R3"))

    viewer = NetworkUtilityViewer()
    exporter = NetworkInfoExporter(NetworkInfoCollector())

    # Inicializace Configuration objektů
    ospf_config = OSPFConfiguration()
    eigrp_config = EIGRPConfiguration()
    static_routing_config = StaticRoutingConfiguration()
    interfaces_configuration = InterfacesConfiguration()
    packet_filter = PacketFilterConfiguration()
    linux_config = LinuxConfiguration()
    nat_config = NATConfiguration()
    delete_config = DeleteConfiguration()
    static_routing_config = StaticRoutingConfiguration()

    # Příklady konfigurace síťových zařízení
    configure_network_devices(l3_devices, interfaces_configuration.configure_ipv4_interfaces, "IPv4 interfaces config",dry_run=False)
    configure_network_devices(l3_devices, interfaces_configuration.configure_ipv6_interfaces, "IPv6 interfaces config",dry_run=False)
    configure_network_devices(l3_switches, interfaces_configuration.configure_switching_interfaces,"Switching interfaces config", dry_run=False)
    configure_network_devices(routers, ospf_config.configure_ospf, "OSPFv2 config", dry_run=False)
    configure_network_devices(routers, ospf_config.configure_ospfv3, "OSPFv3 config", dry_run=False)
    configure_network_devices(mls1_r3, eigrp_config.configure_eigrp_ipv4, "EIGRP config", dry_run=False)
    configure_network_devices(mls1_r3, eigrp_config.configure_eigrp_ipv6, "EIGRP IPV6 config", dry_run=False)
    configure_network_devices(mls1, packet_filter.configure_ipv4_packet_filters, "IPv4 packet filter config",dry_run=False)
    configure_network_devices(mls1, packet_filter.configure_ipv6_packet_filters, "IPv6 packet filter config",dry_run=False)

    # Mazání konfigurace
    # configure_network_devices(l3_devices, delete_config.delete_configuration, "Delete Configuration", dry_run=False)

    # Sběr a výpis dat
    l3_switches.run(task=viewer.show_vlans, json_out=False)
    l3_switches.run(task=viewer.show_vlans, json_out=True)
    l3_devices.run(task=viewer.show_ospf_neighbors, ipv6=True)

    # Export dat
    l3_devices.run(task=exporter.export_device_configuration)
    l3_devices.run(task=exporter.export_packet_filter_info)
    l3_devices.run(task=exporter.export_ipv4_routes)
    l3_devices.run(task=exporter.export_ipv6_routes)

    # Tvorba Excel reportů
    exporter.export_device_facts(l3_devices)
    exporter.export_interfaces_packet_counters(l3_devices)

    # Konfigurace Ubuntu serveru
    ubuntu_servers.run(task=linux_config.send_commands, enable=True)
    ubuntu_servers.run(task=linux_config.configure_vsftpd, enable=True)


if __name__ == "__main__":
    try:
        main()
    except (NornirSubTaskError, NornirExecutionError) as err:
        print_title("Failed hosts - more in nornir.log:")
        for host in err.failed_hosts:
            host_tasks_name = []
            print(f"{Fore.RED}{host}: Nornir (sub)tasks failed: ", sep="")
            for task in err.failed_hosts[host]:
                if task.name not in host_tasks_name:
                    host_tasks_name.append(task.name)
                    print(f"{task.name}", sep=", ")
