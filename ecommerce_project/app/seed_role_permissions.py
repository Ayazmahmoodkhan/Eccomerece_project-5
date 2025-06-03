from app.database import SessionLocal
from app.models import Role, Permission
from sqlalchemy.orm import Session

def seed_roles_and_permissions(db: Session):
    permissions = [
        "view_products", "add_product", "edit_product", "delete_product",
        "view_orders", "edit_orders", "manage_users", "assign_roles",
        "view_dashboard", "process_refunds", "apply_discount", "post_review"
    ]

    # Create permissions if not exist
    created_permissions = []
    for perm in permissions:
        if not db.query(Permission).filter_by(name=perm).first():
            created = Permission(name=perm)
            db.add(created)
            created_permissions.append(created)

    db.commit()
    all_permissions = db.query(Permission).all()

    # Define role-permission mapping
    role_definitions = {
        "admin": all_permissions,
        "manager": [p for p in all_permissions if p.name in [
            "view_products", "add_product", "edit_product", "delete_product",
            "view_orders", "edit_orders", "view_dashboard", "process_refunds"
        ]],
        "customer": [p for p in all_permissions if p.name in [
            "view_products", "post_review", "apply_discount"
        ]],
        "vendor": [p for p in all_permissions if p.name in [
            "view_products", "add_product", "edit_product", "delete_product",
            "view_orders"
        ]],
        "staff": [p for p in all_permissions if p.name in [
            "view_products", "view_orders", "edit_orders"
        ]]
    }

    # Create roles if not exist
    created_roles = []
    for role_name, perms in role_definitions.items():
        if not db.query(Role).filter_by(name=role_name).first():
            new_role = Role(name=role_name, permissions=perms)
            db.add(new_role)
            created_roles.append(new_role)

    db.commit()
    return {
        "permissions_created": len(created_permissions),
        "roles_created": len(created_roles),
        "message": "Seeding completed successfully."
    }

# Optional CLI run
if __name__ == "__main__":
    db = SessionLocal()
    try:
        result = seed_roles_and_permissions(db)
        print(result)
    finally:
        db.close()
