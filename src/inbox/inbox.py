from datetime import UTC, datetime, timedelta
from pathlib import Path

from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.attachment import Attachment
from msgraph.generated.models.attachment_collection_response import (
    AttachmentCollectionResponse,
)
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.file_attachment import FileAttachment
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.message_collection_response import (
    MessageCollectionResponse,
)
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)
from msgraph.generated.users.item.messages.item.attachments.attachments_request_builder import (
    AttachmentsRequestBuilder,
)
from msgraph.generated.users.item.messages.item.forward.forward_post_request_body import (
    ForwardPostRequestBody,
)
from msgraph.generated.users.item.messages.item.reply.reply_post_request_body import (
    ReplyPostRequestBody,
)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)
from msgraph.generated.users.item.user_item_request_builder import (
    UserItemRequestBuilder,
)

from inbox import credentials
from inbox.body_content import generate_email_html


def _graph_timestamp(
    moment : datetime
) -> str:
    """
    Render a moment the way Microsoft Graph compares
    receivedDateTime against.

    Graph holds the received time in UTC, so a moment carrying
    another timezone is converted rather than having its offset
    written out. A moment carrying none is read as UTC, which
    is what the rest of this package works in.

    Args:
        moment (datetime): The moment to render.

    Returns:
        str: The moment as an ISO timestamp ending in Z.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)

    return moment.astimezone(UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


ITEM_EXPAND = "microsoft.graph.itemAttachment/item"
"""
What asks Graph for the message carried inside an attachment.

An itemAttachment is returned without its own item unless this is
expanded, and an item returned without its attachments says nothing
about the files it holds. One expanded request answers both, with the
nested files' bytes included, so a batch forwarded as an attached email
costs no more to read than one attached directly.
"""


MAX_ATTACHMENT_DEPTH = 4
"""
How far into attached messages to look for files.

