from pydantic import BaseModel

class Comment(BaseModel):
    id: str
    video_timestamp: float
    message: str
    author: str
    created_at: float
