from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class NATConfiguration:
    """
    Třída pro konfiguraci překládání síťových adres (NAT).
    """

    def configure_source_nat_overload(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci zdrojového NAT Overloadu.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="NAT Overload Configuration",
                     template="source_nat_overload.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     nat_overload_config=task.host["nat_overload_config"])

        task.host["nat_overload"] = r.result

        task.run(task=napalm_configure,
                 name="Loading NAT Overload Configuration on the device",
                 replace=False,
                 configuration=task.host["nat_overload"],
                 dry_run=dry_run)
