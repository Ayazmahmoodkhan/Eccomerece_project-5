from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import Order, Payment, Refund, User, RefundStatus, PaymentLog
from app.database import get_db
from app.auth import get_current_user
from app.schemas import RefundRequest, RefundResponse  # Tum bana chuke ho
import stripe, paypalrestsdk, json
from app.config import Settings
import logging
router = APIRouter(prefix="/refunds", tags=["Refunds"])

# ------------------------
# 1. User Refund Request
# ------------------------
@router.post("/request", response_model=RefundResponse)
def request_refund(
    data: RefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == data.order_id, Order.user_id == current_user.id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.order_status.name not in ["delivered", "shipped"]:
        raise HTTPException(status_code=400, detail="Refund allowed only after delivery/shipping")
    
    if order.created_timestamp < datetime.utcnow() - timedelta(days=15):
        raise HTTPException(status_code=400, detail="15-day refund window expired")

    existing_refund = db.query(Refund).filter(Refund.order_id == order.id).first()
    if existing_refund:
        raise HTTPException(status_code=400, detail="Refund already requested")

    refund = Refund(
        order_id=order.id,
        stripe_refund_id="pending",
        amount=order.final_amount,
        reason=data.reason,
        status="requested"
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)

    return refund



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def get_settings():
    return Settings()

@router.post("/approve/{refund_id}")
async def approve_refund(refund_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), settings: Settings = Depends(get_settings)):
    if current_user.role != "admin":
        raise HTTPException(403, "Not authorized")

    logger.info(f"Querying refund id={refund_id}")
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise HTTPException(404, "Refund not found")
    if refund.status != "requested":
        raise HTTPException(400, "Refund already processed")

    payment = db.query(Payment).filter(Payment.order_id == refund.order_id).first()
    if not payment or payment.amount <= 0:
        raise HTTPException(400, "Invalid payment")
    if payment.status != "succeeded":
        raise HTTPException(400, "Cannot refund failed payment")

    try:
        with db.begin_nested():
            if payment.payment_method in ["Credit Card", "Debit Card"]:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                if not intent.charges.data:
                    refund.status = "rejected"
                    refund.stripe_refund_id = f"no_charge_{payment.stripe_payment_intent_id}"
                    db.add(PaymentLog(payment_id=payment.id, status="refund_failed", message="No charge found"))
                    db.add(refund)
                    db.commit()
                    raise HTTPException(400, "No charge found")

                charge = intent.charges.data[0]
                if charge.refunded:
                    refund.stripe_refund_id = charge.refunds.data[0].id if charge.refunds.data else f"already_refunded_{charge.id}"
                    refund.status = "approved"
                    db.add(PaymentLog(payment_id=payment.id, status="refund_approved", message=f"Charge {charge.id} already refunded"))
                else:
                    stripe_refund = stripe.Refund.create(
                        charge=charge.id,
                        amount=int(payment.amount * 100),
                        idempotency_key=f"refund_{refund_id}"
                    )
                    refund.stripe_refund_id = stripe_refund.id
                    refund.status = "approved"
                    db.add(PaymentLog(payment_id=payment.id, status="refund_approved", message=f"Stripe refund: {stripe_refund.id}"))

            elif payment.payment_method == "paypal":
                paypalrestsdk.configure({
                    "mode": "sandbox",  # Change to "live" for production
                    "client_id": settings.paypal_client_id,
                    "client_secret": settings.paypal_client_secret
                })
                order = paypalrestsdk.Order.find(payment.paypal_payment_intent_id)
                if not order.transactions or not order.transactions[0].related_resources:
                    refund.status = "rejected"
                    refund.stripe_refund_id = f"no_capture_{payment.paypal_payment_intent_id}"
                    db.add(PaymentLog(payment_id=payment.id, status="refund_failed", message="No capture found"))
                    db.add(refund)
                    db.commit()
                    raise HTTPException(400, "No capture found")
                capture = order.transactions[0].related_resources[0].capture
                if capture.state != "completed":
                    refund.status = "rejected"
                    refund.stripe_refund_id = f"not_refundable_{payment.paypal_payment_intent_id}"
                    db.add(PaymentLog(payment_id=payment.id, status="refund_failed", message=f"Capture not refundable: {capture.state}"))
                    db.add(refund)
                    db.commit()
                    raise HTTPException(400, f"Capture not refundable: {capture.state}")

                paypal_refund = capture.refund({"amount": {"total": f"{payment.amount:.2f}", "currency": payment.currency}})
                if not paypal_refund.success():
                    raise HTTPException(400, f"PayPal refund failed: {paypal_refund.error}")
                refund.stripe_refund_id = f"paypal_{paypal_refund.id}"
                refund.status = "approved"
                db.add(PaymentLog(payment_id=payment.id, status="refund_approved", message=f"PayPal refund: {paypal_refund.id}"))

            elif payment.payment_method == "Cash on Delivery":
                refund.stripe_refund_id = f"manual_{refund_id}"
                refund.status = "approved"
                db.add(PaymentLog(payment_id=payment.id, status="refund_approved", message="Manual refund for COD"))

            else:
                raise HTTPException(400, "Unsupported payment method")

            refund.refunded_by = current_user.id
            db.add(refund)
            db.commit()

        return {"message": "Refund approved", "status": "success"}

    except stripe.error.InvalidRequestError as e:
        if e.code == "resource_missing":
            refund.status = "rejected"
            refund.stripe_refund_id = f"error_{payment.stripe_payment_intent_id}"
            db.add(PaymentLog(payment_id=payment.id, status="refund_failed", message="Invalid payment ID"))
            db.add(refund)
            db.commit()
            raise HTTPException(400, "Invalid payment ID")
        elif e.code == "charge_already_refunded":
            refund.status = "approved"
            refund.stripe_refund_id = f"already_refunded_{intent.charges.data[0].id}" if 'intent' in locals() else f"error_{refund_id}"
            db.add(PaymentLog(payment_id=payment.id, status="refund_approved", message="Charge already refunded"))
            db.add(refund)
            db.commit()
            raise HTTPException(400, "Already refunded")
        raise HTTPException(400, f"Stripe error: {str(e)}")
    except paypalrestsdk.exceptions.AuthorizationError:
        raise HTTPException(401, "PayPal authentication failed")
    except paypalrestsdk.exceptions.ResourceNotFound:
        refund.status = "rejected"
        refund.stripe_refund_id = f"error_{payment.paypal_payment_intent_id}"
        db.add(PaymentLog(payment_id=payment.id, status="refund_failed", message="PayPal payment not found"))
        db.add(refund)
        db.commit()
        raise HTTPException(404, "PayPal payment not found")
    except Exception as e:
        logger.error(f"Refund failed id={refund_id}: {str(e)}")
        raise HTTPException(400, f"Refund failed: {str(e)}")
# ------------------------
# 3. User or Admin: List My Refunds
# ------------------------
@router.get("/my-requests", response_model=list[RefundResponse])
def list_my_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):  
    if current_user.role == "user":
        refunds = db.query(Refund).join(Order).filter(Order.user_id == current_user.id).all()
    elif current_user.role == "admin":
        refunds = db.query(Refund).all()
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    return refunds