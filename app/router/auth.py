from fastapi import Body, Depends, FastAPI, Response, status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import schemas, utils, models
from ..database import get_db
from . import oauth2

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post('/login')
def login(user_card: OAuth2PasswordRequestForm = Depends(), user_data: schemas.UserLogin = Body(None), db: Session = Depends(get_db)):
    email = user_card.username if user_card else user_data.email
    password = user_card.password if user_card else user_data.password

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    if not utils.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    access_token = oauth2.create_access_token(data={'user_id': user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post('/login-json')
def login_json(
    user_data: schemas.UserLogin = Body(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()

    if not user or not utils.verify(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    access_token = oauth2.create_access_token(data={'user_id': user.id})
    return {"access_token": access_token, "token_type": "bearer"}
    