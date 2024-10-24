from fastapi import Body, Depends, FastAPI, Response, status, HTTPException, Depends, APIRouter
from . import oauth2
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
import random
import string
from ..config import settings
from .. import models
from typing import List

router = APIRouter(prefix="/payment-links", tags=["Payment Links"])


def generate_random_link(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# This route retrieves and builds the form on the frontend!
@router.get("/{link_code}")
def get_link_by_code(link_code: str, db: Session = Depends(get_db)):
    link = db.query(models.PaymentLink).filter(models.PaymentLink.link_code == link_code).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found!")
    return link

@router.post("/", status_code=status.HTTP_201_CREATED, response_model= schemas.PaymentLinkOut)
def create_payment_link(link: schemas.PaymentLinkCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """Create a new link"""
    generated_link_code = generate_random_link()
    generated_link_url = f"{settings.client_url}/pay/{generated_link_code}"

    new_link = models.PaymentLink(user_id=current_user.id, link_url=generated_link_url, link_code=generated_link_code, **link.dict())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

@router.get("/", response_model=List[schemas.PaymentLinkOut])
def get_payment_links(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    links = db.query(models.PaymentLink).filter(models.PaymentLink.user_id == current_user.id).all()
    return links



@router.get("/{id}", response_model=schemas.PaymentLinkOut)
def get_payment_link(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found!")
    return link

@router.put("/{id}", response_model=schemas.PaymentLinkOut)
def update_payment_link(id: int, link_update: schemas.PaymentLinkUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found!')
    
    # update the fields
    for field, value in link_update.dict(exclude_unset=True).items():
        setattr(link, field, value)
    
    db.commit()
    db.refresh(link)
    return link

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_link(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment link not found")
    
    db.delete(link)
    db.commit()
    return {"message": "Link deleted successfully!"}


