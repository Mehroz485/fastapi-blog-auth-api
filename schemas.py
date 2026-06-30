from pydantic import BaseModel


class BlogCreate(BaseModel):
    title: str
    content: str


class BlogResponse(BlogCreate):
    id: int

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"