from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class EIGRPConfiguration:
    """
    Třída pro konfiguraci EIGRP (IPv4 i IPv6).
    """

    def configure_eigrp_ipv4(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 EIGRP.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="EIGRP IPv4 Template Loading",
                     template="eigrp_ipv4.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     eigrp_config=task.host["eigrp_config"])

        task.host["ipv4_eigrp"] = r.result

        task.run(task=napalm_configure,
                 name="Loading EIGRP IPv4 Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv4_eigrp"],
                 dry_run=dry_run)

    def configure_eigrp_ipv6(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 EIGRP.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="EIGRP IPv6 Template Loading",
                     template="eigrp_ipv6.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     eigrp_ipv6_config=task.host["eigrp_ipv6_config"])

        task.host["ipv6_eigrp"] = r.result

        task.run(task=napalm_configure,
                 name="Loading EIGRP IPv6 Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv6_eigrp"],
                 dry_run=dry_run)
