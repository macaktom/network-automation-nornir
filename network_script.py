import datetime
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import napalm_cli, napalm_get
from nornir.plugins.tasks.networking import napalm_ping


def main():
    nr = InitNornir(config_file="config.yml")
    # cisco = nr.filter(F(groups__contains='cisco_group'))
    # junos = nr.filter(F(groups__contains='junos_group'))
    # commands = [f"ping 192.168.122.{last_octet}" for last_octet in range(1, 10)]
    # results1 = cisco.run(task=napalm_cli, commands=commands)
    # results2 = junos.run(task=napalm_ping, dest="192.168.122.1")
    # print_result(results1)
    # print_result(results2)

    cisco = nr.filter(F(groups__contains='cisco_group') and F(groups__contains='test'))
    result = cisco.run(napalm_ping, dest="192.168.122.1")
    print_result(result)


if __name__ == "__main__":
    start = datetime.datetime.now()
    main()
    print("Time elapsed: " + str((datetime.datetime.now() - start)))
