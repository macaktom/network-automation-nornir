from copy import deepcopy
from pathlib import Path
from ansible.parsing.vault import VaultLib
from ansible.cli import CLI
from ansible.parsing.dataloader import DataLoader
import yaml
from nornir.core import Nornir


class CredentialHandler:

    def __init__(self):
        self._credentials = self._get_unencrypted_creds()

    def _get_unencrypted_creds(self):
        enrypted_file_path = str(Path(Path.cwd() / 'inventory' / "vault" / "creds.yml"))
        password_file = str(Path(Path.cwd() / 'inventory' / "vault" / ".vault_pass"))
        result = self._decrypt_vault(encrypted_file=enrypted_file_path, vault_password_file=password_file)
        return dict(result)

    def _get_group_credentials(self, group):
        username = None
        password = None
        secret = None
        if group in self._credentials:
            username = self._credentials[group].get('username', None)
            password = self._credentials[group].get('password', None)
            secret = self._credentials[group].get('secret', None)
        return username, password, secret

    def _get_encrypted_inventory_groups(self):
        return list(self._credentials.keys())

    def _decrypt_vault(self, encrypted_file, vault_password_file):
        """
        filename: name of your encrypted file that needs decrypted.
        vault_password_file: file containing key that will decrypt the vault.
        """
        loader = DataLoader()
        vault_secret = CLI.setup_vault_secrets(loader=loader, vault_ids=[vault_password_file])
        vault = VaultLib(vault_secret)

        with open(encrypted_file) as file:
            unencrypted_byte_string = vault.decrypt(file.read())
            parsed_byte_string = yaml.safe_load(unencrypted_byte_string)
            return parsed_byte_string

    def insert_creds(self, nornir_obj: Nornir):
        credential_sets = self._get_encrypted_inventory_groups()
        for group_name, group_obj in nornir_obj.inventory.groups.items():
            if group_name in credential_sets:
                username, password, secret = self._get_group_credentials(group_name)
                group_obj.username = username
                group_obj.password = password
                if secret and group_name != "junos_group":
                    netmiko_params = group_obj.get_connection_parameters("netmiko")
                    extras = deepcopy(netmiko_params.extras)
                    extras["secret"] = secret
                    netmiko_params.extras = extras
                    group_obj.connection_options["netmiko"] = netmiko_params
                    if group_name == "cisco_group":
                        napalm_params = group_obj.get_connection_parameters("napalm")
                        extras = deepcopy(napalm_params.extras)
                        extras["optional_args"]["secret"] = secret
                        napalm_params.extras = extras
                        group_obj.connection_options["napalm"] = napalm_params

