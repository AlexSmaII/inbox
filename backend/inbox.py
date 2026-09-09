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
from msgraph.generated.models.file_attachment import FileAttachment
from msgraph.generated.models.message import Message
from msgraph.generated.models.message_collection_response import (
    MessageCollectionResponse,
)
from msgraph.generated.users.item.user_item_request_builder import (
    UserItemRequestBuilder,
)
from pathlib import Path


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
    
    async def get_attachments(self, email : Message) -> list[FileAttachment]:
        if not email.has_attachments: return []

        if not email.id: raise ValueError("Email is missing an ID field")

        result : AttachmentCollectionResponse = await self.inbox.messages.by_message_id(
            email.id
        ).attachments.get()

        if not result: return []
        attachments : list[Attachment] | None = result.value
        if not attachments: return []

        # Only include direct file attachments
        # (no SharePoint links) in the response
        # since these have a content_bytes field
        file_attachments : list[FileAttachment] = []
        for attachment in result.value:
            if isinstance(attachment, FileAttachment):
                file_attachments.append(attachment)

        return result.value
    
    async def save_attachment(
        self,
        attachment: FileAttachment,
        out_path : Path
    ):
        if attachment.name is None:
            raise TypeError("Attachment missing 'name' field")
        if attachment.content_bytes is None:
            raise TypeError("Attachment missing 'content_bytes' field")

        out_file = out_path / attachment.name

        with open(out_file, "wb") as f:
            f.write(attachment.content_bytes)
        
        return out_path


async def main():
    client = PODInbox()

    emails : list[Message] = await client.get_emails()

    ATTACHMENT_PATH = Path(__file__).parent / "attachments"

    for email in emails:
        print("-------------------------------------")
        print(f"SUBJECT:         {email.subject}")
        print(f"RECEIVED:        {email.received_date_time}")
        print(f"PREVIEW:\n\n{email.body_preview}\n")

        attachments : list[FileAttachment] = await client.get_attachments(email)
        if attachments:
            print("ATTACHMENTS:")
            for attachment in attachments:
                print(f"    NAME:  {attachment.name}")
                try:
                    await client.save_attachment(attachment, ATTACHMENT_PATH)
                except Exception as e:
                    pass




if __name__ == "__main__":
    asyncio.run(main())
