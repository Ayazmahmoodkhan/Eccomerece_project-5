from pydantic import BaseModel, EmailStr, Field, field_validator,condecimal, conint, ConfigDict, validator

from datetime import date,datetime
from enum import Enum
from typing import Optional, List, Any, Literal,Dict
from app.models import RatingEnum

# website logo schema
class WebsiteLogoBase(BaseModel):   
    name: str
    logo_path: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
class WebsiteLogoCreate(WebsiteLogoBase):
    pass
class WebsiteLogoUpdate(WebsiteLogoBase):
    name: Optional[str] = None
    logo_path: Optional[str] = None
class WebsiteLogoResponse(WebsiteLogoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)
    confirm_password: str = Field(..., min_length=6, max_length=20)

class UserLogin(BaseModel):
    username:str
    password:str

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    role: str

    model_config=ConfigDict(from_attributes=True)
class UserUpdate(BaseModel):
    is_active: bool

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password:str
#schemas for address form
class Addressbase(BaseModel):
    street:str
    city:str
    state:str
    postal_code:str
    country:str
class AddressCreate(Addressbase):
    pass
class AddressUpdate(Addressbase):
    pass
class AddressResponse(Addressbase):
    id:int
    user_id:int
    model_config = ConfigDict(from_attributes=True)
#end
#schema for user profile
class UserProfileBase(BaseModel):
    first_name: str
    last_name: str | None = None
    date_birth: date
    phone: str
    age: int
class UserProfileCreate(UserProfileBase):
    pass  

class UserProfileUpdate(UserProfileBase):
    pass  

class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
#end




# Category Base schema 
class CategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)



from decimal import Decimal
from typing_extensions import Annotated


# ---------------- Variant Schemas ----------------

class ProductVariantBase(BaseModel):
    price: Annotated[Decimal, Field(gt=0)]
    stock: Annotated[int, Field(ge=0)]
    discount: Optional[Annotated[int, Field(ge=0, le=100)]] = 0
    shipping_time: Optional[Annotated[int, Field(ge=0)]] = None
    attributes: Dict[str, Any]

class ProductVariantCreate(ProductVariantBase):
    images: List[str]

class ProductVariantResponse(ProductVariantBase):
    id: int
    images: List[str]

    @field_validator("images", mode="before")
    @classmethod
    def extract_image_paths(cls, value):
        if isinstance(value, list) and all(hasattr(i, "image_url") for i in value):
            return [i.image_url for i in value]
        return value

    model_config = ConfigDict(from_attributes=True)


# ---------------- Product Schemas ----------------

class ProductBase(BaseModel):
    product_name: str
    brand: str
    category_id: int
    description: str

    @field_validator("product_name", "brand", "description", mode="before")
    @classmethod
    def remove_extra_quotes(cls, value):
        return value.strip('"') if isinstance(value, str) else value

class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate]

class ProductResponse(ProductBase):
    id: int
    sku: str
    admin_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    variants: List[ProductVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------- Image Response ----------------

class ProductImageResponse(BaseModel):
    id: int
    image_url: str

    model_config = ConfigDict(from_attributes=True)


# Cart Item Schema

# class CartItemBase(BaseModel):
#     product_id: int
#     quantity: int
#     subtotal: float

# class CartItemCreate(CartItemBase):
#     pass

# class CartItemResponse(CartItemBase):
#     id: int
#     subtotal: float 

#     class Config:
#         from_attributes = True


# #  Cart Schemas

# class CartCreate(BaseModel):
#     cart_items: List[CartItemCreate]

# class CartUpdate(BaseModel):
#     cart_items: Optional[List[CartItemCreate]] = None

# class CartResponse(BaseModel):
#     id: int
#     total_amount: float 
#     grand_total: float  
#     created_at: datetime
#     cart_items: List[CartItemResponse]




# Order Enum

class OrderStatus(str, Enum):
    pending = "pending"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# # OrderItem Schema
# class OrderItemBase(BaseModel):
#     product_id: int
#     mrp: float
#     quantity: int

# class OrderItemCreate(OrderItemBase):
#     pass

# class OrderItem(OrderItemBase):
#     id: int

#     class Config:
#         orm_mode = True

# # Order Schema
# class OrderBase(BaseModel):
#     order_date: datetime
#     order_amount: float
#     shipping_date: Optional[datetime] = None
#     order_status: OrderStatus

# class OrderCreate(OrderBase):
#     cart_id: int
#     user_id: int
#     items: List[OrderItemCreate]  # nested order items

# class OrderResponse(OrderBase):
#     id: int
#     created_timestamp: datetime
#     updated_timestamp: datetime
#     items: List[OrderItem] = Field(..., alias="order_items")

#     class Config:
#         orm_mode = True
#         allow_population_by_field_name = True 

# class OrderUpdate(BaseModel):
#     order_date: Optional[datetime] = None
#     order_amount: Optional[float] = None
#     shipping_date: Optional[datetime] = None
#     order_status: Optional[OrderStatus] = None

#     class Config:
#         orm_mode = True
# # Cancel order request
# class OrderCancelRequest(BaseModel):
#     cancel_reason: Optional[str] = None

# class OrderCancelResponse(BaseModel):
#     id: int
#     is_canceled: bool
#     cancel_reason: Optional[str]

#     class Config:
#         orm_mode = True
# # Apply Coupon Request in Order

# class ApplyCouponRequest(BaseModel):
#     coupon_code: str

# # Coupons Schema

# class CouponBase(BaseModel):
#     code: str
#     discount_type: Literal["percentage", "fixed"]
#     discount_value: float
#     expiry_date: Optional[datetime] = None
#     usage_limit: Optional[int] = None

# class CouponCreate(CouponBase):
#     pass

# class CouponResponse(CouponBase):
#     id: int
#     is_active: bool

#     class Config:
#         orm_mode = True

# shipping details schema 

#  Base schema (no order_id here)
class ShippingDetailsBase(BaseModel):
    full_name: str
    email: EmailStr
    contact_information: str
    additional_note: Optional[str] = None
    address: str
    state: str
    city: str                     
    country: str
    postal_code: int             
    shipping_date: Optional[datetime] = None

#  Create schema (inherits base, no order_id)
class ShippingDetailsCreate(ShippingDetailsBase):
    pass

#  Update schema 
class ShippingDetailsUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_information: Optional[str] = None
    additional_note: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[int] = None
    shipping_date: Optional[datetime] = None

# Shipping Response schema 
class ShippingDetailsResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    full_name: str
    email: EmailStr
    contact_information: str
    additional_note: Optional[str] = None
    address: str
    state: str
    city: str
    country: str
    postal_code: int
    shipping_date: Optional[datetime] = None
    created_timestamp: Optional[datetime] = None
    updated_timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)




