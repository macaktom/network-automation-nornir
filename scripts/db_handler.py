from datetime import datetime
from time import sleep
from typing import Dict, List
from colorama import Fore
from influxdb import InfluxDBClient
from nornir import InitNornir
from nornir.core import Task, Nornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.functions import print_title
from scripts.utility.credential_handler import CredentialHandler


def setup_inventory() -> Nornir:
    """
    Funkce, která umožňuje načíst veškeré informace o hostech a využívaných skupinách (groups). Podporuje dynamické načítání citlivých údajů (pouze pro citlivé údaje skupin).

    Returns:
        Nornir - nornir objekt, který obsahuje zparsované informace o hostech, skupinách. Dále zajišťuje multithreading funkcionalitu.
    """
    creds_handler = CredentialHandler()
    nr = InitNornir(
        config_file="config.yml")  # Nornir objekt, který přeskočí zařízení, které nezvládly požadovaný (sub)task. více o chybě v nornir.log

    # Nornir objekt, který zastavení všechny následující tasky, v případě, že došlo k chybě u tasku předchozího.
    # nr = InitNornir(config_file="config.yml", core={"raise_on_error": True})
    creds_handler.insert_creds(nr)
    return nr


class DBHandler:
    """
    Třida, která slouží jako rozhraní pro práci s InfluxDB. Používána např. pro pravidelný zápis NAPALM dat do DB nebo pro zjištění stavu stavu jednotlviých DB.

    Attributes:
        nr_obj (Nornir): Nornir objekt, umožňující volat paralelně nornir úkoly (tasky) a agregovat výsledky z jednotlivých tasků pro daná zařízení.

    """

    def __init__(self):
        self._nr_obj: Nornir = setup_inventory()

    def show_db_state(self, db_conn: InfluxDBClient) -> None:
        """
        Metoda pro zjištění stavu DB (databáze, measurements, datové body).

        Args:
            db_conn (InfluxDBClient): connection objekt, který slouží jako klient pro připojení k InfluxDB. Dále obsahuje operace pro práci s InfluxDB.

        Returns:
            None
        """

        print(f"{Fore.GREEN} List of databases:")
        print(db_conn.get_list_database())
        print(f"{Fore.GREEN} List of measurements:")
        print(db_conn.get_list_measurements())

        print(f"{Fore.GREEN} List of series:")
        print(db_conn.get_list_series())

        for measurement in db_conn.get_list_measurements():
            measurement_name = str(measurement['name'])
            print(f"{Fore.GREEN} Measurement: {measurement_name}")
            query = f"SELECT * FROM {measurement_name};"
            rs = db_conn.query(query)
            for row in list(rs.get_points(measurement=measurement_name)):
                print(row)

    def _get_measurement(self, napalm_key: str) -> str:
        """
        Metoda, která vrací název InfluxDB měření (measurement) dle napalm klíče (podle toho, co zrovna chceme zapsat do DB).

        Args:
            napalm_key (str): napalm klíč (dle použité NAPALM getter funkce)

        Returns:
            Vrací název InfluxDB měření (measurement).
        """
        if napalm_key == "environment":
            return "hw_details"
        elif napalm_key == "facts":
            return "device_facts"
        return ""

    def _get_monitored_fields_values(self, napalm_key: str, host_dict: Dict) -> Dict:
        """
        Metoda, která vrací jednotlivé sloupce (s daty) - fields, které budou uloženy do InfluxDB.

        Args:
            napalm_key (str): napalm klíč (dle použité NAPALM getter funkce)
            host_dict (Dict): nesparsovaný Python slovník, který obsahuje data, které byly získány pomocí NAPALM getteru (týká se konkrétního hosta).

        Returns:
            Vrací Python slovník, který vrací jednotlivé sloupce (s daty ) - fields. V případě prázdného host_dict nebo špatného napalm_klíče je vracen prázdný slovník.
        """
        fields_dict = {}
        if napalm_key == "environment" and host_dict:
            fields_dict['cpu_usage'] = host_dict['cpu'][0]['%usage']
            fields_dict['memory_used'] = host_dict['memory']['used_ram']
            fields_dict['memory_available'] = host_dict['memory']['available_ram']
        elif napalm_key == "facts" and host_dict:
            fields_dict['uptime'] = host_dict['uptime']
        return fields_dict

    def _write_to_db(self, host: str, measurement: str, fetch_time_utc: str, fields_dict: Dict, db_conn: InfluxDBClient) -> None:
        """
        Metoda, která slouží pro samotný zápis datových bodů do InfluxDB. Vypisuje informaci o (ne)úspěšném uložení datových bodů.

        Args:
            db_conn (InfluxDBClient): connection objekt, který slouží jako klient pro připojení k InfluxDB. Dále obsahuje operace pro práci s InfluxDB.
            measurement (str): název InfluxDB měření (measurement).
            fetch_time_utc (str): časové razítko (v UTC) - určuje kdy byla získána data pomocí NAPALM getterů.
            fields_dict (Dict): Python slovník, který obsahuje jednotlivé sloupce (s daty ) - fields.
            db_conn (InfluxDBClient): connection objekt, který slouží jako klient pro připojení k InfluxDB. Dále obsahuje operace pro práci s InfluxDB.

        Returns:
            None
        """
        is_saved = False
        if fields_dict:
            json_body = [
                {
                    "measurement": measurement,
                    "tags": {
                        "host": f"{host}"
                    },
                    "time": f"{fetch_time_utc}",
                    "fields": fields_dict
                }
            ]
            is_saved = db_conn.write_points(json_body)
        save_message = f"[{fetch_time_utc}] {host}: Measurement of {measurement} was successfuly saved." if is_saved and fields_dict else f"{Fore.RED}[{fetch_time_utc}] {host}: Measurement of {measurement} was not successfuly saved."
        print(save_message)

    def write_monitored_data(self, db_conn: InfluxDBClient) -> None:
        """
        Metoda, která slouží k pravidélnemu zápisu dat do InfluxDB. Zápis je prováděň v nekonečné smyččce.
        Ziskávání dat pomocí NAPALM getterů je prováděno +- každých 20s.

        Args:
            db_conn (InfluxDBClient): connection objekt, který slouží jako klient pro připojení k InfluxDB. Dále obsahuje operace pro práci s InfluxDB.

        Returns:
            None
        """
        while True:
            aggregated_result = self._nr_obj.run(task=napalm_get, name="Get env_details and device facts", getters=["environment", "facts"])
            data_fetch_time_utc = str(datetime.utcnow())
            for host in aggregated_result:
                if host not in aggregated_result.failed_hosts:
                    for key, result_dict in aggregated_result[host].result.items():
                        measurement = self._get_measurement(key)
                        fields = self._get_monitored_fields_values(key, result_dict)
                        self._write_to_db(host, measurement, data_fetch_time_utc, fields, db_conn)
                else:
                    print(f"{Fore.RED}[{data_fetch_time_utc}] {host}: Failure during data collection (using NAPALM getters). Device is not probably supported by used NAPALM getter.")
            sleep(10)

    def drop_db_measurements(self, db_conn: InfluxDBClient, measurements: List[str]) -> None:
        """
        Metoda, která slouží k mazání InfluxDB měření (včetně všech dat, která jsou součástí daného měření).

        Args:
            db_conn (InfluxDBClient): connection objekt, který slouží jako klient pro připojení k InfluxDB. Dále obsahuje operace pro práci s InfluxDB.
            measurements (List[str]): list, obsahující jednotliva InfluxDB měření (measurement).

        Returns:
            None
        """
        for measurement in measurements:
            db_conn.drop_measurement(measurement)


