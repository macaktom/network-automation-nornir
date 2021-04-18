from copy import deepcopy
from pathlib import Path
from typing import List, Tuple, Dict
from ansible.parsing.vault import VaultLib
from ansible.cli import CLI
from ansible.parsing.dataloader import DataLoader
import yaml
from nornir.core import Nornir


class CredentialHandler:
    """
    Pomocná třída, která rozšiřuje defaultní parsování YAML inventáře.
    Stará se o dešifrování citlivých údajů (username, password, secret - zašifrované pomocí Ansible Vault) a jejich parsování.

    Attributes:
         credentials (Dict[str, Dict[str, str]]): dynamicky zparsované údaje ze zašifrovaného souboru (vaultu).

    """

    def __init__(self):
        self._credentials = self._get_unencrypted_creds()

    def _get_unencrypted_creds(self) -> Dict[str, Dict[str, str]]:
        """
        Metoda, která slouží k získání citlivých dat z ansible vault souboru.

        Returns:
            Dict[str, Dict[str, str]] - slovník slovníků, který obsahuje dešifrované citlivé údaje.
        """
        enrypted_file_path = str(Path(Path.cwd() / 'inventory' / "vault" / "creds.yml"))
        password_file = str(Path(Path.cwd() / 'inventory' / "vault" / ".vault_pass"))
        result = self._decrypt_vault(encrypted_file=enrypted_file_path, vault_password_file=password_file)
        return dict(result)

    def _get_group_credentials(self, group: str) -> Tuple[str, str, str]:
        """
        Metoda, která slouží k získání konkrétních citlivých dat (username, password, secret) dané skupiny (groupy).

        Args:
            group (str): jméno skupiny

        Returns:
            Tuple[str, str, str] - Tuple, který obsahuje citlivé data konkrétní skupiny.
        """
        username = None
        password = None
        secret = None
        if group in self._credentials:
            username = self._credentials[group].get('username', None)
            password = self._credentials[group].get('password', None)
            secret = self._credentials[group].get('secret', None)
        return username, password, secret

    def _get_encrypted_inventory_groups(self) -> List[str]:
        """
        Metoda, která slouží k získání listu šifrovaných skupin.

        Returns:
            List[str] - Metoda vrací list šifrovaných skupin (jako string).
        """
        return list(self._credentials.keys())

    def _decrypt_vault(self, encrypted_file: str, vault_password_file: str) -> Dict:
        """
        Metoda, která slouží k dešifrování zašifrováno souboru (Ansible Vault souboru).

        Args:
            encrypted_file (str): cesta k zašifrovanému souboru.
            vault_password_file (str): cesta k souboru s vault heslem.
        Returns:
            parsed_byte_string (Dict) - strukturované data z dešifrovaného souboru
        """
        loader = DataLoader()
        vault_secret = CLI.setup_vault_secrets(loader=loader, vault_ids=[vault_password_file])
        vault = VaultLib(vault_secret)

        with open(encrypted_file) as file:
            unencrypted_byte_string = vault.decrypt(file.read())
            parsed_byte_string = yaml.safe_load(unencrypted_byte_string)
            return parsed_byte_string

    def insert_creds(self, nornir_obj: Nornir) -> None:
        """
        Metoda, která slouží k dynamickému vkládání dešifrovaných citlivých údajů do zparsovaného inventáře nornir objektu.

        Args:
            nornir_obj (Nornir): Nornir objekt, který vlastní zparsovaný inventář.
        Returns:
            None
        """
        credential_sets = self._get_encrypted_inventory_groups()
        for group_name, group_obj in nornir_obj.inventory.groups.items():
            if group_name in credential_sets:
                username, password, secret = self._get_group_credentials(group_name)
                group_obj.username = username
                group_obj.password = password
                if secret and group_name != "juniper":
                    netmiko_params = group_obj.get_connection_parameters("netmiko")
                    extras = deepcopy(netmiko_params.extras)
                    extras["secret"] = secret
                    netmiko_params.extras = extras
                    group_obj.connection_options["netmiko"] = netmiko_params
                    if group_name == "cisco":
                        napalm_params = group_obj.get_connection_parameters("napalm")
                        extras = deepcopy(napalm_params.extras)
                        extras["optional_args"]["secret"] = secret
                        napalm_params.extras = extras
                        group_obj.connection_options["napalm"] = napalm_params

