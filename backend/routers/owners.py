from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend import models, auth

router = APIRouter(prefix="/api/owners", tags=["owners"])


class RegisterRequest(BaseModel):
    name: str
    shop_name: str
    phone: str
    email: Optional[str] = None
    password: str
    whatsapp_number: Optional[str] = None


class LoginRequest(BaseModel):
    phone: str
    password: str


class OwnerResponse(BaseModel):
    id: int
    name: str
    shop_name: str
    phone: str
    email: Optional[str]
    whatsapp_number: Optional[str]

    class Config:
        from_attributes = True


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.Owner).filter(models.Owner.phone == req.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    owner = models.Owner(
        name=req.name,
        shop_name=req.shop_name,
        phone=req.phone,
        email=req.email,
        password_hash=auth.hash_password(req.password),
        whatsapp_number=req.whatsapp_number or req.phone,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    token = auth.create_access_token({"sub": str(owner.id)})
    return {"access_token": token, "token_type": "bearer", "owner": OwnerResponse.model_validate(owner)}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.phone == req.phone).first()
    if not owner or not auth.verify_password(req.password, owner.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = auth.create_access_token({"sub": str(owner.id)})
    return {"access_token": token, "token_type": "bearer", "owner": OwnerResponse.model_validate(owner)}


@router.get("/me", response_model=OwnerResponse)
def get_me(current_owner: models.Owner = Depends(auth.get_current_owner)):
    return current_owner


@router.put("/me")
def update_profile(
    name: Optional[str] = None,
    shop_name: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_owner: models.Owner = Depends(auth.get_current_owner),
):
    if name:
        current_owner.name = name
    if shop_name:
        current_owner.shop_name = shop_name
    if whatsapp_number:
        current_owner.whatsapp_number = whatsapp_number
    db.commit()
    return {"message": "Profile updated"}
