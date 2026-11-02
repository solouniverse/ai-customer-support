# # import logging

# # from app.gmail import PROCESSED_LABEL, Gmail, get_headers

# # logger = logging.getLogger(__name__)


# # def handle_message(gmail: Gmail, message_id: str) -> None:
# #     message = gmail.get_message(message_id)
# #     headers = get_headers(message)
# #     logger.info("New email from %s: %s", headers.get("from"), headers.get("subject"))
# #     gmail.add_label(message_id, PROCESSED_LABEL)

# import logging
# from email.utils import parseaddr

# from app import db
# from app.gmail import PROCESSED_LABEL, Gmail, get_body, get_headers

# logger = logging.getLogger(__name__)
# MAX_ATTEMPTS = 3


# def handle_message(gmail: Gmail, message_id: str) -> None:
#     event = db.start_event(message_id)
#     if event is None:
#         gmail.add_label(message_id, PROCESSED_LABEL)
#         return
#     try:
#         status, result = process(gmail, message_id)
#         gmail.add_label(message_id, PROCESSED_LABEL)
#         db.finish_event(event["id"], status, result)
#         logger.info("%s %s %s", message_id, status, result)
#     except Exception as error:
#         db.fail_event(event["id"], str(error))
#         if event["attempts"] >= MAX_ATTEMPTS:
#             # Give up, so the message does not loop forever.
#             gmail.add_label(message_id, PROCESSED_LABEL)
#         raise


# def process(gmail: Gmail, message_id: str) -> tuple[str, dict]:
#     message = gmail.get_message(message_id)
#     headers = get_headers(message)
#     sender = parseaddr(headers.get("from", ""))[1]

#     ticket_id = db.upsert_ticket(message["threadId"], sender, headers.get("subject", ""))
#     db.save_message(ticket_id, message_id, "in", sender, get_body(message))
#     return "processed", {"action": "saved"}

import logging
from email.utils import parseaddr

from app import db
from app.gmail import PROCESSED_LABEL, Gmail, get_body, get_headers
from app.guards import skip_reason

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3

ACKNOWLEDGEMENT = """Hi,

Thanks for your email. We received your message and will get back to you soon.

Harbor & Pine support"""


def handle_message(gmail: Gmail, message_id: str) -> None:
    event = db.start_event(message_id)
    if event is None:
        gmail.add_label(message_id, PROCESSED_LABEL)
        return
    try:
        status, result = process(gmail, message_id)
        gmail.add_label(message_id, PROCESSED_LABEL)
        db.finish_event(event["id"], status, result)
        logger.info("%s %s %s", message_id, status, result)
    except Exception as error:
        db.fail_event(event["id"], str(error))
        if event["attempts"] >= MAX_ATTEMPTS:
            gmail.add_label(message_id, PROCESSED_LABEL)
        raise


def process(gmail: Gmail, message_id: str) -> tuple[str, dict]:
    message = gmail.get_message(message_id)
    headers = get_headers(message)

    reason = skip_reason(message, headers, gmail.address)
    if reason:
        return "skipped", {"reason": reason}

    sender = parseaddr(headers.get("from", ""))[1]
    ticket_id = db.upsert_ticket(message["threadId"], sender, headers.get("subject", ""))
    db.save_message(ticket_id, message_id, "in", sender, get_body(message))

    sent = gmail.send_reply(message, ACKNOWLEDGEMENT)
    db.save_message(ticket_id, sent["id"], "out", gmail.address, ACKNOWLEDGEMENT)
    db.update_ticket(ticket_id, "answered")
    return "processed", {"action": "acknowledged"}