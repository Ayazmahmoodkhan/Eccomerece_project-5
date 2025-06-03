import os, csv, json
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models import Product, ProductVariant, ProductImage, Category
from app.database import get_db  
from app.celery_worker import celery_app

ERROR_DIR = "media/errors"
UPLOAD_DIR = "media/uploads"
get_db_session = get_db
@celery_app.task(name="process_bulk_upload")
def process_bulk_upload(content: str, image_data: dict, admin_id: int):
    session = get_db_session()
    decoded = content.splitlines()
    reader = csv.DictReader(decoded)

    error_rows = []
    success_count = 0
    product_cache = {}

    for idx, row in enumerate(reader):
        try:
            # Validate required fields 
            required_fields = ["product_name", "brand", "is_feature", "category_id", "description",
                               "price", "stock", "attributes", "image_filenames"]
            for field in required_fields:
                if not row.get(field):
                    raise ValueError(f"Missing required field '{field}'")

            product_name = row["product_name"].strip()
            brand = row["brand"].strip()
            is_feature = row["is_feature"].lower() == "true"
            category_id = int(row["category_id"])
            description = row["description"].strip()
            price = float(row["price"])
            stock = int(row["stock"])
            discount = int(row.get("discount", 0))
            shipping_time = int(row.get("shipping_time", 0))
            attributes = json.loads(row["attributes"])
            image_filenames = [img.strip() for img in row["image_filenames"].split(",")]

            category = session.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise ValueError(f"Category ID {category_id} does not exist")

            product_key = f"{product_name}_{category_id}"
            if product_key in product_cache:
                new_product = product_cache[product_key]
            else:
                new_product = Product(
                    sku=str(uuid4()),
                    product_name=product_name,
                    brand=brand,
                    is_feature=is_feature,
                    category_id=category_id,
                    description=description,
                    admin_id=admin_id
                )
                session.add(new_product)
                session.flush()
                session.refresh(new_product)
                product_cache[product_key] = new_product

            new_variant = ProductVariant(
                product_id=new_product.id,
                price=price,
                stock=stock,
                discount=discount,
                shipping_time=shipping_time,
                attributes=attributes
            )
            session.add(new_variant)
            session.flush()
            session.refresh(new_variant)

            for img_name in image_filenames:
                if img_name not in image_data:
                    raise ValueError(f"Image file '{img_name}' not found")
                image_bytes = bytes(image_data[img_name])
                save_path = os.path.join(UPLOAD_DIR, f"{uuid4().hex[:6]}_{img_name}")
                with open(save_path, "wb") as f:
                    f.write(image_bytes)
                image_url = f"/media/uploads/{os.path.basename(save_path)}"
                session.add(ProductImage(variant_id=new_variant.id, image_url=image_url))

            session.commit()
            success_count += 1

        except Exception as e:
            session.rollback()
            row["error"] = str(e)
            error_rows.append(row)

    error_file_path = None
    if error_rows:
        os.makedirs(ERROR_DIR, exist_ok=True)
        error_file_path = os.path.join(ERROR_DIR, f"errors_{uuid4().hex[:6]}.csv")
        with open(error_file_path, "w", newline="", encoding="utf-8") as err_file:
            writer = csv.DictWriter(err_file, fieldnames=reader.fieldnames + ["error"])
            writer.writeheader()
            writer.writerows(error_rows)

    return {
        "message": f"{success_count} variants uploaded successfully",
        "errors": len(error_rows),
        "error_file": error_file_path,
        "sample_errors": error_rows[:5]
    }



