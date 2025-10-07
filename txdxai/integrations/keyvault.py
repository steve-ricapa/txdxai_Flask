import os
from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential

def get_keyvault_client():
    vault_url = os.getenv('AZURE_KEY_VAULT_URL')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    if not all([vault_url, tenant_id, client_id, client_secret]):
        raise ValueError('Azure Key Vault configuration is incomplete. Set AZURE_KEY_VAULT_URL, AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET')
    
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    return SecretClient(vault_url=vault_url, credential=credential)


def store_secret(secret_name, secret_value):
    try:
        client = get_keyvault_client()
        client.set_secret(secret_name, secret_value)
        return secret_name
    except ValueError as e:
        if 'Azure Key Vault configuration is incomplete' in str(e):
            return None
        raise Exception(f'Failed to store secret in Key Vault: {str(e)}')
    except Exception as e:
        raise Exception(f'Failed to store secret in Key Vault: {str(e)}')


def retrieve_secret(secret_name):
    try:
        client = get_keyvault_client()
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        raise Exception(f'Failed to retrieve secret from Key Vault: {str(e)}')


def delete_secret(secret_name):
    try:
        client = get_keyvault_client()
        client.begin_delete_secret(secret_name).wait()
        return True
    except Exception as e:
        raise Exception(f'Failed to delete secret from Key Vault: {str(e)}')
