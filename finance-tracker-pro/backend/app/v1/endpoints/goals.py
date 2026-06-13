from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.v1.models.models import Goal
from app.v1.schemas.schemas import (
    GoalCreate,
    GoalUpdate,
    GoalResponse
)
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/", response_model=List[GoalResponse])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all financial goals for the current user."""
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    
    # Calculate progress percentage for each goal
    goal_responses = []
    for goal in goals:
        goal_dict = {
            "id": goal.id,
            "name": goal.name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "deadline": goal.deadline,
            "description": goal.description,
            "icon": goal.icon,
            "color": goal.color,
            "user_id": goal.user_id,
            "is_completed": goal.is_completed,
            "created_at": goal.created_at,
            "updated_at": goal.updated_at,
            "progress_percentage": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        }
        goal_responses.append(GoalResponse(**goal_dict))
    
    return goal_responses


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific financial goal by ID."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    progress_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    
    goal_dict = {
        "id": goal.id,
        "name": goal.name,
        "target_amount": float(goal.target_amount),
        "current_amount": float(goal.current_amount),
        "deadline": goal.deadline,
        "description": goal.description,
        "icon": goal.icon,
        "color": goal.color,
        "user_id": goal.user_id,
        "is_completed": goal.is_completed,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress_percentage": progress_percentage
    }
    
    return GoalResponse(**goal_dict)


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new financial goal."""
    new_goal = Goal(
        **goal_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    
    return new_goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing financial goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)
    
    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True
    
    db.commit()
    db.refresh(goal)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a financial goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()
    
    return None
