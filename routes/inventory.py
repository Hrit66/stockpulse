from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import SessionLocal
from ..models import InventoryItem
from ..schemas import InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse
from ..routes.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    return current_user

@router.get("/", response_model=list[InventoryItemResponse])
def read_items(page: int = 0, size: int = 10, db: Session = Depends(get_db)):
    try:
        items = db.query(InventoryItem).offset(page * size).limit(size).all()
        logger.info(f"Retrieved {len(items)} inventory items")
        return items
    except Exception as e:
        logger.error(f"Error retrieving inventory items: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory items")

@router.post("/", response_model=InventoryItemResponse)
def create_item(item: InventoryItemCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    try:
        db_item = InventoryItem(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Created new inventory item: {db_item.name}")
        return db_item
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create inventory item")

@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_item(item_id: int, item: InventoryItemUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    try:
        db_item = db.query(InventoryItem).get(item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        for key, value in item.dict().items():
            setattr(db_item, key, value)
        db.commit()
        logger.info(f"Updated inventory item: {db_item.name}")
        return db_item
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update inventory item")

@router.delete("/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    try:
        db_item = db.query(InventoryItem).get(item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(db_item)
        db.commit()
        logger.info(f"Deleted inventory item with ID: {item_id}")
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete inventory item")

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    try:
        total_items = db.query(InventoryItem).count()
        total_quantity = db.query(func.sum(InventoryItem.quantity)).scalar() or 0
        total_categories = db.query(func.count(func.distinct(InventoryItem.category))).scalar()
        out_of_stock = db.query(InventoryItem).filter(InventoryItem.quantity == 0).count()
        
        summary = {
            "totalItems": total_items,
            "totalQuantity": total_quantity,
            "totalCategories": total_categories,
            "outOfStock": out_of_stock
        }
        logger.info(f"Generated inventory summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating inventory summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate inventory summary")
