import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
PROCESSED_LABEL = "ai-processed"
ESCALATED_LABEL = "needs-human"


class Gmail:
    def __init__(self) -> None:
        creds = Credentials(
            token=None,
            refresh_token=settings.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )
        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        self.users = self.service.users()
        self.address = self.users.getProfile(userId="me").execute()["emailAddress"]
        self.label_ids = self._ensure_labels()

    def _ensure_labels(self) -> dict[str, str]:
        labels = self.users.labels().list(userId="me").execute().get("labels", [])
        ids = {label["name"]: label["id"] for label in labels}
        for name in (PROCESSED_LABEL, ESCALATED_LABEL):
            if name not in ids:
                label = self.users.labels().create(userId="me", body={"name": name}).execute()
                ids[name] = label["id"]
        return ids

    def list_new_message_ids(self, max_results: int = 10) -> list[str]:
        response = self.users.messages().list(
            userId="me",
            q=f"in:inbox -label:{PROCESSED_LABEL}",
            maxResults=max_results,
        ).execute()
        return [message["id"] for message in response.get("messages", [])]

    def get_message(self, message_id: str) -> dict:
        return self.users.messages().get(userId="me", id=message_id, format="full").execute()

    def get_thread(self, thread_id: str) -> dict:
        return self.users.threads().get(userId="me", id=thread_id, format="full").execute()

    def add_label(self, message_id: str, name: str) -> None:
        self.users.messages().modify(
            userId="me", id=message_id, body={"addLabelIds": [self.label_ids[name]]}
        ).execute()

    def is_escalated(self, thread: dict) -> bool:
        label_id = self.label_ids[ESCALATED_LABEL]
        return any(label_id in m.get("labelIds", []) for m in thread["messages"])

    def send_reply(self, message: dict, body: str) -> dict:
        headers = get_headers(message)
        subject = headers.get("subject", "")
        reply = EmailMessage()
        reply["To"] = headers.get("reply-to") or headers["from"]
        reply["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        reply["In-Reply-To"] = headers["message-id"]
        reply["References"] = f"{headers.get('references', '')} {headers['message-id']}".strip()
        reply.set_content(body)
        raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        return self.users.messages().send(
            userId="me", body={"raw": raw, "threadId": message["threadId"]}
        ).execute()


def get_headers(message: dict) -> dict[str, str]:
    return {h["name"].lower(): h["value"] for h in message["payload"].get("headers", [])}


def get_body(message: dict) -> str:
    def find_text(part: dict) -> str:
        data = part.get("body", {}).get("data")
        if part.get("mimeType") == "text/plain" and data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for child in part.get("parts", []):
            if text := find_text(child):
                return text
        return ""

    return find_text(message["payload"]) or message.get("snippet", "")


def has_attachments(message: dict) -> bool:
    def walk(part: dict) -> bool:
        return bool(part.get("filename")) or any(walk(p) for p in part.get("parts", []))

    return walk(message["payload"])


def strip_quoted(text: str) -> str:
    """Drop the quoted earlier messages that mail clients add below a reply."""
    lines = []
    for line in text.splitlines():
        if line.startswith("On ") and line.rstrip().endswith("wrote:"):
            break
        if not line.startswith(">"):
            lines.append(line)
    return "\n".join(lines).strip()


def format_thread(thread: dict, own_address: str) -> str:
    """Render a Gmail thread as plain text, oldest message first."""
    first = get_headers(thread["messages"][0])
    parts = [f"Subject: {first.get('subject', '')}"]
    for message in thread["messages"]:
        sender = get_headers(message).get("from", "")
        role = "Harbor & Pine support" if own_address.lower() in sender.lower() else "Customer"
        parts.append(f"{role} ({sender}):\n{strip_quoted(get_body(message))}")
    return "\n\n".join(parts)