from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import OrderStatus


class OrderCreated(BaseModel):
    id: str
    status: OrderStatus


class OrderFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    file_size: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    phone: str
    comment: str | None
    files: list[OrderFileOut]
    status: OrderStatus
    price: float | None
    created_at: datetime
    updated_at: datetime


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    price: float | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminMe(BaseModel):
    username: str
