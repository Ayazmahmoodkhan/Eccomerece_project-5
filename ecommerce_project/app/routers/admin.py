from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.schemas import  UserCreate
from app.auth import get_current_user
from app.utils import pwd_context, has_permission
from typing import List, Optional
from app.database import get_db
from app.seed_role_permissions import seed_roles_and_permissions
from app.models import User, Product, Order, Category, Refund, Review, PaymentMethod, PaymentMode, UserProfile, ShippingDetails, Payment, OrderStatus, ProductVariant
from app.schemas import ProductCreate, OrderUpdate, CategoryResponse, RefundResponse, ReviewResponse, ReviewUpdate, UserUpdate
from datetime import datetime, timedelta


router = APIRouter(prefix="/admin", tags=["Admin Panel"])

@router.post("/seed-roles-permissions")
def seed_roles_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not has_permission(current_user, "assign_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    
    result = seed_roles_and_permissions(db)
    return {"message": "Roles and permissions seeded successfully", "result": result}

@router.post("/create-admin")
def create_admin(user: UserCreate, db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create another admin.")
    existing_admin = db.query(User).filter(User.email == user.email).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin with this email already exists.")

    hashed_password = pwd_context.hash(user.password)
    new_admin = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role="admin",
        is_active=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message": "Admin account created successfully"}

def admin_required(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Admin Profile & Stats
from sqlalchemy import func
@router.get("/admin-profile")
def get_admin_profile(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_sales = db.query(Order).filter(Order.order_status == "delivered").count()
    total_revenue = db.query(func.sum(Order.order_amount)).filter(Order.order_status == "delivered").scalar()
  #  total_revenue = db.query(Order).filter(Order.order_status == "delivered").with_entities(Order.order_amount).sum()

    return {
        "admin_name": admin.name,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "total_revenue": total_revenue
    }
#category 
@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories
#Product Management

#Order Management
@router.get("/orders")
def get_orders(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return {"orders": orders}
# Get single Order by ID with Items
@router.put("/orders/{order_id}")
def update_order_status(order_id: int, order_update: OrderUpdate, admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.order_status = order_update.order_status
    db.commit()
    db.refresh(order)
    return {"msg": "Order status updated successfully", "order": order}

# Admins checks refunds 
@router.get("/refunds", response_model=List[RefundResponse])
def get_all_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    refunds = db.query(Refund).all()
    return refunds


# Delete reviews by admin
@router.delete("/reviews/{review_id}")
def delete_review(review_id: int, admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review: 
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)   
    db.commit()  
    return {"msg": "Review deleted successfully"}
# User Management
@router.get("/users")
def get_users(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == "user").all()
    return {"users": users}

@router.put("/user/{user_id}")
def block_unblock_user(user_id:int,user_update:UserUpdate,admin:User=Depends(admin_required),db:Session=Depends(get_db)):
    user=db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot block/unblock an admin user.")
    if user.is_active==user_update.is_active:
        return {
            "msg": f"User is already {'active' if user.is_active else 'inactive'}",
            "user": {"id": user.id, "is_active": user.is_active}
        }
    
    user.is_active=user_update.is_active
    db.commit()
    db.refresh(user)
    return {"msg":"user status update successfully", "user": {"id":user.id,"is_active":user.is_active}}
#Reports & Analytics
@router.get("/reports")
def get_reports(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    total_revenue = db.query(func.sum(Order.order_amount)).filter(Order.order_status == "delivered").scalar()
    total_orders = db.query(Order).count()
    total_users = db.query(User).filter(User.role == "user").count()

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_users": total_users
    }

def seed_payment_methods(db: Session):
    for method in PaymentMode:
        exists = db.query(PaymentMethod).filter_by(method=method).first()
        if not exists:
            db.add(PaymentMethod(method=method, enabled=True))
    db.commit()
@router.post("/seed-payment-methods")
def seed_payment_endpoint(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    seed_payment_methods(db)
    return {"message": "Payment methods seeded successfully"}
@router.get("/payment-methods/enabled", response_model=List[str])
def get_enabled_payment_methods(db: Session = Depends(get_db)):
    enabled_methods = db.query(PaymentMethod).filter_by(enabled=True).all()
    return [m.method.value for m in enabled_methods]
@router.put("/{method}/toggle")
def toggle_payment_method(
    method: PaymentMode,
    enable: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)  # Only admin!
):
    payment_method = db.query(PaymentMethod).filter_by(method=method).first()
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    payment_method.enabled = enable
    db.commit()
    return {"message": f"{method.value} {'enabled' if enable else 'disabled'}"}



# Check Monthly Orders
@router.get("/monthly-orders")
def get_monthly_orders(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    from datetime import datetime
    from sqlalchemy import extract

    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint.")

    current_year = datetime.now().year
    monthly_orders = (
        db.query(extract('month', Order.order_date).label('month'), func.count(Order.id).label('order_count'))
        .filter(extract('year', Order.order_date) == current_year)
        .group_by(extract('month', Order.order_date))
        .order_by(extract('month', Order.order_date))
        .all()
    )

    result = {int(month): count for month, count in monthly_orders}

    return {"monthly_orders": result}

from sqlalchemy import desc

# Check Purchased Products in the last 30 days


@router.get("/purchased-products-last-30-days")
def get_purchased_products_last_30_days(
    city: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    admin: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint.")

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    query = (
        db.query(
            Order.id.label("order_id"),
            Order.order_date,
            User.id.label("user_id"),
            User.email,
            User.name.label("fallback_name"),
            UserProfile.first_name,
            UserProfile.last_name,
            UserProfile.profile_picture
        )
        .join(User, User.id == Order.user_id)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .join(ShippingDetails, ShippingDetails.order_id == Order.id)
        .filter(Order.order_date >= thirty_days_ago)
        .order_by(desc(Order.order_date))
    )

    if limit:
        query = query.offset(offset).limit(limit)

    if city:
        query = query.filter(ShippingDetails.city.ilike(f"%{city}%"))

    orders = query.all()

    results = []
    for order in orders:
        full_name = (
            f"{order.first_name or ''} {order.last_name or ''}".strip()
            if order.first_name or order.last_name
            else order.fallback_name
        )

        results.append({
            "order_id": order.order_id,
            "order_date": order.order_date,
            "user_full_name": full_name,
            "user_profile_pic": order.profile_picture
        })

    return {
        "purchased_products_last_30_days": results
    }



# Check how many order confirm with Stripe, COD and Paypal

@router.get("/orders/payment-summary")
def get_order_payment_summary(
    admin: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this Payment Summary.")

    results = (
        db.query(Payment.payment_method, func.count(Payment.id))
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.order_status != OrderStatus.cancelled) 
        .group_by(Payment.payment_method)
        .all()
    )

    summary = {
        "Stripe": 0,           
        "Paypal": 0,
        "Cash on Delivery": 0
    }

    for method, count in results:
        if method in [PaymentMode.credit_card.value, PaymentMode.debit_card.value]:
            summary["Stripe"] += count
        elif method == PaymentMode.paypal.value:
            summary["Paypal"] += count
        elif method == PaymentMode.cash_on_delivery.value:
            summary["Cash on Delivery"] += count

    return {
        "status": "success",
        "summary": summary
    }


@router.get("/dashboard-summary")
def get_dashboard_summary(admin: User = Depends(admin_required), db: Session = Depends(get_db)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this Dashboard Summary.")

    total_products = db.query(Product).count()
    total_users = db.query(User).filter(User.role == "user").count()
    total_reviews = db.query(Review).count()
    total_pending_orders = db.query(Order).filter(Order.order_status == "pending").count()
    out_of_stock_products = db.query(Product).filter(
        ~Product.variants.any(ProductVariant.stock > 0)
    ).count()

    total_categories = db.query(Category).count()
    total_orders = db.query(Order).count()

    return {
        "total_products": total_products,
        "total_users": total_users,
        "total_reviews": total_reviews,
        "total_pending_orders": total_pending_orders,
        "out_of_stock_products": out_of_stock_products,
        "total_categories": total_categories,
        "total_orders": total_orders
    }