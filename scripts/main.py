import datetime

from colorama import Fore
from nornir import InitNornir
from nornir.core import Task
from nornir.core.filter import F
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from scripts.utility.network_info_exporter import NetworkInfoExporter
from scripts.utility.network_info_viewer import NetworkUtilityViewer


# Rozdelit SHOW commandy:
# 1) Ty ktere jsou podporovany NAPALMem u OBOU vendoru (nutne udelat specialni tabulku pro printovani) - lze provest export do JSONu, .txt
# 2) Ty ktere NAPALM nema nebo jsou podporovany pouze u nektereho vendora - print pouze neupraveneho textu do konzole + export .txt
# Tři druhy metod teď budou (kromě potom Jinja2): GET, SHOW, EXPORT. Show commandy je ted nutne prepsat na GET commandy, vraci Resulty

# TODO pokud bude cas: Export HTML: show_vlans, show_interfaces_basic_info, show_intefaces_ip_info, Excel: mozna show_interfaces_packet_counters


def configure_ipv4_interfaces(task: Task):
    """
    Cool function
    Args:
        task(Task): typte Task

    Returns:
        None

    """
    r = task.run(task=template_file,
                 name="IPv4 Intefaces Configuration",
                 template="interfaces_ipv4.j2",
                 path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                 interfaces_ipv4=task.host["interfaces_ipv4"])

    # Save the compiled configuration into a host variable
    task.host["ipv4_interfaces"] = r.result

    # Deploy that configuration to the device using NAPALM
    task.run(task=napalm_configure,
             name="Loading Configuration on the device",
             replace=False,
             configuration=task.host["ipv4_interfaces"])


def main():
    # nr = InitNornir(config_file="config.yml", core = {"raise_on_error": True}) # Nornir objekt, který upozorní na chybu při provedení tasku
    nr = InitNornir(
        config_file="config.yml")  # Nornir objekt, který přeskočí hosty, které nezvládli požadovaný task - více o chybě v nornir.log
    routers = nr.filter(F(dev_type="router"))
    l3_switches = nr.filter(F(dev_type="L3_switch"))
    l3_cisco = nr.filter(F(groups__contains="cisco_group") & F(dev_type="router") | F(dev_type="L3_switch"))
    all_devices = nr.filter(F(dev_type="router") | F(dev_type="L3_switch"))
    viewer = NetworkUtilityViewer()
    exporter = NetworkInfoExporter()
    #all_devices.run(task=viewer.show_vlans)
    z = all_devices.run(task=exporter.export_ipv6_routes)
    # print(z['R1'][1].result['facts'])
    # print(z['R1'][2].result)

    # exporter_xlsx = ExcelExporter(Workbook(), "Testa")
    # z = all_devices.run(task=exporter_xlsx.get_conn_state_and_device_facts)


# TODO 1.12 - Prazdne soubory pri exportovani - u ipv4 a ipv6 ip routes nevytvaret, dopsat excel exporter, zacit configuration
if __name__ == "__main__":
    try:
        start = datetime.datetime.now()
        main()
        print("Time elapsed: " + str((datetime.datetime.now() - start)))
    except Exception as err:
        print(f'{Fore.RED}Error occured during script execution!!!')
        print(err)
