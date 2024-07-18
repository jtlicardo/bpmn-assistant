from pydantic import BaseModel


class MessageItem(BaseModel):
    role: str
    content: str
