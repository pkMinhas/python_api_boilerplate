import sendgrid
import os
from sendgrid.helpers.mail import *

# TODO: change from address and names
from_address = "no-reply@marchingbytes.com"
from_name = "MarchingBytes Automated"


def send_email(to, subject, body):
    api_key = os.environ.get("SENDGRID_API_KEY")
    if api_key is None:
        print("Sendgrid not configured!")
        print(f"to {to}, subject {subject}, body {body}")
        return
    sg = sendgrid.SendGridAPIClient(api_key)
    from_sender = Email(email=from_address, name=from_name)
    my_mail = Mail(from_email=from_sender, to_emails=to, subject=subject, html_content=body)
    response = sg.send(my_mail)
    print(response.status_code)
    print(response.body)
    print(response.headers)
