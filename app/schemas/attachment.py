from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)