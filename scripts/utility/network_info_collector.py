from nornir.core import task
from nornir.core.task import AggregatedResult, Result, Task, MultiResult
from nornir_napalm.plugins.tasks import napalm_get


class NetworkInfoCollector:
    """
    Třída, která sbírá informace ze síťových zařízení a provádí jejích agregaci (seskupení výsledků pro každé síťové zařízení,
    které je definováno v Task objektu).
    """

    def _get_conn_state_result(self, task: Task) -> Result:
        """
        Metoda, která vrácí informaci o stavu připojení k danému síťovému zařízení.
        Nornir tuto metodu volá paralelně pro síťová zařízení definována v Nornir objektu (pomocí něho se volá tato metoda).

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir úkoly (funkce).

        Returns:
            Result objekt, který obsahuje informace o stavu připojení k danému síťovému zařízení a o úspěchu provedeného nornir úkolu.

        """
        napalm = task.host.get_connection("napalm", task.nornir.config)
        result = napalm.is_alive()
        return Result(host=task.host, result=result)

    def get_conn_state_and_device_facts(self, task: Task) -> MultiResult:
        """
        Metoda, která vrací data o stavu připojení k síťovým zařízením a základních údajích o těchto zařízeních.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir ůkoly (funkce).

        Returns:
            Metoda vrací pro konkrétního hosta MultiResult objekt (speciální nornir objekt připomínající Python list, který obsahuje Result objekty s výsledky jednotlivých tasků).
            Pokud více hostů zavolá tuto metodu, tak se výsledky seskupí do jednoho AggregatedResult objektu obsahující výsledky všech hostů.
            AggregatedResult si lze představit jako slovník, jejichž klíčem jsou jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků.

        """
        result = task.run(task=napalm_get, name="Get device basic facts", getters=["facts"])
        result += task.run(task=self._get_conn_state_result, name="Get conn status")
        return result

    def get_interfaces_packet_counters(self, task: Task) -> MultiResult:
        """
        Metoda, která vrací statistiky týkající se přijímání a vysílání paketů pro jednotlivá rozhraní síťových zařízení.

        Args:
            task (Task): Task objekt, umožňující paralelně volat a seskupovat další nornir ůkoly (funkce).

        Returns:
            Metoda vrací pro konkrétního hosta MultiResult objekt (speciální nornir objekt připomínající Python list, který obsahuje Result objekty s výsledky jednotlivých tasků).
            Pokud více hostů zavolá tuto metodu, tak se výsledky seskupí do jednoho AggregatedResult objektu obsahující výsledky všech hostů.
            AggregatedResult si lze představit jako slovník, jejichž klíčem jsou jednotlivé síťové zařízení (hosti) a hodnotou jsou výsledky z jednotlivých tasků.

        """
        result = task.run(task=napalm_get, name="Get interfaces packet counters", getters=["interfaces_counters"])
        return result

    def get_device_configuration(self, task: Task) -> MultiResult:
        result = task.run(task=napalm_get, name="Get configuration", getters=["config"])
        return result
