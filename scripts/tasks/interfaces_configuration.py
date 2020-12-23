from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class InterfacesConfiguration:
    """
    Třída pro konfiguraci jednotlivých rozhraní daných zařízení (např: přidělení IPv4, IPv6 adres, popisu,
    konfigurace switchovaných a routovaných portů).
    """

    def configure_ipv4_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv4 rozhraní.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        result = task.run(task=template_file,
                          name="IPv4 Intefaces Configuration",
                          template="interfaces_ipv4.j2",
                          path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                          interfaces_ipv4=task.host["interfaces_ipv4"])

        task.host["ipv4_interfaces"] = result.result

        task.run(task=napalm_configure,
                 name="Loading IPv4 interfaces Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv4_interfaces"],
                 dry_run=dry_run)

    def configure_ipv6_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci IPv6 rozhraní.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        r = task.run(task=template_file,
                     name="IPv6 Intefaces Configuration",
                     template="interfaces_ipv6.j2",
                     path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                     interfaces_ipv6=task.host["interfaces_ipv6"])

        task.host["ipv6_interfaces"] = r.result

        task.run(task=napalm_configure,
                 name="Loading IPv6 interfaces Configuration on the device",
                 replace=False,
                 configuration=task.host["ipv6_interfaces"],
                 dry_run=dry_run)

    def configure_switching_interfaces(self, task: Task, dry_run: bool = False) -> None:
        """
        Metoda pro konfiguraci přepínacích portů.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            dry_run (bool): argument, který rozhoduje, jestli má být konfigurace provedena v testovacím režimu
                            (obdržení konečných změn v konfiguraci bez jejich uložení do zařízení) - True. Defaultně False - uložení konečných změn.

        Returns:
            None
        """
        if task.host["dev_type"] == "L3_switch" or task.host["dev_type"] == "switch":

            interfaces_result = task.run(task=template_file,
                                         name="Switching Intefaces Configuration",
                                         template="switching_interfaces.j2",
                                         path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                                         switching_interfaces=task.host["switching_interfaces"],
                                         vlans_config=task.host["vlans_config"])

            task.host["switching_interfaces_config"] = interfaces_result.result

            task.run(task=napalm_configure,
                     name="Loading Switching Interfaces Configuration on the device",
                     replace=False,
                     configuration=task.host["switching_interfaces_config"],
                     dry_run=dry_run)
        else:
            raise NornirSubTaskError("Invalid device type. Only switches are supported.", task)
