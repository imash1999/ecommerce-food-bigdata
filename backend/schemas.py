from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class RestaurantCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    price_range: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    address: str | None = None
    zip_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None


class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price_range: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    address: str | None = None
    zip_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    is_active: bool | None = None


class DishCreate(BaseModel):
    name: str
    price: float
    description: str | None = None
    category_id: int | None = None
    image_url: str | None = None


class DishUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None
    category_id: int | None = None
    image_url: str | None = None
    is_available: bool | None = None


class OrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    dish_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restaurant_id: int = Field(gt=0)
    delivery_address: str
    items: list[OrderItemRequest]
    idempotency_key: UUID
