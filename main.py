from typing import List  
from fastapi import FastAPI, HTTPException  
from pydantic import BaseModel  
from sqlalchemy import create_engine, Column, String, Float  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker  
from datetime import datetime  
from contextlib import contextmanager  
from dotenv import load_dotenv
import os

load_dotenv()


  
app = FastAPI()  
  
# Database setup  
DATABASE_URL = os.getenv('url') 
engine = create_engine(DATABASE_URL)  
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  
Base = declarative_base()  
  
# Models  
class User(Base):  
    __tablename__ = "users"  
  
    user_id = Column(String, primary_key=True, index=True)  
    amount = Column(Float, nullable=False)  
  
class Transaction(Base):  
    __tablename__ = "transactions"  
  
    transaction_id = Column(String, primary_key=True, index=True)  
    user_id = Column(String, nullable=False)  
    amount = Column(Float, nullable=False)  
  
Base.metadata.create_all(bind=engine)  
  
# Pydantic schemas  
class TopupRequest(BaseModel):  
    user_id: str  
    amount: float  
  
class TransactionResponse(BaseModel):  
    status: bool  
    new_balance: float  
    transaction_id: str  
  
class UserResponse(BaseModel):  
    user_id: str  
    amount: float  
  
class TransactionResponseDetail(BaseModel):  
    transaction_id: str  
    user_id: str  
    amount: float  
  
# Context manager for database session  
@contextmanager  
def get_db_session():  
    db = SessionLocal()  
    try:  
        yield db  
    finally:  
        db.close()  
  
# Endpoints  
@app.post("/topup", response_model=TransactionResponse)  
async def topup(request: TopupRequest):  
    with get_db_session() as db:  
        # Check if the user exists  
        user = db.query(User).filter(User.user_id == request.user_id).first()  
  
        if not user:  
            # Create a new user if not found  
            user = User(user_id=request.user_id, amount=request.amount)  
            db.add(user)  
        else:  
            # Update the existing user's amount  
            user.amount += request.amount  
  
        # Generate a unique transaction ID: user_id_currenttime  
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")  
        transaction_id = f"{request.user_id}_{current_time}"  
  
        # Add the transaction to the database  
        db.add(Transaction(transaction_id=transaction_id, user_id=request.user_id, amount=request.amount))  
  
        # Commit the transaction  
        try:  
            db.commit()  
            new_balance = user.amount  # Access the amount to load it before closing the session  
        except Exception as e:  
            db.rollback()  
            raise HTTPException(status_code=500, detail="Database error")  
  
        return {"status": True, "new_balance": new_balance, "transaction_id": transaction_id}  
  
@app.post("/deduct", response_model=TransactionResponse)  
async def deduct(request: TopupRequest):  
    with get_db_session() as db:  
        # Check if the user exists  
        user = db.query(User).filter(User.user_id == request.user_id).first()  
  
        if not user:  
            raise HTTPException(status_code=404, detail="User not found")  
  
        if user.amount < request.amount:  
            raise HTTPException(status_code=400, detail="Insufficient balance")  
  
        # Deduct the amount  
        user.amount -= request.amount  
  
        # Generate a unique transaction ID: user_id_currenttime  
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")  
        transaction_id = f"{request.user_id}_{current_time}"  
  
                # Add the transaction to the database  
        db.add(Transaction(transaction_id=transaction_id, user_id=request.user_id, amount=-request.amount))  
  
        # Commit the transaction and retrieve the new balance  
        try:  
            db.commit()  
            new_balance = user.amount  # Access the amount to load it before closing the session  
        except Exception as e:  
            db.rollback()  
            raise HTTPException(status_code=500, detail="Database error")  
  
        return {"status": True, "new_balance": new_balance, "transaction_id": transaction_id}  
  
@app.get("/balance/{user_id}", response_model=UserResponse)  
async def get_balance(user_id: str):  
    with get_db_session() as db:  
        user = db.query(User).filter(User.user_id == user_id).first()  
  
        if not user:  
            raise HTTPException(status_code=404, detail="User not found")  
  
        return {"user_id": user.user_id, "amount": user.amount}  
  
@app.get("/users", response_model=List[UserResponse])  
async def get_users():  
    with get_db_session() as db:  
        users = db.query(User).all()  
        return [{"user_id": user.user_id, "amount": user.amount} for user in users]  
  
@app.get("/transactions", response_model=List[TransactionResponseDetail])  
async def get_transactions():  
    with get_db_session() as db:  
        transactions = db.query(Transaction).all()  
        return [{"transaction_id": transaction.transaction_id, "user_id": transaction.user_id, "amount": transaction.amount} for transaction in transactions]  
  
# Additional logic such as authentication, logging, etc. can be added here as needed.  
  
# Run the application  
if __name__ == "__main__":  
    import uvicorn  
    uvicorn.run(app, host="0.0.0.0", port=8000)  

