from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, business, transactions, analytics  # Updated this line

# Create the app FIRST
app = FastAPI(
    title="Revenue Agent API",
    description="Proco Revenue Diagnostics Agent - Backend API",
    version="0.1.0"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://procoagent.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers AFTER app is created
app.include_router(auth.router)
app.include_router(business.router)
app.include_router(transactions.router)  # Added
app.include_router(analytics.router)     # Added


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "Revenue Agent API", "docs": "/docs"}
