"""库存管理API路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import InventoryItem
from backend.schemas import (
    InventoryItemCreate, InventoryItemUpdate,
    InventoryItemResponse, ApiResponse
)

router = APIRouter(prefix="/api/inventory", tags=["库存管理"])


@router.get("", response_model=list[InventoryItemResponse])
def get_inventory(
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[int] = None,
    low_stock: bool = False,
    db: Session = Depends(get_db)
):
    """获取库存列表"""
    query = db.query(InventoryItem)
    if class_id is not None:
        query = query.filter(InventoryItem.class_id == class_id)
    if low_stock:
        query = query.filter(InventoryItem.quantity <= InventoryItem.min_stock)
    items = query.order_by(InventoryItem.updated_at.desc()).offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """获取单个库存项"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="库存项不存在")
    return item


@router.post("", response_model=InventoryItemResponse)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    """创建库存项"""
    existing = db.query(InventoryItem).filter(
        InventoryItem.class_id == item.class_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该类别库存已存在，请使用更新接口")

    db_item = InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: int, item: InventoryItemUpdate, db: Session = Depends(get_db)):
    """更新库存项"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="库存项不存在")

    update_data = item.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.post("/{item_id}/inbound", response_model=ApiResponse)
def inbound_stock(item_id: int, quantity: int, db: Session = Depends(get_db)):
    """入库操作"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="入库数量必须大于0")
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="库存项不存在")
    item.quantity += quantity
    db.commit()
    return ApiResponse(success=True, message=f"入库{quantity}件成功，当前库存: {item.quantity}")


@router.post("/{item_id}/outbound", response_model=ApiResponse)
def outbound_stock(item_id: int, quantity: int, db: Session = Depends(get_db)):
    """出库操作"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="出库数量必须大于0")
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="库存项不存在")
    if item.quantity < quantity:
        raise HTTPException(status_code=400, detail=f"库存不足，当前库存: {item.quantity}")
    item.quantity -= quantity
    db.commit()
    return ApiResponse(success=True, message=f"出库{quantity}件成功，当前库存: {item.quantity}")


@router.delete("/{item_id}", response_model=ApiResponse)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """删除库存项"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="库存项不存在")
    db.delete(item)
    db.commit()
    return ApiResponse(success=True, message="库存项已删除")
