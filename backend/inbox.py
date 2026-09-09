# https://learn.microsoft.com/en-us/graph/tutorials/python-app-only
# https://learn.microsoft.com/en-us/graph/tutorials/python-email

import asyncio

import credentials
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient


class PODInbox:
    def __init__(
        self,
        email_address : str | None = None,
        client_id     : str | None = None,
        tenant_id     : str | None = None,
        client_secret : str | None = None
    ):
        if not any([
            email_address, client_id, tenant_id, client_secret
        ]): email_address, client_id, tenant_id, client_secret = credentials.pod_inbox()
        
        self.client_credential : ClientSecretCredential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        self.app_client : GraphServiceClient = GraphServiceClient(
            self.client_credential
        )
    
    # async def get_app_only_token(self) -> str:
    #     from azure.core.credentials import AccessToken

    #     graph_scope = 'https://graph.microsoft.com/.default'
    #     access_token : AccessToken = await self.client_credential.get_token(graph_scope)
    #     return access_token.token
    
    async def get_emails(self) -> str:
        messages = await self.app_client.users.by_user_id("files@axima.com.au").mail_folders.by_mail_folder_id('inbox').messages.get()

        return messages


async def main():
    client = EmailClient()

    print(await client.get_emails())


if __name__ == "__main__":
    asyncio.run(main())
