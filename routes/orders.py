from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/orders",
    tags=["orders"]
)

@router.post("/", response_model=schemas.Order)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Processing order request for user ID: {current_user['id']}")
        logger.info(f"Order items: {order.items}")
        
        # Calculate total amount and validate inventory
        total_amount = 0
        order_items = []
        
        for item in order.items:
            inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item.inventory_id).first()
            if not inventory_item:
                logger.error(f"Inventory item {item.inventory_id} not found")
                raise HTTPException(status_code=404, detail=f"Inventory item {item.inventory_id} not found")
            
            # Only check inventory levels for customer orders, not purchase orders
            if not order.is_purchase_order:
                if inventory_item.quantity < item.quantity:
                    logger.error(f"Not enough stock for {inventory_item.name}, requested: {item.quantity}, available: {inventory_item.quantity}")
                    raise HTTPException(status_code=400, detail=f"Not enough stock for {inventory_item.name}")
            
            total_amount += inventory_item.price * item.quantity
            order_items.append({
                "inventory_id": item.inventory_id,
                "quantity": item.quantity,
                "price_at_time": inventory_item.price
            })
        
        # Create order
        logger.info(f"Creating order with total amount: {total_amount}")
        db_order = models.Order(
            user_id=current_user['id'],
            status="pending",
            total_amount=total_amount,
            supplier=order.supplier,
            expected_delivery_date=order.expected_delivery_date,
            notes=order.notes,
            is_purchase_order=order.is_purchase_order
        )
        db.add(db_order)
        db.flush()  # Get the order ID
        
        # Create order items and update inventory
        for item in order_items:
            db_order_item = models.OrderItem(
                order_id=db_order.id,
                inventory_id=item["inventory_id"],
                quantity=item["quantity"],
                price_at_time=item["price_at_time"]
            )
            db.add(db_order_item)
            
            # Update inventory quantity for customer orders only
            if not order.is_purchase_order:
                inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item["inventory_id"]).first()
                inventory_item.quantity -= item["quantity"]
        
        db.commit()
        db.refresh(db_order)
        logger.info(f"Order created successfully with ID: {db_order.id}")
        return db_order
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.rollback()
        raise

@router.get("/", response_model=List[schemas.Order])
def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Getting orders for user: {current_user['username']}, admin: {current_user['is_admin']}")
        
        if current_user.get('is_admin'):
            orders = db.query(models.Order).all()
            logger.info(f"Admin user - fetching all orders")
        else:
            orders = db.query(models.Order).filter(models.Order.user_id == current_user['id']).all()
            logger.info(f"Regular user - fetching orders for user_id {current_user['id']}")
        
        logger.info(f"Retrieved {len(orders)} orders for user {current_user['id']}")
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        logger.exception("Detailed exception information:")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@router.get("/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not current_user.get('is_admin') and order.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch order")

@router.patch("/{order_id}", response_model=schemas.Order)
def update_order_status(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not current_user.get('is_admin'):
            raise HTTPException(status_code=403, detail="Only admins can update order status")
        
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # If a purchase order is being marked as delivered, increase inventory
        if order.is_purchase_order and order_update.status == "delivered" and order.status != "delivered":
            try:
                for item in order.items:
                    inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item.inventory_id).first()
                    if inventory_item:
                        inventory_item.quantity += item.quantity
                        logger.info(f"Increased inventory for {inventory_item.name} by {item.quantity} units")
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating inventory: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to update inventory")
        
        order.status = order_update.status
        db.commit()
        db.refresh(order)
        return order 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update order status") 