from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class PacketFilterConfiguration:
    """
    Třída pro konfiguraci paketových filtrů.
    """

    def configure_ipv4_packet_filters(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 paketového filtru.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="IPv4 Packet filter Configuration",
                     template="packet_filter_ipv4.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     packet_filter_config=task.host["packet_filter_config"])

        task.host["ipv4_packet_filter"] = r.result

        task.run(task=napalm_configure,
                 name="Loading IPv4 Packet Filter Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv4_packet_filter"],
                 dry_run=dry_run)

    def configure_ipv6_packet_filters(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 paketového filtru.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="IPv6 Packet filter Configuration",
                     template="packet_filter_ipv6.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     packet_filter_ipv6_config=task.host["packet_filter_ipv6_config"])

        task.host["ipv6_packet_filter"] = r.result

        task.run(task=napalm_configure,
                 name="Loading IPv6 Packet Filter Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv6_packet_filter"],
                 dry_run=dry_run)