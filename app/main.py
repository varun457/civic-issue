from fastapi import FastAPI
from .routes import storage_test, test_db   # import both routers

# Create the FastAPI application
app = FastAPI()

# Root endpoint – quick health-check
@app.get("/")
def root():
    return {"message": "Supabase Civic Backend up"}

# Register routers
app.include_router(storage_test.router)  # for file uploads
app.include_router(test_db.router)       # for database test