if __name__ == '__main__':
    db_nornir_conn = InfluxDBClient(host='10.10.10.10', port=8086, username='monitoring', password='monitoring',
                                     database='monitoring_nornir')
    db_ansible_conn = InfluxDBClient(host='10.10.10.10', port=8086, username='monitoring', password='monitoring',
                                      database='monitoring_ansible')
    db_telegraf_conn = InfluxDBClient(host='10.10.10.10', port=8086, username='monitoring', password='monitoring',
                                     database='monitoring_telegraf')
    db_writer = DBHandler()
    # Zakomentujte následující řádek, pokud chcete pouze zobrazit stav databází pro Nornir a Ansible projekty.
    db_writer.write_monitored_data(db_nornir_conn)

    #db_writer.drop_db_measurements(db_nornir_conn, ['hw_details', 'device_facts'])
    #db_writer.drop_db_measurements(db_ansible_conn, ['hw_details', 'device_facts'])
    #db_writer.drop_db_measurements(db_telegraf_conn, ['cpu', 'mem', 'system'])

    print_title("Ansible DB info")
    db_writer.show_db_state(db_ansible_conn)
    print_title("Nornir DB info ")
    db_writer.show_db_state(db_nornir_conn)
    print_title("Telegraf DB info ")
    db_writer.show_db_state(db_telegraf_conn)

