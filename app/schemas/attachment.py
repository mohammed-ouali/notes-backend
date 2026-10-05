from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AttachmentResponse(BaseModel):
    id: int = Field(description="Unique identifier of the attachment.")
    file_name: str = Field(description="File name returned to clients when downloading the attachment.")
    content_type: str = Field(description="Media type of the attachment, such as image/png.")
    size_bytes: int = Field(description="Attachment size in bytes.")
    created_at: datetime = Field(description="Date and time the attachment was uploaded.")
    
    model_config = ConfigDict(from_attributes=True)