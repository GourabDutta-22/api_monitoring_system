from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime

class ServiceResponse(BaseModel):
    id: int
    name: str
    endpoint: str
    method: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=255)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]

class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    endpoint: str | None = Field(default=None, min_length=1, max_length=255)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] | None = None
    is_active: bool | None = None


class MonitoringLogCreate(BaseModel):
    status_code: int
    response_time: int
    is_healthy: bool = True


class MonitoringLogResponse(BaseModel):
    id: int
    service_id: int
    status_code: int
    response_time: int
    is_healthy: bool
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=6, max_length=100)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)



class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


