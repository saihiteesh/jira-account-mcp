"""
Test suite for Jira account-based time logging and project management features.

This module tests the AccountsMixin functionality including account management,
project mapping, and time logging operations.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from mcp_atlassian.jira.accounts import AccountsMixin
from mcp_atlassian.models.jira.account import Account, TimeLogEntry
from mcp_atlassian.models.jira.project import JiraProject
from mcp_atlassian.models.jira.worklog import JiraWorklog


class TestAccountsMixin:
    """Test suite for AccountsMixin functionality."""
    
    @pytest.fixture
    def accounts_mixin(self):
        """Create a mock AccountsMixin instance for testing."""
        with patch.dict(os.environ, {
            'ACCOUNT_MAPPINGS': 'team-alpha:PROJ,DEV;team-beta:SUPPORT,DOCS;client-work:CLIENT1,CLIENT2'
        }):
            mixin = AccountsMixin()
            mixin._atlassian_client = Mock()
            mixin._config = Mock()
            mixin._config.user_agent = "TestAgent"
            return mixin

    def test_load_account_mappings(self, accounts_mixin):
        """Test loading account mappings from environment variables."""
        accounts_mixin._load_account_mappings()
        
        assert len(accounts_mixin._accounts) == 3
        assert 'team-alpha' in accounts_mixin._accounts
        assert 'team-beta' in accounts_mixin._accounts
        assert 'client-work' in accounts_mixin._accounts
        
        # Check account details
        team_alpha = accounts_mixin._accounts['team-alpha']
        assert team_alpha.id == 'team-alpha'
        assert team_alpha.name == 'Team Alpha'
        
        # Check project mappings
        assert accounts_mixin._account_project_mappings['team-alpha'] == ['PROJ', 'DEV']
        assert accounts_mixin._account_project_mappings['team-beta'] == ['SUPPORT', 'DOCS']
        assert accounts_mixin._account_project_mappings['client-work'] == ['CLIENT1', 'CLIENT2']

    def test_load_account_mappings_no_env_var(self):
        """Test loading account mappings when no environment variable is set."""
        with patch.dict(os.environ, {}, clear=True):
            mixin = AccountsMixin()
            mixin._load_account_mappings()
            
            assert len(mixin._accounts) == 0
            assert len(mixin._account_project_mappings) == 0

    def test_load_account_mappings_invalid_format(self):
        """Test loading account mappings with invalid format."""
        with patch.dict(os.environ, {'ACCOUNT_MAPPINGS': 'invalid-format'}):
            mixin = AccountsMixin()
            mixin._load_account_mappings()
            
            # Should handle invalid format gracefully
            assert len(mixin._accounts) == 0

    def test_format_account_name(self, accounts_mixin):
        """Test account name formatting."""
        assert accounts_mixin._format_account_name('team-alpha') == 'Team Alpha'
        assert accounts_mixin._format_account_name('client-work') == 'Client Work'
        assert accounts_mixin._format_account_name('simple') == 'Simple'
        assert accounts_mixin._format_account_name('multi-word-name') == 'Multi Word Name'

    def test_get_accounts_all(self, accounts_mixin):
        """Test getting all accounts."""
        accounts_mixin._load_account_mappings()
        accounts = accounts_mixin.get_accounts()
        
        assert len(accounts) == 3
        account_ids = [acc.id for acc in accounts]
        assert 'team-alpha' in account_ids
        assert 'team-beta' in account_ids
        assert 'client-work' in account_ids

    def test_get_accounts_with_filter(self, accounts_mixin):
        """Test getting accounts with search filter."""
        accounts_mixin._load_account_mappings()
        
        # Test case-insensitive search
        accounts = accounts_mixin.get_accounts(search_filter='team')
        assert len(accounts) == 2
        account_ids = [acc.id for acc in accounts]
        assert 'team-alpha' in account_ids
        assert 'team-beta' in account_ids

        # Test partial match
        accounts = accounts_mixin.get_accounts(search_filter='alpha')
        assert len(accounts) == 1
        assert accounts[0].id == 'team-alpha'

        # Test no match
        accounts = accounts_mixin.get_accounts(search_filter='nonexistent')
        assert len(accounts) == 0

    def test_get_account_projects(self, accounts_mixin):
        """Test getting projects for a specific account."""
        accounts_mixin._load_account_mappings()
        
        # Mock the get_projects method
        mock_projects = [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]
        accounts_mixin.get_projects = Mock(return_value=mock_projects)
        
        projects = accounts_mixin.get_account_projects('team-alpha')
        
        assert len(projects) == 2
        assert projects[0].key == 'PROJ'
        assert projects[1].key == 'DEV'

    def test_get_account_projects_invalid_account(self, accounts_mixin):
        """Test getting projects for an invalid account."""
        accounts_mixin._load_account_mappings()
        
        with pytest.raises(ValueError, match="Account 'invalid-account' not found"):
            accounts_mixin.get_account_projects('invalid-account')

    def test_get_account_projects_no_projects(self, accounts_mixin):
        """Test getting projects when account has no projects."""
        accounts_mixin._load_account_mappings()
        accounts_mixin.get_projects = Mock(return_value=[])
        
        projects = accounts_mixin.get_account_projects('team-alpha')
        assert len(projects) == 0

    def test_log_time_to_account(self, accounts_mixin):
        """Test logging time to an account."""
        accounts_mixin._load_account_mappings()
        
        # Mock the get_projects method to return projects for the account
        mock_projects = [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]
        accounts_mixin.get_projects = Mock(return_value=mock_projects)
        
        # Mock the add_worklog method
        mock_worklog = JiraWorklog(
            id="12345",
            author_account_id="user123",
            author_display_name="Test User",
            created="2024-01-01T10:00:00.000Z",
            updated="2024-01-01T10:00:00.000Z",
            started="2024-01-01T09:00:00.000Z",
            time_spent="2h",
            time_spent_seconds=7200,
            comment="Test work"
        )
        accounts_mixin.add_worklog = Mock(return_value=mock_worklog)
        
        # Test logging time to account
        result = accounts_mixin.log_time_to_account(
            account_id="team-alpha",
            project_key="PROJ",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Test work"
        )
        
        assert result is not None
        assert result.time_spent == "2h"
        assert result.comment == "Test work"
        
        # Verify that add_worklog was called with correct parameters
        accounts_mixin.add_worklog.assert_called_once_with(
            issue_key="PROJ-123",
            time_spent="2h",
            comment="Test work",
            started=None
        )

    def test_log_time_to_account_invalid_account(self, accounts_mixin):
        """Test logging time to an invalid account."""
        accounts_mixin._load_account_mappings()
        
        with pytest.raises(ValueError, match="Account 'invalid-account' not found"):
            accounts_mixin.log_time_to_account(
                account_id="invalid-account",
                project_key="PROJ",
                issue_key="PROJ-123",
                time_spent="2h"
            )

    def test_log_time_to_account_invalid_project(self, accounts_mixin):
        """Test logging time to a project not in the account."""
        accounts_mixin._load_account_mappings()
        
        # Mock the get_projects method to return projects for the account
        mock_projects = [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]
        accounts_mixin.get_projects = Mock(return_value=mock_projects)
        
        with pytest.raises(ValueError, match="Project 'INVALID' is not associated with account 'team-alpha'"):
            accounts_mixin.log_time_to_account(
                account_id="team-alpha",
                project_key="INVALID",
                issue_key="INVALID-123",
                time_spent="2h"
            )

    def test_log_time_to_account_without_project(self, accounts_mixin):
        """Test logging time to account without specifying project."""
        accounts_mixin._load_account_mappings()
        
        # Mock the get_projects method to return projects for the account
        mock_projects = [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]
        accounts_mixin.get_projects = Mock(return_value=mock_projects)
        
        # Mock the add_worklog method
        mock_worklog = JiraWorklog(
            id="12345",
            author_account_id="user123",
            author_display_name="Test User",
            created="2024-01-01T10:00:00.000Z",
            updated="2024-01-01T10:00:00.000Z",
            started="2024-01-01T09:00:00.000Z",
            time_spent="2h",
            time_spent_seconds=7200,
            comment="General work for Team Alpha"
        )
        accounts_mixin.add_worklog = Mock(return_value=mock_worklog)
        
        # Test logging time to account (should use first project)
        result = accounts_mixin.log_time_to_account(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="General work"
        )
        
        assert result is not None
        assert result.time_spent == "2h"

    def test_validate_account_access(self, accounts_mixin):
        """Test account access validation."""
        accounts_mixin._load_account_mappings()
        
        # Valid account should pass
        assert accounts_mixin.validate_account_access('team-alpha') is True
        
        # Invalid account should fail
        assert accounts_mixin.validate_account_access('invalid-account') is False

    def test_get_account_summary(self, accounts_mixin):
        """Test getting account summary information."""
        accounts_mixin._load_account_mappings()
        
        # Mock the get_projects method
        mock_projects = [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]
        accounts_mixin.get_projects = Mock(return_value=mock_projects)
        
        summary = accounts_mixin.get_account_summary('team-alpha')
        
        assert summary['account_id'] == 'team-alpha'
        assert summary['account_name'] == 'Team Alpha'
        assert summary['project_count'] == 2
        assert len(summary['projects']) == 2
        assert summary['projects'][0]['key'] == 'PROJ'
        assert summary['projects'][1]['key'] == 'DEV'

    def test_get_account_summary_invalid_account(self, accounts_mixin):
        """Test getting summary for invalid account."""
        accounts_mixin._load_account_mappings()
        
        with pytest.raises(ValueError, match="Account 'invalid-account' not found"):
            accounts_mixin.get_account_summary('invalid-account')


class TestAccountModels:
    """Test suite for Account and TimeLogEntry models."""
    
    def test_account_model_creation(self):
        """Test creating an Account model."""
        account = Account(
            id="team-alpha",
            name="Team Alpha",
            description="Alpha team projects",
            is_active=True
        )
        
        assert account.id == "team-alpha"
        assert account.name == "Team Alpha"
        assert account.description == "Alpha team projects"
        assert account.is_active is True

    def test_account_model_defaults(self):
        """Test Account model with default values."""
        account = Account()
        
        assert account.id == ""
        assert account.name == ""
        assert account.description == ""
        assert account.is_active is True

    def test_time_log_entry_model_creation(self):
        """Test creating a TimeLogEntry model."""
        entry = TimeLogEntry(
            id="log-123",
            account_id="team-alpha",
            project_key="PROJ",
            issue_key="PROJ-123",
            time_spent="2h",
            time_spent_seconds=7200,
            description="Development work",
            started="2024-01-01T09:00:00.000Z",
            author_account_id="user123",
            author_display_name="Test User"
        )
        
        assert entry.id == "log-123"
        assert entry.account_id == "team-alpha"
        assert entry.project_key == "PROJ"
        assert entry.issue_key == "PROJ-123"
        assert entry.time_spent == "2h"
        assert entry.time_spent_seconds == 7200
        assert entry.description == "Development work"
        assert entry.started == "2024-01-01T09:00:00.000Z"
        assert entry.author_account_id == "user123"
        assert entry.author_display_name == "Test User"

    def test_time_log_entry_model_defaults(self):
        """Test TimeLogEntry model with default values."""
        entry = TimeLogEntry(account_id="team-alpha")
        
        assert entry.id == ""
        assert entry.account_id == "team-alpha"
        assert entry.project_key == ""
        assert entry.issue_key == ""
        assert entry.time_spent == ""
        assert entry.time_spent_seconds == 0
        assert entry.description == ""
        assert entry.started == ""
        assert entry.author_account_id == ""
        assert entry.author_display_name == ""

    def test_account_model_validation(self):
        """Test Account model validation."""
        # Test required fields
        account = Account(id="test-account", name="Test Account")
        assert account.id == "test-account"
        assert account.name == "Test Account"
        
        # Test that model accepts extra fields gracefully
        account_dict = {
            "id": "test-account",
            "name": "Test Account",
            "extra_field": "extra_value"
        }
        account = Account(**account_dict)
        assert account.id == "test-account"
        assert account.name == "Test Account"

    def test_time_log_entry_model_validation(self):
        """Test TimeLogEntry model validation."""
        # Test required account_id
        entry = TimeLogEntry(account_id="team-alpha")
        assert entry.account_id == "team-alpha"
        
        # Test time validation
        entry = TimeLogEntry(
            account_id="team-alpha",
            time_spent="2h",
            time_spent_seconds=7200
        )
        assert entry.time_spent == "2h"
        assert entry.time_spent_seconds == 7200 