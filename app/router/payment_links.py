from fastapi import Body, Depends, FastAPI, Response, status, HTTPException, Depends, APIRouter, Query
from . import oauth2
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
import random
import string
from ..config import settings
from .. import models
from typing import List
from ..logger import logger

router = APIRouter(prefix="/api/payment-links", tags=["Payment Links"])


def generate_random_link(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# This route retrieves and builds the form on the frontend!
@router.get("/{link_code}")
def get_link_by_code(link_code: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching link with code: {link_code}")
    link = db.query(models.PaymentLink).filter(models.PaymentLink.link_code == link_code).first()
    if not link:
        logger.warning(f"Link with code {link_code} not found!")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found!")
    return link

@router.post("/", status_code=status.HTTP_201_CREATED, response_model= schemas.PaymentLinkOut)
def create_payment_link(link: schemas.PaymentLinkCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """Create a new link"""
    generated_link_code = generate_random_link()
    generated_link_url = f"{settings.client_url}/pay/{generated_link_code}"


    logger.info(f"Creating a new payment link for user ID {current_user.id}")
    new_link = models.PaymentLink(user_id=current_user.id, link_url=generated_link_url, link_code=generated_link_code, **link.dict())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    logger.info(f"Payment link created successfully with ID: {new_link.id}")
    return new_link

# GET /links/?start_date=2024-01-01&end_date=2024-10-23&currency=USD&status=active

@router.get("/", response_model=List[schemas.PaymentLinkOut])
def get_payment_links(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), currency: str = Query(None, description="Filter By Currency e.g (USD)")):
    logger.info(f"Fetching payment links for user ID {current_user.id} with currency filter: {currency}")    
    query = db.query(models.PaymentLink).filter(models.PaymentLink.user_id == current_user.id)
    if currency:
        query = query.filter(models.PaymentLink.currency == currency)
    
    links = query.all()
    logger.info(f"Retrieved {len(links)} payment links for user ID {current_user.id}")
    
    return links



@router.get("/{id}", response_model=schemas.PaymentLinkOut)
def get_payment_link(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), ):
    logger.info(f"Fetching payment link with ID: {id} for user ID {current_user.id}")
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    
    if not link:
        logger.warning(f"Payment link with ID {id} not found for user ID {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found!")
    return link

@router.put("/{id}", response_model=schemas.PaymentLinkOut)
def update_payment_link(id: int, link_update: schemas.PaymentLinkUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    logger.info(f"Updating payment link with ID {id} for user ID {current_user.id}")
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    if not link:
        logger.warning(f"Payment link with ID {id} not found for user ID {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found!')
    
    # update the fields
    for field, value in link_update.dict(exclude_unset=True).items():
        setattr(link, field, value)
    
    db.commit()
    db.refresh(link)
    logger.info(f"Payment link with ID {id} updated successfully for user ID {current_user.id}")
    return link

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_link(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    logger.info(f"Attempting to delete payment link with ID {id} for user ID {current_user.id}")
    link = db.query(models.PaymentLink).filter(models.PaymentLink.id == id, models.PaymentLink.user_id == current_user.id).first()
    
    if not link:
        logger.warning(f"Payment link with ID {id} not found for user ID {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment link not found")
    
    db.delete(link)
    db.commit()
    logger.info(f"Payment link with ID {id} deleted successfully for user ID {current_user.id}")
    return {"message": "Link deleted successfully!"}


