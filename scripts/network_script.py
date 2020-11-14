import datetime
import logging
from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.functions import print_result


def main():
    nr = InitNornir(config_file="config.yml")

    # cisco = nr.filter(F(groups__contains='cisco_group'))
    # junos = nr.filter(F(groups__contains='junos_group'))
    # commands = [f"ping 192.168.122.{last_octet}" for last_octet in range(1, 10)]
    # results1 = cisco.run(task=napalm_cli, commands=commands)
    # results2 = junos.run(task=napalm_ping, dest="192.168.122.1")
    # print_result(results1)
    # print_result(results2)
    #routers = nr.filter(F(groups__contains='test'))
    #for ip in ["192.168.122.1", "192.168.122.2", "192.168.122.3"]:
    #    result = routers.run(task=napalm_ping, dest=ip)
    #    print_result(result)
    routers = nr.filter(F(groups__contains='cisco_group'))
    result = routers.run(task=napalm_get, getters=["facts"])
    print_result(result)


if __name__ == "__main__":
    start = datetime.datetime.now()
    main()
    print("Time elapsed: " + str((datetime.datetime.now() - start)))
