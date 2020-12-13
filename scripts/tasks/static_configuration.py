from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class StaticRoutingConfiguration:
    """
    Třída pro konfiguraci statického směrování (IPv4 i IPv6).
    """

    def configure_static_routing_ipv4(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 statického směrování.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="IPv4 Static Routing Template Loading",
                     template="static_ipv4.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     static_routing_config=task.host["static_routing_config"])

        task.host["ipv4_static"] = r.result

        task.run(task=napalm_configure,
                 name="Loading IPv4 Static Routing Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv4_static"],
                 dry_run=dry_run)

    def configure_static_routing_ipv6(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 statického směrování.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="IPv6 Static Routing Template Loading",
                     template="static_ipv6.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     static_routing_ipv6_config=task.host["static_routing_ipv6_config"])

        task.host["ipv6_static"] = r.result

        task.run(task=napalm_configure,
                 name="Loading IPv6 Static Routing Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv6_static"],
                 dry_run=dry_run)