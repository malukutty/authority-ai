from pydantic import BaseModel


class SeedResponse(BaseModel):
    count_created: int
    count_skipped: int