Graph expands one level, so anything deeper arrives only if a later
version of the service sends it. The bound is here so that a message
which somehow attaches itself cannot be followed forever.
"""


def file_attachments(
    attachments : list[Attachment] | None,
    depth : int = 0
) -> list[FileAttachment]:
    """
    Every file in a collection of attachments, including the files
    carried inside attached messages.

    A person who forwards a batch as an attached email rather than
    forwarding it inline sends the same scans, but Graph files them
    under the message they came from rather than under the message
    which arrived. Reading only the outer collection therefore finds
    nothing and the batch looks like an email with no documents in it.

    A reference attachment, which is a link to a document rather than
    the document, carries no bytes and is left out, as is an attached
    item which is a contact or an appointment rather than a message.

    Args:
        attachments (list[Attachment] | None):
            The collection to read, or nothing.
        depth (int, optional):
            How many attached messages deep this call already is.
            Defaults to 0, which is the message itself.

    Returns:
        list[FileAttachment]:
            The files, outermost first, each with whatever bytes the
            request they came from asked for.
    """
    found : list[FileAttachment] = []

    if not attachments or depth > MAX_ATTACHMENT_DEPTH:
        return found

    for attachment in attachments:
        if isinstance(attachment, FileAttachment):
            found.append(attachment)
            continue

        # An itemAttachment, whose files belong to the message it
        # holds. Anything else is a link, which has neither an item
        # nor bytes, and getattr answers None for it rather than
        # needing the type to be tested for.
        item = getattr(attachment, "item", None)
        found.extend(
            file_attachments(getattr(item, "attachments", None), depth + 1)
        )

    return found


def save_attachment(
    attachment: FileAttachment,
    out_path : Path
) -> Path:
    """
    Download an attachment from an Outlook email.

    Args:
        attachment (FileAttachment): The attachment.
        out_path (Path): The path to save it.

    Raises:
        TypeError: Attachment missing 'name' field.
        TypeError: Attachment is missing a 'content_bytes' field.

    Returns:
        Path: Path of the saved attachment file.
    """    
    if attachment.name is None:
        raise TypeError("Attachment missing 'name' field")
    if attachment.content_bytes is None:
        raise TypeError("Attachment is missing a 'content_bytes' field")
        
    out_file = out_path / attachment.name

    with open(out_file, "wb") as f:
        f.write(attachment.content_bytes)
    
    return out_file.resolve()


class OutlookInbox:
    def __init__(
        self,
        email_address : str | None = None,
        client_id     : str | None = None,
        tenant_id     : str | None = None,
        client_secret : str | None = None
    ):
        if not any([
            email_address, client_id, tenant_id, client_secret
        ]): email_address, client_id, tenant_id, client_secret = credentials.outlook_inbox()
        
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
    

    async def get_emails(
        self,
        unread_only : bool = True,
        search_term : str | None = None,
        min_age : timedelta | None = None,
        top : int = 10,
        exclude_self : bool = True,
        from_email_address : str | None = None,
        received_from : datetime | None = None,
        received_to : datetime | None = None,
        skip : int = 0,
        select : list[str] | None = None
    ) -> list[Message]:
        """
        Obtain a list of emails from the inbox ordered
        by received date, descending.

        Args:
            unread_only (bool, optional):
                Only include unread emails. Defaults to True.
            search_term (str | None, optional):
                If given, only include emails where the
                subject contains a search term. Defaults to None.
            min_age (timedelta | None, optional):
                If given, only include emails received at least
                this long ago. Defaults to None.
            top (int, optional):
                Number of emails to return. Defaults to 10.
            exclude_self (bool, optional):
                Exclude emails send from this inbox.
                Defaults to True.
            from_email_address (str | None, optional):
                If given, only include emails sent from this
                address. Defaults to None, which includes
                every sender.
            received_from (datetime | None, optional):
                If given, only include emails received at or
                after this moment. Must carry a timezone, since
                Microsoft Graph compares against an absolute
                instant rather than a wall clock. Defaults to
                None.
            received_to (datetime | None, optional):
                If given, only include emails received before
                this moment. Defaults to None.
            skip (int, optional):
                How many of the matching emails to pass over
                before the ones returned, which is what reads a
                mailbox a page at a time. Defaults to 0.
            select (list[str] | None, optional):
                The message properties to return, named as
                Microsoft Graph names them. Defaults to None,
                which returns the whole message. A caller which
                only lists what arrived should name the few
                fields it reads: the body travels with a message
                otherwise, and a page of them is most of the time
                a listing takes.

        Returns:
            list[Message]: The list of emails.
        """

        filter_list : list[str] = []
        if unread_only: filter_list.append("isRead eq false")
        if search_term: filter_list.append(f"contains(subject, '{search_term}')")
        if from_email_address:
            filter_list.append(
                f"from/emailAddress/address eq '{from_email_address}'"
            )
        if exclude_self and self.email_address:
            filter_list.append(
                f"from/emailAddress/address ne '{self.email_address}'"
            )
        if min_age:
            date_cutoff : datetime = datetime.now(UTC)
            # from zoneinfo import ZoneInfo
            # print(date_cutoff.astimezone(ZoneInfo("Australia/Melbourne")).strftime("%d/%m/%Y %I:%M %p"))
            # print(min_age)
            date_cutoff -= min_age
            # print(date_cutoff.astimezone(ZoneInfo("Australia/Melbourne")).strftime("%d/%m/%Y %I:%M %p"))
            date_cutoff_str : str = date_cutoff.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            # print(date_cutoff_str)
            filter_list.append(f"receivedDateTime le {date_cutoff_str}")

        if received_from:
            filter_list.append(
                f"receivedDateTime ge {_graph_timestamp(received_from)}"
            )

        if received_to:
            filter_list.append(
                f"receivedDateTime lt {_graph_timestamp(received_to)}"
            )

        filter : str | None = None
        if filter_list: filter = " and ".join(filter_list)

        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            filter=filter,
            # The order is the mailbox's own, which is newest first, and
            # is not asked for. Microsoft Graph refuses to sort a result
            # it has already restricted this far and answers "The
            # restriction or sort order is too complex for this
            # operation", so asking for the order it was going to use
            # anyway is what would break paging rather than steady it.
            top=top,
            skip=skip or None,
            select=select
        )

        request_configuration = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        result : MessageCollectionResponse | None = await self.inbox.messages.get(
            request_configuration=request_configuration
        )

        if not result: return []
        messages : list[Message] | None = result.value
        if messages is None: return []

        return messages
    
    
    async def mark_as_read(
        self,
        email : Message,
        mark_unread : bool = False
    ) -> Message:
        """
        Mark an email as read so that it does not appear
        when calling get_emails(unread_only = True).

        Args:
            email (Message): Email to mark as read.
            mark_unread (bool):
                Whether to mark the email as unread
                rather than read.

        Returns:
            Message: The email, now marked as read.
        """
        
        result : Message = await self.inbox.messages.by_message_id(
            email.id
        ).patch(
            Message(
                is_read=not mark_unread
            )
        )

        return result
    
    
    def _generate_recipients(
        self,
        recipient_emails : list[str]
    ) -> list[Recipient]:
        return [
            Recipient(
                email_address = EmailAddress(
                    address=email
                )
            ) for email in recipient_emails
        ]
    
    
    async def forward(
        self,
        email : Message,
        recipient_emails : list[str],
        comment : str | None = "FYI"
    ):
        """
        Forward an email.

        Args:
            email (Message):
                Email to be forwarded.
            recipient_emails (list[str]):
                List of recipients to send.
            comment (str | None, optional):
                Comment. Defaults to "FYI".
        """        
        to_recipients : list[Recipient] = self._generate_recipients(
            recipient_emails
        )

        request : ForwardPostRequestBody = ForwardPostRequestBody(
            comment=comment,
            to_recipients=to_recipients
        )

        await self.inbox.messages.by_message_id(
            email.id
        ).forward.post(request)


    async def get_attachments(
        self,
        email : Message,
        file_suffix : str | None = ".pdf"
    ) -> list[FileAttachment]:
        """
        Download all attachments for a given email.

        The files carried inside attached messages are included
        beside the files attached to the email itself. A batch
        forwarded as an attached email rather than forwarded
        inline holds its scans one level down, and reading only
        the outer collection found none of them.

        Args:
            email (Message):
                The email to download attachments for.
            file_suffix (str | None, optional):
                Only include files with the given suffix.
                Defaults to ".pdf".

        Raises:
            ValueError: Email does not have an ID field.

        Returns:
            list[FileAttachment]:
                The attachments, those of the email itself first.
                A file found inside an attached message is
                identified by that message rather than by this
                one, so it cannot be fetched again through
                get_attachment with this email's identifier.
        """

        if not email.has_attachments: return []

        if not email.id: raise ValueError("Email is missing an ID field")

        query_params = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetQueryParameters(
            expand=[ITEM_EXPAND]
        )

        request_configuration = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        result : AttachmentCollectionResponse | None = await self.inbox.messages.by_message_id(
            email.id
        ).attachments.get(request_configuration=request_configuration)

        if not result: return []
        attachments : list[Attachment] | None = result.value
        if not attachments: return []

        # Only files are returned, because a SharePoint link has no
        # content_bytes field and a caller reading one got an
        # AttributeError rather than a document.
        found : list[FileAttachment] = file_attachments(attachments)

        # The same message attached twice carries the same file twice,
        # and a batch read twice would record its hours twice.
        seen : set[str] = set()
        unique : list[FileAttachment] = []
        for attachment in found:
            key = attachment.id or f"{attachment.name}:{attachment.size}"
            if key in seen: continue
            seen.add(key)
            unique.append(attachment)

        if not file_suffix: return unique

        # Narrows the file attachments rather than the whole collection.
        # Filtering the collection put a SharePoint link named '.pdf'
        # back into the result, and a link carries no content_bytes, so
        # a caller reading the file got an AttributeError instead.
        return [
            a for a in unique
            if (a.name or "").strip().lower().endswith(file_suffix)
        ]


    async def attached_messages(
        self,
        email : Message,
        file_suffix : str | None = ".pdf"
    ) -> list[Message]:
        """
        The emails attached to an email.

        Somebody chasing a batch which never arrived forwards the
        original as an attachment rather than forwarding it inline,
        and several days of sheets then arrive on one message. Each
        attached email keeps its own sender, subject and arrival
        time, none of which the message carrying them states, so
        this is what says which days a chased-up batch covers.

        Microsoft Graph expands one level, so an email attached to
        an attached email is not reported here even though
        get_attachments would still find its files.

        Args:
            email (Message):
                The email to read the attached emails of.
            file_suffix (str | None, optional):
                Count only files with this suffix against each
                attached email. Defaults to ".pdf".

        Raises:
            ValueError: Email does not have an ID field.

        Returns:
            list[Message]:
                One per attached email, in the order the mailbox
                holds them, each carrying its own attachments.
                Empty where nothing is attached or nothing
                attached is an email.
        """
        if not email.has_attachments: return []

        if not email.id: raise ValueError("Email is missing an ID field")

        query_params = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetQueryParameters(
            expand=[ITEM_EXPAND]
        )

        request_configuration = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        result : AttachmentCollectionResponse | None = await self.inbox.messages.by_message_id(
            email.id
        ).attachments.get(request_configuration=request_configuration)

        if not result or not result.value: return []

        messages : list[Message] = []

        for attachment in result.value:
            item = getattr(attachment, "item", None)
            if not isinstance(item, Message): continue

            # The attached email as Graph returns it, which names no
            # subject of its own where the attachment was renamed. The
            # attachment's name is what a person sees in Outlook, so it
            # stands in for a subject the item does not carry.
            if item.subject is None: item.subject = attachment.name

            # Narrowed here rather than by the caller, so that the files
            # counted against an attached email are the same ones
            # get_attachments would return for the message as a whole.
            if file_suffix:
                item.attachments = [
                    a for a in file_attachments(item.attachments)
                    if (a.name or "").strip().lower().endswith(file_suffix)
                ]

            messages.append(item)

        return messages


    async def list_attachments(
        self,
        email : Message,
        file_suffix : str | None = ".pdf"
    ) -> list[Attachment]:
        """
        List an email's attachments without downloading them.

        get_attachments asks for the whole collection, and Graph answers
        that with contentBytes on every attachment. A batch of scanned
        activity sheets is megabytes, so a caller which only wants to know
        what is attached pays for the files themselves. This asks for the
        identifying fields and nothing else.

        The result carries no bytes, so it cannot be read or saved. Fetch
        one with get_attachment once it is known which one is wanted.

        Args:
            email (Message):
                The email to list attachments for.
            file_suffix (str | None, optional):
                Only include files with the given suffix.
                Defaults to ".pdf".

        Raises:
            ValueError: Email does not have an ID field.

        Returns:
            list[Attachment]: The attachments, without their contents.
        """
        if not email.has_attachments: return []

        if not email.id: raise ValueError("Email is missing an ID field")

        query_params = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetQueryParameters(
            select=["id", "name", "size", "contentType"]
        )

        request_configuration = AttachmentsRequestBuilder.AttachmentsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        result : AttachmentCollectionResponse | None = await self.inbox.messages.by_message_id(
            email.id
        ).attachments.get(request_configuration=request_configuration)

        if not result: return []
        attachments : list[Attachment] | None = result.value
        if not attachments: return []

        if file_suffix:
            # Selected by name rather than by type. Without contentBytes a
            # reference attachment and a file attachment are much the same
            # object, and the name is what says whether it is a scan.
            attachments = [
                a for a in attachments
                if (a.name or "").strip().lower().endswith(file_suffix)
            ]

        return attachments


    async def get_attachment(
        self,
        email_id : str,
        attachment_id : str
    ) -> FileAttachment:
        """
        Download one attachment from an email by its identifier.

        Reading one attachment rather than every attachment of
        the email is what lets a caller show a single scanned
        sheet without downloading the rest of the batch beside
        it.

        Args:
            email_id (str): Identifier of the email.
            attachment_id (str): Identifier of the attachment.

        Raises:
            TypeError: The attachment is a link rather than a
                file, and so carries no bytes.

        Returns:
            FileAttachment: The attachment, including its bytes.
        """
        attachment : Attachment | None = await self.inbox.messages.by_message_id(
            email_id
        ).attachments.by_attachment_id(attachment_id).get()

        if not isinstance(attachment, FileAttachment):
            raise TypeError(
                f"Attachment '{attachment_id}' is not a file attachment"
            )

        return attachment
    

    async def send_email(
        self,
        subject : str,
        content : str,
        recipient_emails : list[str],
        attachments : list[FileAttachment] = []
    ) -> Message:
        """
        Send an email.

        Args:
            subject (str): The email's title.
            content (str): The email's body content in HTML.
            recipient_emails (list[str]):
                Who to send the email to.
            attachments (list[FileAttachment], optional):
                List of FileAttachment objects to attach.
                Defaults to [].

        Returns:
            Message: The content of the email.
        """        

        to_recipients = self._generate_recipients(
            recipient_emails
        )
        
        body = ItemBody(
            content_type = BodyType.Html,
            content = generate_email_html(content)
        )

        email : SendMailPostRequestBody = SendMailPostRequestBody(
            message = Message(
                subject = subject,
                to_recipients = to_recipients,
                body = body,
                attachments = attachments
            )
        )

        await self.inbox.send_mail.post(email)

        return email.message
    

    async def send_reply(
        self,
        email : Message,
        content : str,
        subject : str | None = None,
        recipient_emails : list[str] | None = None,
        attachments : list[FileAttachment] = []
    ) -> Message:
        """
        Send a reply to a given email.

        Args:
            email (Message): The email to reply to.
            content (str): The content of the reply.
            subject (str | None, optional):
                The title of the reply.
                Defaults to Re: <original subject>.
            recipient_emails (list[str] | None, optional):
                Who to send the reply to.
                Defaults to the sender of the original email.
            attachments (list[FileAttachment], optional):
                List of FileAttachment objects to attach.
                Defaults to [].

        Returns:
            Message: The content of the reply.
        """
        
        if not recipient_emails:
            to_recipients = [email.sender]
        else:
            sender_address : str = email.sender.email_address.address
            if not sender_address in recipient_emails:
                recipient_emails.append(sender_address)
            to_recipients = self._generate_recipients(
                recipient_emails
            )
        
        if not subject:
            subject = f"Re: {email.subject}"
        
        content : str = generate_email_html(content)
        content = content.strip()
        content += "<br/><hr/><br/>"
        content += email.body.content.strip()

        body = ItemBody(
            content_type = BodyType.Html,
            content = content
        )

        reply : ReplyPostRequestBody = ReplyPostRequestBody(
            message = Message(
                subject = subject,
                to_recipients = to_recipients,
                body = body,
                attachments = attachments
            )
        )

        await self.inbox.messages.by_message_id(
            email.id
        ).reply.post(reply)

        return reply.message