# -------- Order Status Enum --------
class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"





# -------- OrderItem Schemas --------
class OrderItemBase(BaseModel):
    product_id: int
    variant_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    variant_id: int
    quantity: int
    total_price: float
    product_name: Optional[str] = None  # Name of the product
    variant_attributes: Optional[Dict[str, Any]] = None  # Variant-specific attributes
    variant_image: Optional[str] = None  # First image of the variant (if any)

    model_config = ConfigDict(from_attributes=True)


# -------- Order Schemas --------
class OrderBase(BaseModel):
    order_date: datetime = Field(default_factory=datetime.utcnow)
    shipping_date: Optional[datetime] = None
    order_status: OrderStatus = OrderStatus.pending
    coupon_id: Optional[int] = None

class OrderCreate(OrderBase):
    order_items: List[OrderItemCreate]
    shipping_details: ShippingDetailsCreate

class OrderStatusResponse(BaseModel):
    order_id: int
    status: str

class OrderResponse(OrderBase):
    id: int
    user_id: int
    user: Optional[UserResponse]
    order_amount: float
    shipping_charge: float = 0  # If you're not yet using this in logic, keep default 0
    discount_amount: float
    final_amount: float
    cancel_reason: Optional[str]
    created_timestamp: datetime
    updated_timestamp: datetime
    order_items: List[OrderItemResponse]
    shipping_details: Optional[ShippingDetailsResponse] = None
    order_status: OrderStatus

    @validator("order_status", pre=True)
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    order_status: Optional[OrderStatus] = None
    cancel_reason: Optional[str] = None
    shipping_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------- Cancel Order --------
class OrderCancelRequest(BaseModel):
    cancel_reason: Optional[str] = None

class OrderCancelResponse(BaseModel):
    id: int
    cancel_reason: Optional[str]
    order_status: OrderStatus

    model_config = ConfigDict(from_attributes=True)


# -------- Coupon Schemas --------
class CouponBase(BaseModel):
    code: str
    discount_type: Literal["percentage", "fixed"]
    discount_value: float
    expiry_date: Optional[datetime] = None
    usage_limit: Optional[int] = None

class CouponCreate(CouponBase):
    pass

class CouponResponse(CouponBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ApplyCouponRequest(BaseModel):
    coupon_code: str


# -------- Order Tracking --------
class OrderTrackingResponse(BaseModel):
    order_id: int
    order_status: str
    message: str
    countdown: Optional[str] = None

#end new schemas


# Create Review Schema
class ReviewCreate(BaseModel):
    product_id: int
    rating: int 
    description: str
    email: EmailStr

class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    email: str
    rating: int
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Response Review Schema
class ProductReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    email: str
    rating: int
    description: str
    created_at: datetime
    full_name: str                      
    profile_picture: Optional[str] = None      

    model_config = ConfigDict(from_attributes=True)

# Update Review Schema
class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(ge=1, le=5)
    description: Optional[str] = Field(max_length=500)

    
    model_config = ConfigDict(from_attributes=True)  # added for model config
# schema for payment table
import enum
class PaymentMode(str, enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    paypal = "paypal"
    cash_on_delivery = "cash_on_delivery"



class PaymentBase(BaseModel):
    order_id: int
    stripe_payment_intent_id: Optional[str] = None
    paypal_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id:Optional[str]=None
    stripe_customer_id: Optional[str] = None
    payment_method: PaymentMode
    currency: Optional[str] = "usd"
    amount: float
    status: Optional[str] = "processing"
    payment_ref: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentCreate(PaymentBase):
    pass

class PaymentIntentRequest(BaseModel):
    order_id: int
    currency: str = "usd"
    payment_method: PaymentMode

class PaymentResponse(PaymentBase):
    id: int
    created_timestamp: datetime
    updated_timestamp: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
class StripeCheckoutResponse(BaseModel):
    payment_id: int
    order_id: int
    checkout_url: str
    message: Optional[str] = None
    amount: float
    status: str
# schema for payments logs

class PaymentLogCreate(BaseModel):
    payment_id: int
    status: str
    message: Optional[str] = None


class PaymentLogResponse(PaymentLogCreate):
    id: int
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

# Refund Payments Schema

class RefundRequest(BaseModel):
    order_id: int
    reason: Optional[str] = None

class RefundResponse(BaseModel):
    id: int
    order_id: int
    checkout_url: str
    amount: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# refund response
class RefundResponse(BaseModel):
    id: int
    payment_id: int
    amount: float
    status: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)





