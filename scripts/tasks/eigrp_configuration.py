from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_configure


class EIGRPConfiguration:
    """
    Třída pro konfiguraci EIGRP (IPv4 i IPv6).
    """
