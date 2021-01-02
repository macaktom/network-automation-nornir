import datetime
import logging
import ssl
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import List, Dict, Union

from colorama import Fore
from nornir.core import Task
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import Result
from nornir_jinja2.plugins.tasks import template_file
from nornir_netmiko import netmiko_send_command, netmiko_file_transfer
from nornir_utils.plugins.functions import print_result, print_title
from nornir_utils.plugins.tasks import files
from nornir_utils.plugins.tasks.data import load_yaml

from scripts.utility.text_file_exporter import FileExporter


class LinuxConfiguration:

    def send_commands(self, task: Task, commands: List[str] = None, enable: bool = False) -> None:
        if commands is None:
            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            if not data.failed and data[0].result["commands"]:
                commands = data[0].result["commands"]
            else:
                print(f"{Fore.RED}Device {task.host.name}: Command list is empty or task failed. More in nornir.log.")

        if task.host.platform == "linux":
            print_title(f"Device {task.host.name}:")
            for command in commands:
                task.run(task=netmiko_send_command, command_string=command, enable=enable)
        else:
            print(f"{Fore.RED}Device {task.host.name}: Not a Linux server.")

    def configure_vsftpd(self, task: Task, enable: bool = True) -> None:
        if task.host["dev_type"] == "ubuntu_server":
            print_title(f"Device {task.host.name}:")
            data = task.run(task=load_yaml, file=f'inventory/host_vars/{task.host.name}.yml', name="Load host data",
                            severity_level=logging.DEBUG)
            task.host["vsftpd_config"] = data[0].result["vsftpd_config"]
            ssl_enabled = data[0].result["vsftpd_config"]["ssl"]["enabled"]
            ftp_testing = data[0].result["vsftpd_config"]["testing"]
            ftp_testing["ssl"] = ssl_enabled
            commands = data[0].result["vsftpd_config"]["commands"]
            r = task.run(task=template_file,
                         name="VSFTPD configuration Template Loading",
                         template="vsftpd.j2",
                         path=f"templates/{task.host.platform}/{task.host['dev_type']}",
                         severity_level=logging.DEBUG)
            if not r.failed:
                file_path = Path(Path.cwd() / 'export' / "configuration" / "vsftpd.conf")
                exporter = FileExporter(file_path, content=r.result)
                exporter.export_to_file()
                for command in commands:
                    if command == "scp":
                        task.run(task=netmiko_file_transfer, source_file=file_path, dest_file=f"{file_path.name}", severity_level=logging.DEBUG)
                        task.run(task=netmiko_send_command, command_string=f"mv /var/tmp/vsftpd.conf /etc/", enable=enable, severity_level=logging.DEBUG)
                        task.run(task=netmiko_send_command, command_string=f"chown root:root /etc/vsftpd.conf", enable=enable, severity_level=logging.DEBUG)
                    else:
                        task.run(task=netmiko_send_command, command_string=command, enable=enable, severity_level=logging.DEBUG)
                task.run(task=self._testing_vsftpd, name="VSFTPD Testing", ftp_data=ftp_testing)
        else:
            print(f"{Fore.RED} Device {task.host.name}: invalid device type.")
            raise NornirSubTaskError("Invalid device type. Only Ubuntu servers and L3 switches are supported.", task)

    def _testing_vsftpd(self, task: Task, ftp_data: Dict[str, Union[str, bool]]):
        ssl_enabled = ftp_data["ssl"]
        base_directory = ftp_data["base_directory"]
        ftp = FTP_TLS(f"{ftp_data['host']}") if ssl_enabled else FTP(f"{ftp_data['host']}")
        with ftp:
            ftp.login(user=f"{ftp_data['user']}", passwd=f"{ftp_data['password']}")
            if ssl_enabled:
                ftp.ssl_version = ssl.PROTOCOL_TLSv1
                ftp.prot_p()
            ftp.login(user=f"{ftp_data['user']}", passwd=f"{ftp_data['password']}")
            if base_directory:
                ftp.cwd(base_directory)
            if ftp_data["test_folder"] not in ftp.nlst():
                ftp.mkd(f"{ftp_data['test_folder']}")
            files = []
            ftp.dir(files.append)
            return Result(host=task.host, result="\n".join(files))


