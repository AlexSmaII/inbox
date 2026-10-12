"""
Find messages by what they are rather than by what they say.

A mailbox search asks Microsoft Graph for the messages whose
subject contains a term. That answers a question about wording,
not about content: a reply quoting the term is returned, an
automatic reply carrying it is returned, and a message whose
sender worded the subject differently is missed. A caller which
wants the messages of a particular kind has to decide that for
itself.

This module holds the three parts of doing so. A classifier
decides what one message is. An index remembers that decision
against the message it was made about. IndexedSearch puts the
two together: it asks the mailbox for candidates, reads the
index for the ones already decided, classifies only the rest,
and writes every new decision back.

The decision is therefore made once per message however often
the mailbox is searched, which is what makes a classifier
expensive enough to be worth caching usable here at all.

Nothing in this module knows what any particular label means. A
label is a string the caller chooses, the classifier produces
and the index stores, so the same machinery serves a mailbox
sorting scanned forms and a mailbox sorting invoices.

An index which keeps decisions beyond the life of the process
has to be supplied by the caller, because where they are kept is
a question about the caller's deployment rather than about the
mailbox. MemoryIndex is the default and keeps them for the
process only, so a caller which has nowhere to put them still
works and simply classifies again next time.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from msgraph.generated.models.message import Message
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from inbox.inbox import OutlookInbox


UNKNOWN = "unknown"
"""
The label of a message nothing could decide about.

A classifier which fails is not the same as a classifier which
decided a message is not what was asked for, and recording the
failure as a decision would mean never looking at that message
again. This label is written down so the attempt is visible, and
IndexedSearch treats it as undecided and tries once more.
"""


PAGE_SIZE = 25
"""
How many messages a search reads from the mailbox at a time.

Large enough that an ordinary search is one request, and small
enough that a search which stops early has not paid to classify
a page it did not need.
"""

MAX_CANDIDATES = 200
"""
How many messages a search considers before giving up.

