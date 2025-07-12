"""
Jira account models for account-based time logging and project management.

This module provides Pydantic models for managing accounts and time log entries
at the account level, providing a business-level abstraction over Jira projects.
"""

import logging
from typing import Any

from pydantic import Field

from ..base import ApiModel, TimestampMixin
from ..constants import EMPTY_STRING, JIRA_DEFAULT_ID
from .common import JiraUser

logger = logging.getLogger(__name__)


class Account(ApiModel):
    """
    Model representing an account that groups projects.
    
    This model provides a business-level abstraction for organizing
    Jira projects under accounts for time logging and project management.
    """
    
    id: str = JIRA_DEFAULT_ID
    name: str = EMPTY_STRING
    description: str | None = None
    project_keys: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_by: JiraUser | None = None
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any], **kwargs: Any) -> "Account":
        """
        Create an Account from API response data.
        
        Args:
            data: The account data from the API
            
        Returns:
            An Account instance
        """
        if not data:
            return cls()
            
        # Handle non-dictionary data by returning a default instance
        if not isinstance(data, dict):
            logger.debug("Received non-dictionary data, returning default instance")
            return cls()
            
        # Extract created_by data if available
        created_by = None
        created_by_data = data.get("created_by")
        if created_by_data:
            created_by = JiraUser.from_api_response(created_by_data)
            
        return cls(
            id=str(data.get("id", JIRA_DEFAULT_ID)),
            name=str(data.get("name", EMPTY_STRING)),
            description=data.get("description"),
            project_keys=data.get("project_keys", []),
            is_active=bool(data.get("is_active", True)),
            created_by=created_by,
        )
    
    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result = {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "project_count": len(self.project_keys),
        }
        
        if self.description:
            result["description"] = self.description
            
        if self.project_keys:
            result["project_keys"] = self.project_keys
            
        if self.created_by:
            result["created_by"] = self.created_by.to_simplified_dict()
            
        return result


class TimeLogEntry(ApiModel, TimestampMixin):
    """
    Model representing a time log entry at the account level.
    
    This model extends the concept of worklog entries to support
    account-based time logging with optional project association.
    """
    
    id: str = JIRA_DEFAULT_ID
    account_id: str = JIRA_DEFAULT_ID
    project_id: str | None = None
    issue_key: str | None = None
    user: JiraUser | None = None
    time_spent: str = EMPTY_STRING
    time_spent_seconds: int = 0
    description: str | None = None
    started: str = EMPTY_STRING
    created: str = EMPTY_STRING
    updated: str = EMPTY_STRING
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any], **kwargs: Any) -> "TimeLogEntry":
        """
        Create a TimeLogEntry from API response data.
        
        Args:
            data: The time log entry data from the API
            
        Returns:
            A TimeLogEntry instance
        """
        if not data:
            return cls()
            
        # Handle non-dictionary data by returning a default instance
        if not isinstance(data, dict):
            logger.debug("Received non-dictionary data, returning default instance")
            return cls()
            
        # Extract user data if available
        user = None
        user_data = data.get("user")
        if user_data:
            user = JiraUser.from_api_response(user_data)
            
        # Parse time spent seconds with type safety
        time_spent_seconds = data.get("time_spent_seconds", 0)
        try:
            time_spent_seconds = (
                int(time_spent_seconds) if time_spent_seconds is not None else 0
            )
        except (ValueError, TypeError):
            time_spent_seconds = 0
            
        return cls(
            id=str(data.get("id", JIRA_DEFAULT_ID)),
            account_id=str(data.get("account_id", JIRA_DEFAULT_ID)),
            project_id=data.get("project_id"),
            issue_key=data.get("issue_key"),
            user=user,
            time_spent=str(data.get("time_spent", EMPTY_STRING)),
            time_spent_seconds=time_spent_seconds,
            description=data.get("description"),
            started=str(data.get("started", EMPTY_STRING)),
            created=str(data.get("created", EMPTY_STRING)),
            updated=str(data.get("updated", EMPTY_STRING)),
        )
    
    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result = {
            "id": self.id,
            "account_id": self.account_id,
            "time_spent": self.time_spent,
            "time_spent_seconds": self.time_spent_seconds,
        }
        
        if self.project_id:
            result["project_id"] = self.project_id
            
        if self.issue_key:
            result["issue_key"] = self.issue_key
            
        if self.user:
            result["user"] = self.user.to_simplified_dict()
            
        if self.description:
            result["description"] = self.description
            
        if self.started:
            result["started"] = self.started
            
        if self.created:
            result["created"] = self.created
            
        if self.updated:
            result["updated"] = self.updated
            
        return result 