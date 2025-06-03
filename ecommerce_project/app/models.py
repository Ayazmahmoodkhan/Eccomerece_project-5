from sqlalchemy import Column, Integer, Table, String, JSON, Boolean,TIMESTAMP, text, Enum, Date, ForeignKey, Float, DateTime, Text
from app.database import Base
from sqlalchemy.sql import func
from datetime import datetime
import enum
from sqlalchemy.orm import relationship
from pydantic import ConfigDict

# Enums
class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    manager = "manager"
    vendor = "vendor"
    staff = "staff"


class OrderStatus(str, enum.Enum):
    pending = "Pending"
    confirmed = "Confirmed"
    shipped = "Shipped"
    delivered = "Delivered"
    cancelled = "Cancelled"

class PaymentMode(str, enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    paypal = "paypal"
    cash_on_delivery = "cash_on_delivery"



class RatingEnum(int, enum.Enum):
    one_star = 1
    two_star = 2
    three_star = 3
    four_star = 4
    five_star = 5

# website logo table
class WebsiteLogo(Base):
    __tablename__ = "website_logo"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    logo_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Role Table
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", back_populates="role")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


# User Table
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    addresses = relationship("Address", back_populates="user")
    products = relationship("Product", back_populates="admin")
    orders = relationship("Order", back_populates="user")
    # carts = relationship("Cart", back_populates="user")
    reviews = relationship("Review", back_populates="user")

# User Profile Table
class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    date_birth = Column(Date, nullable=False)
    phone = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    profile_picture = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

# Address Table
class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)

    user = relationship("User", back_populates="addresses")

# Category Table
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    products = relationship("Product", back_populates="category",cascade="all, delete")
    variant_attributes = relationship("CategoryVariantAttribute", back_populates="category")

class VariantAttribute(Base):
    __tablename__ = "variant_attributes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) 

    categories = relationship("CategoryVariantAttribute", back_populates="attribute")
class CategoryVariantAttribute(Base):
    __tablename__ = "category_variant_attributes"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    attribute_id = Column(Integer, ForeignKey("variant_attributes.id"))

    category = relationship("Category", back_populates="variant_attributes")
    attribute = relationship("VariantAttribute", back_populates="categories")

from sqlalchemy.dialects.postgresql import ARRAY
# Product Table 
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, nullable=False, unique=True)
    product_name = Column(String, nullable=False)
    description = Column(Text)
    brand = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_feature = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    admin = relationship("User", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

   
# PorductImage Table
class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"))
    image_url = Column(String, nullable=False)

    # Relationship
    variant = relationship("ProductVariant", back_populates="images")

#  Update: ProductVariant Table
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))

    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    discount = Column(Integer, default=0)
    shipping_time = Column(Integer, nullable=True)
    attributes = Column(JSON, nullable=True, default={})


    # Relationships
    product = relationship("Product", back_populates="variants")
    order_items = relationship("OrderItem", back_populates="variant")
    images = relationship("ProductImage", back_populates="variant", cascade="all, delete-orphan")

# Cart Table
# class Cart(Base):
#     __tablename__ = "carts"

#     id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
#     total_amount = Column(Float, nullable=False)
#     grand_total = Column(Float, nullable=False)

#     # Relationships
#     user = relationship("User", back_populates="carts")
#     cart_items = relationship("CartItem", back_populates="cart")


# CartItem Table
# class CartItem(Base):
#     __tablename__ = "cart_items"

#     id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
#     cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
#     product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     subtotal = Column(Float, nullable=False)

#     # Relationships
#     cart = relationship("Cart", back_populates="cart_items")
#     product = relationship("Product", back_populates="cart_items")


#Order Table
# class Order(Base):
#     __tablename__ = "orders"
    
#     id = Column(Integer, primary_key=True, index=True)
#     order_date = Column(DateTime, nullable=False)
#     order_amount = Column(Float, nullable=False)
#     shipping_date = Column(DateTime, nullable=True)
#     order_status = Column(Enum(OrderStatus), nullable=False)
#     is_canceled = Column(Boolean, default=False)
#     cancel_reason = Column(String, nullable=True)
#     coupon_code = Column(String, nullable=True)
#     discount_amount = Column(Float, default=0.0)
#     # cart_id = Column(Integer, ForeignKey("carts.id"))
#     user_id = Column(Integer, ForeignKey("users.id"))
#     created_timestamp = Column(DateTime, default=func.now())
#     updated_timestamp = Column(DateTime, default=func.now(), onupdate=func.now())

