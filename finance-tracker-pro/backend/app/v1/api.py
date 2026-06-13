from fastapi import APIRouter

from app.v1.endpoints import (
    auth,
    transactions,
    categories,
    recurring_payments,
    budgets,
    goals,
    analytics,
    insights,
    dashboard,
    export
)

# Create main API router for v1
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(transactions.router)
api_router.include_router(categories.router)
api_router.include_router(recurring_payments.router)
api_router.include_router(budgets.router)
api_router.include_router(goals.router)
api_router.include_router(analytics.router)
api_router.include_router(insights.router)
api_router.include_router(dashboard.router)
api_router.include_router(export.router)
