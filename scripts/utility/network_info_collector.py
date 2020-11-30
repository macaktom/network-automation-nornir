import datetime
import re

from nornir.core.task import AggregatedResult, Result, Task, MultiResult
from nornir_napalm.plugins.tasks import napalm_get


class NetworkInfoCollector:

    def _get_conn_state_result(self, task: Task) -> Result:
        napalm = task.host.get_connection("napalm", task.nornir.config)
        result = napalm.is_alive()
        return Result(host=task.host, result=result)

    def get_conn_state_and_device_facts(self, task: Task) -> AggregatedResult:
        result = task.run(task=napalm_get, name="Get device basic facts", getters=["facts"])
        result += task.run(task=self._get_conn_state_result, name="Get conn status")
        return AggregatedResult(*result)
