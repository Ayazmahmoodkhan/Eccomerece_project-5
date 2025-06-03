import os
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.models import User, Order
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    USE_CREDENTIALS=True,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    VALIDATE_CERTS=True,
)


# Background Email Sending Function
def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    login_url = "https://192.168.1.32/login" 
    html_body = f"""
    <html>
        <body>
            <h1>{body.get("title", "No Title")}</h1>
            <p>Hello {body.get("name", "User")},</p>
            <p>Thank you for signing up. We're excited to have you on board!</p>

            <p>Click the link below to log in:</p>
            <p><a href="{login_url}" style="padding:10px 20px; background-color:blue; color:white; text-decoration:none; border-radius:5px;">
            Login to Your Account</a></p>

            <p>Feel free to explore our platform and reach out if you have any questions.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_body,  
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

# payment confirmation email

def send_payment_confirmation(background_tasks: BackgroundTasks, email_to: str, name: str, order_id: int, amount: float):
    subject = "Payment Confirmation - Order #" + str(order_id)
    body = {
        "title": "Payment Successful",
        "name": name,
        "order_id": order_id,
        "amount": f"${amount / 100:.2f}",
    }

    send_email_background(background_tasks, subject, email_to, body)

# Admin Notification Email on New Order 

def send_order_notification_to_admin(background_tasks: BackgroundTasks, db: Session, current_user: User, created_order: Order):
    admin_user = db.query(User).filter(User.role == "admin").first()

    if not admin_user:
        return  

    product_summary = {}
    for item in created_order.order_items:
        product_name = item.variant.product.product_name
        variant_attr = item.variant.attributes
        key = f"{product_name} - {variant_attr}"
        if key in product_summary:
            product_summary[key] += item.quantity
        else:
            product_summary[key] = item.quantity

    items_html = """
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
            <tr>
                <th>Product</th>
                <th>Quantity</th>
            </tr>
        """
    for name, qty in product_summary.items():
        items_html += f"""
        <tr>
            <td>{name}</td>
            <td>{qty} unit(s)</td>
        </tr>
        """
    items_html += "</table>"


    body = {
        "title": f"New Order Received - Order #{created_order.id}",
        "name": admin_user.name,
    }


    body["admin_email"] = admin_user.email

    html_body = f"""
    <html>
        <body>
            <h2>{body.get("title")}</h2>
            <p>Placed by: {current_user.name} ({current_user.email})</p>
            <p>Order ID: <strong>{created_order.id}</strong></p>
            <p>Ordered Items:</p>
            <ul>{items_html}</ul>
            <p><strong>Total Payment:</strong> ${created_order.final_amount:.2f}</p>
            <p><strong>Shipping Date:</strong> {created_order.shipping_date.strftime('%Y-%m-%d')}</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=body["title"],
        recipients=[admin_user.email],
        body=html_body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)