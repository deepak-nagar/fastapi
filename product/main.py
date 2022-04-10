from pkg_resources import yield_lines
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from .import schemas
from .import models
from .database import engine, SessionLocal
from fastapi.params import Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi import status
app = FastAPI()


models.Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close


@app.put('/product/{id}')
def update(id, request: schemas.Product, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id)
    if not product.first():
        pass
    product.update(request.dict())
    db.commit()
    return {"updated"}


@app.delete('/product/{id}')
def delete(id, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == id).delete(synchronize_session=False)

    db.commit()
    return {'Entry deleted'}


@app.get('/products', response_model=List[schemas.DisplayProduct])
def products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products


@app.get('/product/{id}', response_model=schemas.DisplayProduct)
def product(id, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="product not found")
    return product


@app.post('/product', status_code=status.HTTP_201_CREATED)
def add(request: schemas.Product, db: Session = Depends(get_db)):
    new_product = models.Product(
        name=request.name, desc=request.desc, price=request.price)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return request


@app.post('/seller')
def create_seller(request: schemas.Seller, db: Session = Depends(get_db)):
    new_seller = models.Seller(username=request.username)
    return request


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client driver says #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
