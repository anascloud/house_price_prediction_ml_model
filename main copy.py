from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Home page"}

@app.get("/about")
async def about():
    return {"project": "About page"}@app.get("/about")

@app.get("/customer")
def get_customer(customer_id: int):
    return {
        "customer_id": customer_id,
        "customer_name": "John Smith",
        "status": "active"
    }