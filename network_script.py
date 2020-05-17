import datetime
from nornir import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command


def main():
    nr = InitNornir(config_file="config.yml", dry_run=True)
    results = nr.run(task=netmiko_send_command, command_string="ping 10.0.0.1", use_timing=False)
    print_result(results)


if __name__ == "__main__":
    start = datetime.datetime.now()
    main()
    print("Time elapsed: " + str((datetime.datetime.now() - start)))
