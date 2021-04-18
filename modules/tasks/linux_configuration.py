import logging
from pathlib import Path
from typing import List, Dict, Union
from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_jinja2.plugins.tasks import template_file
from nornir_netmiko import netmiko_send_command, netmiko_file_transfer
from nornir_utils.plugins.functions import print_result, print_title
from nornir_utils.plugins.tasks.data import load_yaml

from modules.utility.text_file_exporter import FileExporter


class LinuxConfiguration:
    """
    Třída pro konfigurování Linux serverů. Konfigurace VSFTPD implementována pouze pro linuxovou distribuci Ubuntu (18.04).
    """

    def send_commands(self, task: Task, commands: List[str] = None, enable: bool = False) -> None:
        """
        Metoda, která slouží pro vykonání příkazů linuxovými servery pomocí knihovny Netmiko.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            commands (List[str]): Příkazy, které budou provedeny. Defaultně None (příkazy jsou obdrženy z inventáře).
            enable (bool): Argument, kterým lze specifikovat, jestli je nutný pro daný nornir úkol práv superuživatele (rootu). Defaultně je nastaveno na True (root práva).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud nastana chyba v nornir úkolu nebo pokud provádíte
                konfiguraci na nepodporovaných zařízeních.

        Returns:
            None
        """
        if task.host.platform == "linux":
            if commands is None:
                data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                                severity_level=logging.DEBUG)
                commands_key = "commands"
                if commands_key in data[0].result:
                    commands = data[0].result[commands_key]
                    print_title(f"Device {task.host.name}:")
                    for command in commands:
                        res = task.run(task=netmiko_send_command, command_string=command, enable=enable)
                        print(res[0].result)
                else:
                    print(f"{Fore.RED}Device {task.host.name}: Command list is empty.")
            else:
                print_title(f"Device {task.host.name}:")
                for command in commands:
                    res = task.run(task=netmiko_send_command, command_string=command, enable=enable)
                    print(res[0].result)
        else:
            print(f"{Fore.RED}Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only Linux servers are supported.", task)

    def configure_vsftpd(self, task: Task, enable: bool = True) -> None:
        """
        Metoda, která slouží pro konfiguraci vsftpd serveru (S)FTP.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).
            enable (bool): Argument, kterým lze specifikovat, jestli je nutný pro daný nornir úkol práv superuživatele (rootu). Defaultně je nastaveno na True (root práva).

        Raises:
            NornirSubTaskError: Výjimka, která nastane, pokud nastana chyba v nornir úkolu nebo pokud provádíte
                konfiguraci na nepodporovaných zařízeních. Podporovány jsou pouze ubuntu servery.

        Returns:
            None
        """
        if task.host["dev_type"] == "ubuntu_server":
            print_title(f"Device {task.host.name}:")
            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            vsftpd_key = "vsftpd_config"

            if vsftpd_key in data[0].result:
                task.host[vsftpd_key] = data[0].result[vsftpd_key]

                commands = data[0].result[vsftpd_key]["commands"]
                r = task.run(task=template_file,
                             name="VSFTPD configuration Template Loading",
                             template="vsftpd.j2",
                             path=f"templates/{task.host['vendor']}/{task.host['dev_type']}",
                             severity_level=logging.DEBUG)
                if not r.failed:
                    file_path = Path(Path.cwd() / 'export' / "configuration" / "vsftpd.conf")
                    exporter = FileExporter(file_path, content=r.result)
                    exporter.export_to_file()
                    for command in commands:
                        if command == "scp":
                            task.run(task=netmiko_file_transfer, source_file=file_path, dest_file=f"{file_path.name}",
                                     severity_level=logging.DEBUG)
                            task.run(task=netmiko_send_command, command_string=f"mv /var/tmp/vsftpd.conf /etc/",
                                     enable=enable, severity_level=logging.DEBUG)
                            task.run(task=netmiko_send_command, command_string=f"chown root:root /etc/vsftpd.conf",
                                     enable=enable, severity_level=logging.DEBUG)
                        else:
                            task.run(task=netmiko_send_command, command_string=command, enable=enable,
                                     severity_level=logging.DEBUG)
            else:
                print(f"{Fore.RED}Device {task.host.name}: No {vsftpd_key} key was found in host data.")
        else:
            print(f"{Fore.RED}Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only Ubuntu servers are supported.", task)