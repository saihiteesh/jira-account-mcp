"""
Integration tests for account-based MCP tools.

This module tests the MCP tools for account-based time logging and project management
including list_accounts, get_account_projects, and log_time_with_account.
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock

from mcp_atlassian.servers.context import Context
from mcp_atlassian.servers.jira import list_accounts, get_account_projects, log_time_with_account
from mcp_atlassian.models.jira.account import Account
from mcp_atlassian.models.jira.project import JiraProject
from mcp_atlassian.models.jira.worklog import JiraWorklog


class TestAccountMCPTools:
    """Test suite for account-based MCP tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        ctx = Mock(spec=Context)
        ctx.dependencies = Mock()
        ctx.dependencies.jira = Mock()
        ctx.dependencies.jira.get_accounts = Mock()
        ctx.dependencies.jira.get_account_projects = Mock()
        ctx.dependencies.jira.log_time_to_account = Mock()
        ctx.dependencies.jira.validate_account_access = Mock()
        return ctx

    @pytest.fixture
    def sample_accounts(self):
        """Sample accounts for testing."""
        return [
            Account(id="team-alpha", name="Team Alpha", description="Alpha team projects"),
            Account(id="team-beta", name="Team Beta", description="Beta team projects"),
            Account(id="client-work", name="Client Work", description="Client project work")
        ]

    @pytest.fixture
    def sample_projects(self):
        """Sample projects for testing."""
        return [
            JiraProject(id="10001", key="PROJ", name="Project 1"),
            JiraProject(id="10002", key="DEV", name="Development Project")
        ]

    @pytest.fixture
    def sample_worklog(self):
        """Sample worklog for testing."""
        return JiraWorklog(
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

    @pytest.mark.asyncio
    async def test_list_accounts_all(self, mock_context, sample_accounts):
        """Test listing all accounts."""
        mock_context.dependencies.jira.get_accounts.return_value = sample_accounts
        
        result = await list_accounts(mock_context)
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert len(data["accounts"]) == 3
        assert data["accounts"][0]["id"] == "team-alpha"
        assert data["accounts"][0]["name"] == "Team Alpha"
        assert data["accounts"][1]["id"] == "team-beta"
        assert data["accounts"][2]["id"] == "client-work"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.get_accounts.assert_called_once_with(search_filter=None)

    @pytest.mark.asyncio
    async def test_list_accounts_with_filter(self, mock_context, sample_accounts):
        """Test listing accounts with search filter."""
        # Filter to only team accounts
        filtered_accounts = [acc for acc in sample_accounts if "team" in acc.id]
        mock_context.dependencies.jira.get_accounts.return_value = filtered_accounts
        
        result = await list_accounts(mock_context, search_filter="team")
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert len(data["accounts"]) == 2
        assert data["accounts"][0]["id"] == "team-alpha"
        assert data["accounts"][1]["id"] == "team-beta"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.get_accounts.assert_called_once_with(search_filter="team")

    @pytest.mark.asyncio
    async def test_list_accounts_empty_result(self, mock_context):
        """Test listing accounts with no results."""
        mock_context.dependencies.jira.get_accounts.return_value = []
        
        result = await list_accounts(mock_context)
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert len(data["accounts"]) == 0
        assert data["message"] == "No accounts found"

    @pytest.mark.asyncio
    async def test_list_accounts_error(self, mock_context):
        """Test listing accounts with error."""
        mock_context.dependencies.jira.get_accounts.side_effect = Exception("API Error")
        
        result = await list_accounts(mock_context)
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "API Error" in data["error"]

    @pytest.mark.asyncio
    async def test_get_account_projects_success(self, mock_context, sample_projects):
        """Test getting projects for an account."""
        mock_context.dependencies.jira.get_account_projects.return_value = sample_projects
        
        result = await get_account_projects(mock_context, account_id="team-alpha")
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["account_id"] == "team-alpha"
        assert len(data["projects"]) == 2
        assert data["projects"][0]["key"] == "PROJ"
        assert data["projects"][0]["name"] == "Project 1"
        assert data["projects"][1]["key"] == "DEV"
        assert data["projects"][1]["name"] == "Development Project"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.get_account_projects.assert_called_once_with("team-alpha")

    @pytest.mark.asyncio
    async def test_get_account_projects_empty_result(self, mock_context):
        """Test getting projects for an account with no projects."""
        mock_context.dependencies.jira.get_account_projects.return_value = []
        
        result = await get_account_projects(mock_context, account_id="team-alpha")
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["account_id"] == "team-alpha"
        assert len(data["projects"]) == 0
        assert data["message"] == "No projects found for account 'team-alpha'"

    @pytest.mark.asyncio
    async def test_get_account_projects_invalid_account(self, mock_context):
        """Test getting projects for an invalid account."""
        mock_context.dependencies.jira.get_account_projects.side_effect = ValueError("Account 'invalid-account' not found")
        
        result = await get_account_projects(mock_context, account_id="invalid-account")
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Account 'invalid-account' not found" in data["error"]

    @pytest.mark.asyncio
    async def test_get_account_projects_error(self, mock_context):
        """Test getting projects with API error."""
        mock_context.dependencies.jira.get_account_projects.side_effect = Exception("API Error")
        
        result = await get_account_projects(mock_context, account_id="team-alpha")
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "API Error" in data["error"]

    @pytest.mark.asyncio
    async def test_log_time_with_account_success(self, mock_context, sample_worklog):
        """Test logging time with account ID."""
        mock_context.dependencies.jira.log_time_to_account.return_value = sample_worklog
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["account_id"] == "team-alpha"
        assert data["issue_key"] == "PROJ-123"
        assert data["time_spent"] == "2h"
        assert data["time_spent_seconds"] == 7200
        assert data["description"] == "Development work"
        assert data["worklog_id"] == "12345"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.log_time_to_account.assert_called_once_with(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work",
            project_key=None,
            started=None
        )

    @pytest.mark.asyncio
    async def test_log_time_with_account_and_project(self, mock_context, sample_worklog):
        """Test logging time with account ID and project key."""
        mock_context.dependencies.jira.log_time_to_account.return_value = sample_worklog
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work",
            project_key="PROJ"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["account_id"] == "team-alpha"
        assert data["project_key"] == "PROJ"
        assert data["issue_key"] == "PROJ-123"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.log_time_to_account.assert_called_once_with(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work",
            project_key="PROJ",
            started=None
        )

    @pytest.mark.asyncio
    async def test_log_time_with_account_with_started_time(self, mock_context, sample_worklog):
        """Test logging time with account ID and started time."""
        mock_context.dependencies.jira.log_time_to_account.return_value = sample_worklog
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work",
            started="2024-01-01T09:00:00.000Z"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["started"] == "2024-01-01T09:00:00.000Z"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.log_time_to_account.assert_called_once_with(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work",
            project_key=None,
            started="2024-01-01T09:00:00.000Z"
        )

    @pytest.mark.asyncio
    async def test_log_time_with_account_invalid_account(self, mock_context):
        """Test logging time with invalid account ID."""
        mock_context.dependencies.jira.log_time_to_account.side_effect = ValueError("Account 'invalid-account' not found")
        
        result = await log_time_with_account(
            mock_context,
            account_id="invalid-account",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Account 'invalid-account' not found" in data["error"]

    @pytest.mark.asyncio
    async def test_log_time_with_account_invalid_project(self, mock_context):
        """Test logging time with invalid project key."""
        mock_context.dependencies.jira.log_time_to_account.side_effect = ValueError("Project 'INVALID' is not associated with account 'team-alpha'")
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="INVALID-123",
            time_spent="2h",
            description="Development work",
            project_key="INVALID"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Project 'INVALID' is not associated with account 'team-alpha'" in data["error"]

    @pytest.mark.asyncio
    async def test_log_time_with_account_api_error(self, mock_context):
        """Test logging time with API error."""
        mock_context.dependencies.jira.log_time_to_account.side_effect = Exception("API Error")
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="Development work"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is False
        assert "API Error" in data["error"]

    @pytest.mark.asyncio
    async def test_log_time_with_account_minimal_params(self, mock_context, sample_worklog):
        """Test logging time with minimal required parameters."""
        mock_context.dependencies.jira.log_time_to_account.return_value = sample_worklog
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h"
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["account_id"] == "team-alpha"
        assert data["issue_key"] == "PROJ-123"
        assert data["time_spent"] == "2h"
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.log_time_to_account.assert_called_once_with(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description="",
            project_key=None,
            started=None
        )

    @pytest.mark.asyncio
    async def test_log_time_with_account_unicode_description(self, mock_context, sample_worklog):
        """Test logging time with unicode characters in description."""
        mock_context.dependencies.jira.log_time_to_account.return_value = sample_worklog
        
        unicode_description = "Development work with émojis 🚀 and special chars: áéíóú"
        
        result = await log_time_with_account(
            mock_context,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description=unicode_description
        )
        
        # Parse the JSON result
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["description"] == unicode_description
        
        # Verify the method was called correctly
        mock_context.dependencies.jira.log_time_to_account.assert_called_once_with(
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h",
            description=unicode_description,
            project_key=None,
            started=None
        )


class TestAccountMCPToolsEnvironment:
    """Test suite for account MCP tools with environment configurations."""
    
    @pytest.mark.asyncio
    async def test_list_accounts_with_env_config(self):
        """Test listing accounts with environment configuration."""
        with patch.dict(os.environ, {
            'ACCOUNT_MAPPINGS': 'team-alpha:PROJ,DEV;team-beta:SUPPORT,DOCS'
        }):
            # Mock context
            ctx = Mock(spec=Context)
            ctx.dependencies = Mock()
            ctx.dependencies.jira = Mock()
            
            # Mock accounts based on environment
            accounts = [
                Account(id="team-alpha", name="Team Alpha"),
                Account(id="team-beta", name="Team Beta")
            ]
            ctx.dependencies.jira.get_accounts.return_value = accounts
            
            result = await list_accounts(ctx)
            
            # Parse the JSON result
            data = json.loads(result)
            
            assert data["success"] is True
            assert len(data["accounts"]) == 2
            assert data["accounts"][0]["id"] == "team-alpha"
            assert data["accounts"][1]["id"] == "team-beta"

    @pytest.mark.asyncio
    async def test_get_account_projects_with_env_config(self):
        """Test getting account projects with environment configuration."""
        with patch.dict(os.environ, {
            'ACCOUNT_MAPPINGS': 'team-alpha:PROJ,DEV;team-beta:SUPPORT,DOCS'
        }):
            # Mock context
            ctx = Mock(spec=Context)
            ctx.dependencies = Mock()
            ctx.dependencies.jira = Mock()
            
            # Mock projects based on environment
            projects = [
                JiraProject(id="10001", key="PROJ", name="Project 1"),
                JiraProject(id="10002", key="DEV", name="Development Project")
            ]
            ctx.dependencies.jira.get_account_projects.return_value = projects
            
            result = await get_account_projects(ctx, account_id="team-alpha")
            
            # Parse the JSON result
            data = json.loads(result)
            
            assert data["success"] is True
            assert data["account_id"] == "team-alpha"
            assert len(data["projects"]) == 2
            assert data["projects"][0]["key"] == "PROJ"
            assert data["projects"][1]["key"] == "DEV"

    @pytest.mark.asyncio
    async def test_account_tools_error_handling(self):
        """Test error handling in account tools."""
        # Mock context with no jira dependency
        ctx = Mock(spec=Context)
        ctx.dependencies = Mock()
        ctx.dependencies.jira = None
        
        # Test list_accounts with missing dependency
        result = await list_accounts(ctx)
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data
        
        # Test get_account_projects with missing dependency
        result = await get_account_projects(ctx, account_id="team-alpha")
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data
        
        # Test log_time_with_account with missing dependency
        result = await log_time_with_account(
            ctx,
            account_id="team-alpha",
            issue_key="PROJ-123",
            time_spent="2h"
        )
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data 