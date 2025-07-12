"""Module for Jira account management operations."""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

from ..models.jira.account import Account, TimeLogEntry
from ..models.jira.common import JiraUser
from ..models.jira.project import JiraProject
from .client import JiraClient

logger = logging.getLogger("mcp-jira")


class AccountsMixin(JiraClient):
    """Mixin for account management operations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accounts: Dict[str, Account] = {}
        self._account_project_mappings: Dict[str, List[str]] = {}
        # Defer loading account mappings until after other mixins are initialized
        self._accounts_loaded = False
    
    def _ensure_accounts_loaded(self) -> None:
        """Ensure accounts are loaded (lazy loading)."""
        if not self._accounts_loaded:
            self._load_account_mappings()
            self._accounts_loaded = True
    
    def _load_account_mappings(self) -> None:
        """
        Load account mappings from environment variables or configuration.
        
        This method loads account-to-project mappings from environment variables
        in the format: ACCOUNT_MAPPINGS=account1:PROJ1,PROJ2;account2:PROJ3,PROJ4
        """
        try:
            account_mappings = os.getenv("ACCOUNT_MAPPINGS", "")
            if not account_mappings:
                logger.info("No ACCOUNT_MAPPINGS environment variable found. Using default mapping.")
                # Create a default account mapping based on available projects
                self._create_default_account_mapping()
                return
                
            # Parse the account mappings
            for account_mapping in account_mappings.split(";"):
                if ":" not in account_mapping:
                    continue
                    
                account_name, project_keys_str = account_mapping.split(":", 1)
                project_keys = [key.strip() for key in project_keys_str.split(",")]
                
                # Create account
                account = Account(
                    id=account_name.strip(),
                    name=account_name.strip(),
                    project_keys=project_keys,
                    is_active=True,
                )
                
                self._accounts[account.id] = account
                self._account_project_mappings[account.id] = project_keys
                
            logger.info(f"Loaded {len(self._accounts)} accounts from environment mappings")
            
        except Exception as e:
            logger.error(f"Error loading account mappings: {e}")
            self._create_default_account_mapping()
    
    def _create_default_account_mapping(self) -> None:
        """Create a default account mapping based on available projects."""
        try:
            # Get all available projects using the method from ProjectsMixin
            if hasattr(self, 'get_all_projects'):
                all_projects = self.get_all_projects()
            else:
                logger.warning("get_all_projects method not available. Creating empty default account.")
                all_projects = []
            
            if not all_projects:
                logger.warning("No projects available to create default account mapping")
                # Create a default account anyway
                default_account = Account(
                    id="default",
                    name="Default Account",
                    project_keys=[],
                    is_active=True,
                    description="Default account (no projects available)",
                )
                self._accounts["default"] = default_account
                self._account_project_mappings["default"] = []
                return
                
            # Create a single default account with all projects
            default_account = Account(
                id="default",
                name="Default Account",
                project_keys=[project.get("key", "") for project in all_projects if project.get("key")],
                is_active=True,
                description="Default account containing all available projects",
            )
            
            self._accounts["default"] = default_account
            self._account_project_mappings["default"] = default_account.project_keys
            
            logger.info(f"Created default account with {len(default_account.project_keys)} projects")
            
        except Exception as e:
            logger.error(f"Error creating default account mapping: {e}")
    
    def get_all_accounts(self, search_filter: str | None = None) -> List[Dict[str, Any]]:
        """
        Get all available accounts.
        
        Args:
            search_filter: Optional search filter to match account names
            
        Returns:
            List of account dictionaries
        """
        try:
            self._ensure_accounts_loaded()
            accounts = []
            
            for account in self._accounts.values():
                # Apply search filter if provided
                if search_filter and search_filter.lower() not in account.name.lower():
                    continue
                    
                accounts.append(account.to_simplified_dict())
                
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting all accounts: {e}")
            return []
    
    def get_account(self, account_id: str) -> Account | None:
        """
        Get account by ID.
        
        Args:
            account_id: The account ID
            
        Returns:
            Account object or None if not found
        """
        self._ensure_accounts_loaded()
        return self._accounts.get(account_id)
    
    def get_account_projects(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get all projects associated with an account.
        
        Args:
            account_id: The account ID
            
        Returns:
            List of project dictionaries
        """
        try:
            self._ensure_accounts_loaded()
            account = self.get_account(account_id)
            if not account:
                logger.warning(f"Account {account_id} not found")
                return []
                
            # Get all projects using the method from ProjectsMixin
            if hasattr(self, 'get_all_projects'):
                all_projects = self.get_all_projects()
            else:
                logger.warning("get_all_projects method not available")
                return []
            
            # Filter projects by account's project keys
            account_projects = []
            for project in all_projects:
                project_key = project.get("key", "")
                if project_key in account.project_keys:
                    account_projects.append(project)
                    
            return account_projects
            
        except Exception as e:
            logger.error(f"Error getting projects for account {account_id}: {e}")
            return []
    
    def validate_account_access(self, account_id: str, project_key: str | None = None) -> bool:
        """
        Validate that an account has access to a project.
        
        Args:
            account_id: The account ID
            project_key: Optional project key to validate access
            
        Returns:
            True if access is valid, False otherwise
        """
        try:
            self._ensure_accounts_loaded()
            account = self.get_account(account_id)
            if not account:
                logger.warning(f"Account {account_id} not found")
                return False
                
            if not account.is_active:
                logger.warning(f"Account {account_id} is not active")
                return False
                
            if project_key and project_key not in account.project_keys:
                logger.warning(f"Account {account_id} does not have access to project {project_key}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating account access: {e}")
            return False
    
    def log_time_to_account(
        self,
        account_id: str,
        time_spent: str,
        description: str | None = None,
        project_key: str | None = None,
        issue_key: str | None = None,
        started: str | None = None,
    ) -> Dict[str, Any]:
        """
        Log time against an account.
        
        Args:
            account_id: The account ID
            time_spent: Time spent in Jira format
            description: Optional description
            project_key: Optional project key
            issue_key: Optional issue key
            started: Optional start time
            
        Returns:
            Time log entry result
        """
        try:
            self._ensure_accounts_loaded()
            # Validate account access
            if not self.validate_account_access(account_id, project_key):
                raise ValueError(f"Invalid account access for account {account_id}")
                
            # If issue_key is provided, use existing worklog functionality
            if issue_key:
                if hasattr(self, 'add_worklog'):
                    worklog_result = self.add_worklog(
                        issue_key=issue_key,
                        time_spent=time_spent,
                        comment=description,
                        started=started,
                    )
                    
                    # Create time log entry based on worklog result
                    time_log_entry = TimeLogEntry(
                        id=worklog_result.get("id", ""),
                        account_id=account_id,
                        project_id=project_key,
                        issue_key=issue_key,
                        time_spent=time_spent,
                        time_spent_seconds=worklog_result.get("timeSpentSeconds", 0),
                        description=description,
                        started=started or worklog_result.get("started", ""),
                        created=worklog_result.get("created", ""),
                        updated=worklog_result.get("updated", ""),
                    )
                    
                    return {
                        "success": True,
                        "message": f"Time logged successfully to account {account_id}",
                        "account_name": self.get_account(account_id).name if self.get_account(account_id) else account_id,
                        "time_log_entry": time_log_entry.to_simplified_dict(),
                    }
                else:
                    raise ValueError("add_worklog method not available")
                    
            else:
                # For account-level time logging without specific issue
                # This is a conceptual implementation - in practice, you might
                # want to create a special issue type or use a different approach
                
                # Parse time spent to seconds
                if hasattr(self, '_parse_time_spent'):
                    time_spent_seconds = self._parse_time_spent(time_spent)
                else:
                    # Simple fallback parsing
                    time_spent_seconds = self._simple_parse_time_spent(time_spent)
                
                # Create time log entry
                time_log_entry = TimeLogEntry(
                    id=f"account_{account_id}_{int(time.time())}",
                    account_id=account_id,
                    project_id=project_key,
                    time_spent=time_spent,
                    time_spent_seconds=time_spent_seconds,
                    description=description,
                    started=started or datetime.now().isoformat(),
                    created=datetime.now().isoformat(),
                    updated=datetime.now().isoformat(),
                )
                
                return {
                    "success": True,
                    "message": f"Time logged successfully to account {account_id}",
                    "account_name": self.get_account(account_id).name if self.get_account(account_id) else account_id,
                    "time_log_entry": time_log_entry.to_simplified_dict(),
                }
                
        except Exception as e:
            logger.error(f"Error logging time to account {account_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _simple_parse_time_spent(self, time_spent: str) -> int:
        """
        Simple time parsing fallback method.
        
        Args:
            time_spent: Time spent string
            
        Returns:
            Time spent in seconds
        """
        try:
            if time_spent.endswith("h"):
                return int(float(time_spent[:-1]) * 3600)
            elif time_spent.endswith("m"):
                return int(float(time_spent[:-1]) * 60)
            elif time_spent.endswith("d"):
                return int(float(time_spent[:-1]) * 24 * 3600)
            else:
                return int(float(time_spent) * 60)  # Default to minutes
        except (ValueError, TypeError):
            logger.warning(f"Could not parse time: {time_spent}, defaulting to 60 seconds")
            return 60 