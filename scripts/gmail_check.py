import sys
sys.path.append("..")
from app.gmail import Gmail, get_body, get_headers

gmail = Gmail()
print("Connected as", gmail.address)

message_id = gmail.list_new_message_ids(max_results=1)[0]
message = gmail.get_message(message_id)
headers = get_headers(message)
print(headers["from"], "|", headers.get("subject"))
print(get_body(message)[:500])

gmail.send_reply(message, "Thanks, we received your email.")
print("Reply sent")