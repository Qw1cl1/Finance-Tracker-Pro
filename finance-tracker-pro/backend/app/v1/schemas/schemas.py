from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = "folder"
    color: Optional[str] = "#6366f1"
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    children: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    date: Optional[datetime] = None
    transaction_type: TransactionType
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    comment: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None
    transaction_type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    comment: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    is_recurring: bool = False
    recurring_payment_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True


# Recurring Payment Schemas
class RecurringPaymentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    frequency: Frequency
    next_payment_date: datetime
    category_id: Optional[int] = None


class RecurringPaymentCreate(RecurringPaymentBase):
    pass


class RecurringPaymentUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[Frequency] = None
    next_payment_date: Optional[datetime] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class RecurringPaymentResponse(RecurringPaymentBase):
    id: int
    user_id: int
    is_active: bool = True
    last_payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Budget Schemas
class BudgetBase(BaseModel):
    category_id: int
    limit_amount: float = Field(..., gt=0)
    period: Optional[str] = "monthly"


class BudgetCreate(BudgetBase):
    start_date: datetime


class BudgetUpdate(BaseModel):
    limit_amount: Optional[float] = None
    period: Optional[str] = None
    end_date: Optional[datetime] = None


class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    spent_amount: Optional[float] = None
    is_exceeded: Optional[bool] = None
    
    class Config:
        from_attributes = True


# Goal Schemas
class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_amount: float = Field(..., gt=0)
    current_amount: Optional[float] = 0
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    icon: Optional[str] = "target"
    color: Optional[str] = "#10b981"


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_completed: Optional[bool] = None


class GoalResponse(GoalBase):
    id: int
    user_id: int
    is_completed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True


# Dashboard Schema
class DashboardSummary(BaseModel):
    total_balance: float = 0
    monthly_income: float = 0
    monthly_expense: float = 0
    savings: float = 0
    recent_transactions: List[TransactionResponse] = []


# Analytics Schema
class CategoryAnalytics(BaseModel):
    category_id: int
    category_name: str
    total_amount: float
    transaction_count: int
    percentage: float
    color: Optional[str] = None


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float
    net: float


class AnalyticsResponse(BaseModel):
    categories: List[CategoryAnalytics] = []
    monthly_trends: List[MonthlyTrend] = []
    top_categories: List[CategoryAnalytics] = []
    average_daily_expense: float = 0
    comparison: Optional[dict] = None


# Insight Schema
class Insight(BaseModel):
    message: str
    type: str  # warning, info, success
    category: Optional[str] = None