A bound on the work rather than a page size. A mailbox whose
wanted messages have been buried under several hundred unwanted
ones is a mailbox which needs attention, and reading the whole
of it on every search would not be the way to give it any.
"""


class MessageLabel(BaseModel):
    """
    What a classifier decided one message is.

    Attributes:
        message_id (str):
            The message the decision is about, as Microsoft
            Graph identifies it.
        label (str):
            What it was decided to be. The caller chooses the
            vocabulary; UNKNOWN means nothing could be decided.
        confidence (float | None):
            How sure the classifier was, from zero to one, where
            it reports such a figure.
        reason (str | None):
            Why it decided that, in the classifier's own words,
            kept so a decision can be argued with afterwards.
        decided_by (str | None):
            What made the decision, such as a model name. Two
            decisions made by different things are worth telling
            apart when one of them turns out to be wrong.
        decided_at (datetime):
            When it was decided.
    """

    message_id : str
    label : str
    confidence : float | None = None
    reason : str | None = None
    decided_by : str | None = None
    decided_at : datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def decided(self) -> bool:
        """
        Whether this counts as an answer.

        Returns:
            bool: True where the label is anything but UNKNOWN.
        """
        return self.label != UNKNOWN


@runtime_checkable
class MessageIndex(Protocol):
    """
    Somewhere decisions about messages are kept.

    Stated as a protocol rather than a base class because an
    implementation is a database table, a file or a dictionary,
    and those have nothing in common underneath for a shared
    parent to hold.

    An implementation has to be safe to call with identifiers it
    has never seen, which is the ordinary case on the first
    search of a day.
    """

    def labels(
        self,
        message_ids : Sequence[str]
    ) -> dict[str, MessageLabel]:
        """
        Read the decisions already made about some messages.

        Args:
            message_ids (Sequence[str]): The messages to look up.

        Returns:
            dict[str, MessageLabel]:
                A decision for each identifier one is held for.
                An identifier nothing is held for is absent
                rather than present and empty.
        """
        ...

    def remember(
        self,
        label : MessageLabel
    ) -> None:
        """
        Write down one decision, replacing any already held.

        Args:
            label (MessageLabel): The decision.
        """
        ...


class MemoryIndex:
    """
    Decisions kept for the life of the process and no longer.

    What a caller with nowhere else to put them gets. A search
    repeated in the same process classifies nothing twice, and a
    restart classifies everything again, so this is enough for a
    script and not enough for a service.
    """

    def __init__(self) -> None:
        self._labels : dict[str, MessageLabel] = {}

    def labels(
        self,
        message_ids : Sequence[str]
    ) -> dict[str, MessageLabel]:
        """
        Read the decisions already made about some messages.

        Args:
            message_ids (Sequence[str]): The messages to look up.

        Returns:
            dict[str, MessageLabel]: Those which are held.
        """
        return {
            message_id : self._labels[message_id]
            for message_id in message_ids
            if message_id in self._labels
        }

    def remember(
        self,
        label : MessageLabel
    ) -> None:
        """
        Write down one decision, replacing any already held.

        Args:
            label (MessageLabel): The decision.
        """
        self._labels[label.message_id] = label


@runtime_checkable
class MessageClassifier(Protocol):
    """
    Something which decides what a message is.

    An implementation may read the message itself, download its
    attachments, call a model, or any combination, and is
    expected to be costly enough that the result is worth
    keeping. It is called once per message per index.

    A classifier is asked about one message at a time rather than
    a list, so that a failure belongs to the message which caused
    it and the rest of the search goes on.
    """

    @property
    def name(self) -> str:
        """
        What to record as having made the decision.

        Returns:
            str: A name, such as the model which was called.
        """
        ...

    async def label(
        self,
        inbox : OutlookInbox,
        message : Message
    ) -> MessageLabel:
        """
        Decide what one message is.

        Args:
            inbox (OutlookInbox):
                The mailbox it came from, for reading anything
                the message itself does not carry, such as its
                attachments.
            message (Message): The message to decide about.

        Returns:
            MessageLabel:
                The decision, which may be UNKNOWN where nothing
                could be decided.
        """
        ...


class IndexedSearch:
    """
    Search a mailbox by what a classifier made of each message.

    The mailbox narrows the candidates by the things it can
    answer cheaply and exactly, such as whether a message is
    unread, how old it is and who sent it. The classifier
    answers the one thing the mailbox cannot, which is what the
    message holds, and the index means it answers it once.
    """

    def __init__(
        self,
        inbox : OutlookInbox,
        classifier : MessageClassifier,
        index : MessageIndex | None = None
    ) -> None:
        """
        Args:
            inbox (OutlookInbox): The mailbox to search.
            classifier (MessageClassifier):
                What decides a message nothing has decided yet.
            index (MessageIndex | None, optional):
                Where decisions are kept. Defaults to a
                MemoryIndex, which keeps them for this process
                only.
        """
        self.inbox = inbox
        self.classifier = classifier
        self.index : MessageIndex = index if index is not None else MemoryIndex()

    async def classify(
        self,
        messages : Sequence[Message],
        reclassify : bool = False
    ) -> dict[str, MessageLabel]:
        """
        Decide what each of some messages is, reading the index
        first and writing every new decision to it.

        A message already decided costs nothing. A message not
        yet decided is put to the classifier, and what comes
        back is written down before it is returned, so a run
        which fails part way through keeps the decisions it paid
        for.

        A classifier which raises is recorded as UNKNOWN rather
        than allowed to end the search. One unreadable message
        should not stop the rest being found, and UNKNOWN is
        read as undecided, so the message is tried again on the
        next search rather than being left out for good.

        Args:
            messages (Sequence[Message]): The messages to decide.
            reclassify (bool, optional):
                Decide every message again, ignoring and then
                replacing what the index holds. Defaults to
                False.

        Returns:
            dict[str, MessageLabel]:
                One decision per message which carries an
                identifier, by identifier.
        """
        identified = [m for m in messages if m.id]

        known : dict[str, MessageLabel] = {}
        if not reclassify:
            known = self.index.labels([m.id for m in identified])
            # A message whose only decision is that nothing could be
            # decided is not decided, so it is put to the classifier
            # again rather than being passed over for the rest of time.
            known = {k : v for k, v in known.items() if v.decided}

        decisions : dict[str, MessageLabel] = dict(known)

        for message in identified:
            if message.id in decisions:
                continue

            try:
                decision = await self.classifier.label(self.inbox, message)
            except Exception as error:
                decision = MessageLabel(
                    message_id = message.id,
                    label      = UNKNOWN,
                    reason     = f"{type(error).__name__}: {error}",
                    decided_by = self.classifier.name
                )

            self.index.remember(decision)
            decisions[message.id] = decision

        return decisions

    async def search(
        self,
        label : str,
        limit : int | None = None,
        unread_only : bool = True,
        min_age : timedelta | None = None,
        exclude_self : bool = True,
        from_email_address : str | None = None,
        received_from : datetime | None = None,
        received_to : datetime | None = None,
        page_size : int = PAGE_SIZE,
        max_candidates : int = MAX_CANDIDATES,
        reclassify : bool = False
    ) -> list[Message]:
        """
        List the messages a classifier decided are of one kind.

        The arguments the mailbox can answer are passed to it
        unchanged. What this adds is the one thing the mailbox
        cannot answer, so the cost of a search is a
        classification of each candidate the index holds no
        decision for, and nothing for the rest.

        The mailbox is read a page at a time until enough
        messages carrying the label have been found, because
        wanted and unwanted messages are mixed together in it and
        the mailbox cannot be asked to return only one of them.
        One page would therefore answer fewer messages than were
        asked for whenever anything else is sitting among them,
        and nothing at all once a message no caller claims has
        settled at the front. `max_candidates` is what bounds how
        far it reads instead.

        Args:
            label (str): The label to return messages for.
            limit (int | None, optional):
                How many messages to return. Defaults to None,
                which is every one found within max_candidates.
            unread_only (bool, optional):
                Only consider unread messages. Defaults to True.
            min_age (timedelta | None, optional):
                Only consider messages received at least this
                long ago. Defaults to None.
            exclude_self (bool, optional):
                Leave out messages sent from this mailbox.
                Defaults to True.
            from_email_address (str | None, optional):
                Only consider messages from this address.
                Defaults to None, which is every sender.
            received_from (datetime | None, optional):
                Only consider messages received at or after this
                moment. Defaults to None.
            received_to (datetime | None, optional):
                Only consider messages received before this
                moment. Defaults to None.
            page_size (int, optional):
                How many messages to read from the mailbox at a
                time. Defaults to PAGE_SIZE.
            max_candidates (int, optional):
                How many messages to consider in all, however
                few of them carry the label. Defaults to
                MAX_CANDIDATES.
            reclassify (bool, optional):
                Decide every candidate again rather than reading
                the index. Defaults to False.

        Returns:
            list[Message]:
                The messages carrying the label, in the order the
                mailbox gave them.
        """
        found : list[Message] = []
        seen : int = 0

        while seen < max_candidates:
            wanted = min(page_size, max_candidates - seen)

            page : list[Message] = await self.inbox.get_emails(
                unread_only        = unread_only,
                search_term        = None,
                min_age            = min_age,
                top                = wanted,
                exclude_self       = exclude_self,
                from_email_address = from_email_address,
                received_from      = received_from,
                received_to        = received_to,
                skip               = seen
            )

            if not page:
                break

            seen += len(page)

            decisions = await self.classify(page, reclassify=reclassify)

            for message in page:
                if not message.id:
                    continue
                decision = decisions.get(message.id)
                if decision is not None and decision.label == label:
                    found.append(message)

            if limit is not None and len(found) >= limit:
                return found[:limit]

            # A short page is the end of the mailbox. Asking for the
            # next one would answer nothing and cost a request.
            if len(page) < wanted:
                break

        return found
