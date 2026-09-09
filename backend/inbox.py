# https://learn.microsoft.com/en-us/graph/tutorials/python-app-only
# https://learn.microsoft.com/en-us/graph/tutorials/python-email

import asyncio

import credentials
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.attachment import Attachment
from msgraph.generated.models.attachment_collection_response import (
    AttachmentCollectionResponse,
)
from msgraph.generated.models.message import Message
from msgraph.generated.models.message_collection_response import (
    MessageCollectionResponse,
)
from msgraph.generated.users.item.user_item_request_builder import (
    UserItemRequestBuilder,
)


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
        
        self.email_address = email_address

        self.client_credential : ClientSecretCredential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        self.app_client : GraphServiceClient = GraphServiceClient(
            self.client_credential
        )

        self.inbox : UserItemRequestBuilder = self.app_client.users.by_user_id(
            self.email_address
        )

        # self.inbox = self.email_client.mail_folders.by_mail_folder_id('inbox')
    
    # async def get_app_only_token(self) -> str:
    #     from azure.core.credentials import AccessToken

    #     graph_scope = 'https://graph.microsoft.com/.default'
    #     access_token : AccessToken = await self.client_credential.get_token(graph_scope)
    #     return access_token.token
    
    async def get_emails(self) -> list[Message]:
        result : MessageCollectionResponse | None = await self.inbox.messages.get()
        if not result: raise ValueError("No emails found")
        messages : list[Message] | None = result.value
        if not messages: raise ValueError("No emails found")

        return messages
    
    async def get_attachments(self, email : Message) -> list[Attachment]:
        if not email.has_attachments: return []

        if not email.id: raise ValueError("Email is missing an ID field")

        result : AttachmentCollectionResponse = await self.inbox.messages.by_message_id(
            email.id
        ).attachments.get()

        if not result: return []
        if not result.value: return []
        return result.value


async def main():
    client = PODInbox()

    emails : list[Message] = await client.get_emails()

    for email in emails:
        print("-------------------------------------")
        print(f"SUBJECT:         {email.subject}")
        print(f"RECEIVED:        {email.received_date_time}")
        print(f"PREVIEW:\n\n{email.body_preview}\n")

        attachments : list[Attachment] = await client.get_attachments(email)
        if attachments:
            print("ATTACHMENTS:")
            for attachment in attachments:
                print(f"    NAME: {attachment.name}")


if __name__ == "__main__":
    asyncio.run(main())
