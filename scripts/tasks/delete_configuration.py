from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class DeleteConfiguration:
    """
    Třída pro smazání specifických částí konfigurace daných zařízení.
    """

    def delete_configuration(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro mazání konfigurace dle definovaného YAML mappingu (slovníku) delete_config.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="Delete Configuration Template Loading",
                     template="delete_configuration.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     delete_config=task.host["delete_config"])

        task.host["conf_delete"] = r.result

        task.run(task=napalm_configure,
                 name="Loading Delete Configuration on the device",
                 replace=False,
                 configuration=task.host["conf_delete"],
                 dry_run=dry_run)
