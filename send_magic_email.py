import resend
import os
from dotenv import load_dotenv

from lib import inject_variables, load_template
from orm import User

load_dotenv()


resend.api_key = os.getenv("RESEND_API_KEY", "")

html_file_path = "magic_link_template.html"


def send_email_with_magic_number(user: User, code: str):
    variables = {
        "first_name": str(user.first_name),
        "last_name": str(user.last_name),
        "code": code,
    }
    file = load_template(html_file_path)
    template = inject_variables(file, variables)

    resend.Emails.send(
        {
            "from": "noreply@vectra-noreply.issaminu.com",
            "to": str(user.email),
            "subject": "Here's the code you requested",
            "html": template,
        }
    )
