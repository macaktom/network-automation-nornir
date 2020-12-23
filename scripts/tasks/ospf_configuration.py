from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result


class OSPFConfiguration:
    """
    Třída pro konfiguraci OSPF a OSPFv3.
    """

    def configure_ospf(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci OSPFv2.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="OSPF Template Loading",
                     template="ospf_ipv4.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     ospf_config=task.host["ospf_config"])

        task.host["ipv4_ospf"] = r.result

        task.run(task=napalm_configure,
                 name="Loading OSPFv2 Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv4_ospf"],
                 dry_run=dry_run)

    def configure_ospfv3(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci OSPFv3.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="OSPF Template Loading",
                     template="ospfv3.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     ospfv3_config=task.host["ospfv3_config"])

        task.host["ipv6_ospf"] = r.result

        task.run(task=napalm_configure,
                 name="Loading OSPFv3 Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv6_ospf"],
                 dry_run=dry_run)
