import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal

from pydantic import BaseModel, ConfigDict, SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
    UserPasswordCredentials,
)
from backend.integrations.providers import ProviderName

class SMTPConfig(BaseModel):
    smtp_server: str = SchemaField(default="mail.intone.ca", description="SMTP server address")
    smtp_port: int = SchemaField(default=25, description="SMTP port number")
    auth_username: str = SchemaField(description="username for SMTP auth")
    auth_password: str = SchemaField(description="password for SMTP auth")
    
    model_config = ConfigDict(title="SMTP Config")


SMTPCredentials = UserPasswordCredentials
SMTPCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.SMTP],
    Literal["user_password"],
]


def SMTPCredentialsField() -> SMTPCredentialsInput:
    return CredentialsField(
        description="The SMTP integration requires a username and password.",
    )


class IntoneSendEmailBlock(Block):
    class Input(BlockSchema):
        to_email: str = SchemaField(
            description="Recipient email address", placeholder="recipient@example.com"
        )
        subject: str = SchemaField(
            description="Subject of the email", placeholder="Enter the email subject"
        )
        body: str = SchemaField(
            description="Body of the email in text", placeholder="Enter the email body"
        )
        bodyHtml: str = SchemaField(
            description="Body of the email in html", placeholder="Enter the email body",
        )
        config: SMTPConfig = SchemaField(
            description="SMTP Config",
            default=SMTPConfig(),
        )
        

    class Output(BlockSchema):
        status: str = SchemaField(description="Status of the email sending operation")
        error: str = SchemaField(
            description="Error message if the email sending failed"
        )

    def __init__(self):
        super().__init__(
            id="aabbccdd-0000-1111-2222-000000000002",
            description="This block sends a text/html email using SMTP.",
            categories={BlockCategory.OUTPUT},
            input_schema=IntoneSendEmailBlock.Input,
            output_schema=IntoneSendEmailBlock.Output,
        )

    @staticmethod
    def send_email(
        config: SMTPConfig,
        to_email: str,
        subject: str,
        body: str,
        bodyHtml:str
    ) -> str:
        smtp_server = config.smtp_server
        smtp_port = config.smtp_port
        smtp_username = config.auth_username
        smtp_password = config.auth_password

        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = to_email
        msg["Subject"] = subject
        if body:
            msg.attach(MIMEText(body, "plain"))
        if bodyHtml:
            msg.attach(MIMEText(bodyHtml,"html"))
        try:
            server=smtplib.SMTP(smtp_server, smtp_port)
            #server.starttls()
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, msg.as_string())
        except Exception as e:
            return f"error: {e}"
		
        return "Email sent successfully"

    def run(
        self, input_data: Input, *, credentials: SMTPCredentials, **kwargs
    ) -> BlockOutput:
        yield "status", self.send_email(
            config=input_data.config,
            to_email=input_data.to_email,
            subject=input_data.subject,
            body=input_data.body,
            bodyHtml=input_data.bodyHtml,
            credentials=credentials,
        )

# for testing
if __name__ == "__main__":
    config=SMTPConfig(smtp_server="mail.intone.ca",smtp_port=25)
    
    
    smtp = IntoneSendEmailBlock()
    input_args=IntoneSendEmailBlock.Input(config=config,to_email="ts@intone.ca",subject="test",body="text",
                                          bodyHtml="<body style='background-color:yellow'>html</body>")
    result = smtp.run(input_data=input_args,credentials=SMTPCredentials(
                                              username=SecretStr("tshazli@intonesolutions.com"),
                                              password=SecretStr( "2B3F0rG0od"),
                                              provider="smtp",
                                              title="intone"
										  ))
    print("Result:", list(result))
    input("Press any key to close...")