#     # Relationships
#     payment = relationship("Payment", back_populates="order", uselist=False)
#     user = relationship("User", back_populates="orders")
#     order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
#     shipping_details = relationship("ShippingDetails", back_populates="order", uselist=False)
#     refunds = relationship("Refund", back_populates="order", cascade="all, delete")

class Order(Base):
        __tablename__ = "orders"

        id = Column(Integer, primary_key=True, index=True)
        order_date = Column(DateTime, nullable=False, default=func.now())
        order_amount = Column(Float, nullable=False)  
        shipping_charge = Column(Float, default=0.0)
        discount_amount = Column(Float, default=0.0)
        final_amount = Column(Float, nullable=False)
        shipping_date = Column(DateTime, nullable=True)
        order_status = Column(Enum(OrderStatus), nullable=False)
        cancel_reason = Column(String, nullable=True)
        coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        created_timestamp = Column(DateTime, default=func.now())
        updated_timestamp = Column(DateTime, default=func.now(), onupdate=func.now())

        # Relationships
        user = relationship("User", back_populates="orders")
        order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
        shipping_details = relationship("ShippingDetails", back_populates="order", uselist=False)
        refunds = relationship("Refund", back_populates="order", cascade="all, delete")
        coupon = relationship("Coupon", back_populates="orders", uselist=False)
        payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

from sqlalchemy.sql import func
    # Order Item Table
class OrderItem(Base):
        __tablename__ = "order_items"
        
        id = Column(Integer, primary_key=True, index=True)
        order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
        product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
        variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)

        mrp = Column(Float, nullable=False)
        quantity = Column(Integer, nullable=False)
        total_price = Column(Float, nullable=False)  

        # Relationships
        order = relationship("Order", back_populates="order_items")
        product = relationship("Product", back_populates="order_items")
        variant = relationship("ProductVariant", back_populates="order_items")

       

# Review Table

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)
    description = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


# Payment Table
# class Payment(Base):
#     __tablename__ = "payments"
#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
#     payment_mode = Column(Enum(PaymentMode), nullable=False)
#     payment_date = Column(DateTime, nullable=False)

#     orders = relationship("Order", back_populates="payments")


    #searching for payment method and shipping details and use later


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    stripe_payment_intent_id = Column(String, nullable=True, unique=True)
    stripe_checkout_session_id = Column(String) 
    paypal_payment_intent_id = Column(String, nullable=True, unique=True)
    stripe_customer_id = Column(String, nullable=True)
    payment_method = Column(String, nullable=False)
    currency = Column(String, default="usd")
    amount = Column(Float, nullable=False)
    status = Column(String, default="processing")
    payment_ref = Column(String, nullable=True, unique=True)
    paid_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_timestamp = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_timestamp = Column(TIMESTAMP(timezone=True), onupdate=text("now()"))

   
    logs = relationship("PaymentLog", back_populates="payment", cascade="all, delete-orphan")
    order = relationship("Order", back_populates="payments")
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)


#payment log table    

class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    status = Column(String, nullable=False)  
    message = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    payment = relationship("Payment", back_populates="logs")



class ShippingDetails(Base):
    __tablename__ = "shipping_details"
    id = Column(Integer, primary_key=True, nullable=False)
    order_id = Column(
        Integer,
        ForeignKey(column="orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    full_name = Column(String, nullable=False)
    contact_information = Column(String, nullable=False)
    email = Column(String, nullable=False)
    postal_code = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    additional_note = Column(String, nullable=True)
    address = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    shipping_date = Column(TIMESTAMP(timezone=True))
    created_timestamp = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)

    order = relationship("Order", back_populates="shipping_details", uselist=False)

# Coupons table
class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    discount_type = Column(Enum("percentage", "fixed", name="discounttype"), nullable=False)
    discount_value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    expiry_date = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    orders = relationship("Order", back_populates="coupon")

# Refunds Table
class RefundStatus(str, enum.Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    stripe_refund_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(RefundStatus), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="refunds")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    method = Column(Enum(PaymentMode), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)