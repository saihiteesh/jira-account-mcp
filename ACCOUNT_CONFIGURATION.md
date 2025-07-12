# Account-Based Time Logging Configuration

This document provides comprehensive guidance on configuring and using the account-based time logging and project management features in MCP Atlassian.

## Overview

The account-based time logging feature provides a business-level abstraction over Jira projects, allowing you to:

- Group related projects under accounts
- Log time at the account level
- Manage projects by account
- Track time across multiple projects within an account

## Configuration

### Environment Variable Setup

Add the following environment variable to your `.env` file:

```bash
# Account mappings for time logging and project management
# Format: account_id:project_key1,project_key2;account_id2:project_key3
ACCOUNT_MAPPINGS=team-alpha:PROJ,DEV;team-beta:SUPPORT,DOCS;client-work:CLIENT1,CLIENT2
```

### Configuration Format

The `ACCOUNT_MAPPINGS` environment variable uses the following format:

```
account_id:project_key1,project_key2;account_id2:project_key3,project_key4
```

Where:
- `account_id`: A unique identifier for the account
- `project_key1,project_key2`: Comma-separated list of Jira project keys
- `;`: Semicolon separates different accounts

### Configuration Examples

#### 1. Team-Based Accounts
```bash
ACCOUNT_MAPPINGS=frontend:WEB,MOBILE;backend:API,DB;devops:INFRA,DEPLOY
```

#### 2. Client-Based Accounts
```bash
ACCOUNT_MAPPINGS=client-acme:ACME1,ACME2;client-beta:BETA1,BETA2;internal:INTERNAL,TOOLS
```

#### 3. Department-Based Accounts
```bash
ACCOUNT_MAPPINGS=engineering:PROJ,DEV,TEST;marketing:MARK,CAMP;sales:SALES,CRM
```

#### 4. Project-Type Based Accounts
```bash
ACCOUNT_MAPPINGS=product-development:PROD,FEAT;maintenance:MAINT,BUGS;research:RND,POC
```

### Default Behavior

If no `ACCOUNT_MAPPINGS` is provided, the system will create a default account:
- **Account ID**: `default`
- **Account Name**: `Default Account`
- **Projects**: All available projects in your Jira instance

## Available Tools

### 1. `list_accounts`

Retrieves all available accounts for time logging and project management.

**Usage:**
```javascript
// List all accounts
list_accounts()

// Search for specific accounts
list_accounts({ search_filter: "team" })
```

**Response:**
```json
{
  "success": true,
  "accounts": [
    {
      "id": "team-alpha",
      "name": "team-alpha",
      "is_active": true,
      "project_count": 2,
      "project_keys": ["PROJ", "DEV"]
    }
  ],
  "total": 1
}
```

### 2. `get_account_projects`

Fetches all projects associated with a given account.

**Usage:**
```javascript
get_account_projects({ account_id: "team-alpha" })
```

**Response:**
```json
{
  "success": true,
  "account_id": "team-alpha",
  "account_name": "team-alpha",
  "projects": [
    {
      "id": "10000",
      "key": "PROJ",
      "name": "Main Project",
      "description": "Main development project"
    }
  ],
  "total": 1
}
```

### 3. `log_time`

Enhanced time logging tool that requires an account_id parameter.

**Usage:**
```javascript
// Log time to account without specific issue
log_time({
  account_id: "team-alpha",
  time_spent: "2h",
  description: "Feature development"
})

// Log time to specific issue within account
log_time({
  account_id: "team-alpha",
  time_spent: "1h",
  issue_key: "PROJ-123",
  description: "Bug fix for login issue"
})

// Log time with project association
log_time({
  account_id: "team-alpha",
  time_spent: "30m",
  project_id: "PROJ",
  description: "Code review"
})
```

**Response:**
```json
{
  "success": true,
  "message": "Time logged successfully to account team-alpha",
  "account_name": "team-alpha",
  "time_log_entry": {
    "id": "account_team-alpha_1672531200",
    "account_id": "team-alpha",
    "time_spent": "2h",
    "time_spent_seconds": 7200,
    "description": "Feature development"
  }
}
```

## Usage Examples

### Example 1: Development Team Workflow

```bash
# Configuration
ACCOUNT_MAPPINGS=frontend:WEB,MOBILE;backend:API,DB

# Usage
# 1. List available accounts
list_accounts()

# 2. Get projects for frontend team
get_account_projects({ account_id: "frontend" })

# 3. Log time for frontend development
log_time({
  account_id: "frontend",
  time_spent: "3h",
  project_id: "WEB",
  description: "Implemented user authentication"
})
```

### Example 2: Client Work Management

```bash
# Configuration
ACCOUNT_MAPPINGS=client-acme:ACME1,ACME2;client-beta:BETA1,BETA2

# Usage
# 1. Check client accounts
list_accounts({ search_filter: "client" })

# 2. Get projects for ACME client
get_account_projects({ account_id: "client-acme" })

# 3. Log time for client work
log_time({
  account_id: "client-acme",
  time_spent: "4h",
  issue_key: "ACME1-456",
  description: "Client meeting and requirements gathering"
})
```

### Example 3: Mixed Project Types

```bash
# Configuration
ACCOUNT_MAPPINGS=product:PROD,FEAT;maintenance:MAINT,BUGS;research:RND,POC

# Usage
# 1. Log product development time
log_time({
  account_id: "product",
  time_spent: "2h",
  project_id: "PROD",
  description: "New feature implementation"
})

# 2. Log maintenance time
log_time({
  account_id: "maintenance",
  time_spent: "1h",
  issue_key: "MAINT-789",
  description: "Fixed critical bug in payment system"
})

# 3. Log research time
log_time({
  account_id: "research",
  time_spent: "30m",
  project_id: "RND",
  description: "Evaluated new technology stack"
})
```

## Validation and Error Handling

### Account Validation
- The system validates that the specified `account_id` exists
- Ensures the account is active
- Verifies project access if `project_id` is provided

### Error Responses
```json
{
  "success": false,
  "error": "Invalid account access for account team-alpha"
}
```

## Best Practices

### 1. Account Naming
- Use descriptive, consistent account IDs
- Consider using prefixes for different types (e.g., `team-`, `client-`, `dept-`)
- Avoid special characters except hyphens and underscores

### 2. Project Mapping
- Ensure all project keys in the mapping exist in your Jira instance
- Review and update mappings when projects are added/removed
- Consider project lifecycle when creating accounts

### 3. Time Logging Strategy
- Always specify `account_id` when logging time
- Use `issue_key` for specific issue-related work
- Use `project_id` for general project work
- Provide meaningful descriptions for time entries

### 4. Security Considerations
- Review account mappings regularly
- Ensure users only have access to appropriate accounts
- Consider using environment-specific configurations
- Audit time logging activities regularly

## Troubleshooting

### Common Issues

1. **Account Not Found**
   - Check that the account ID exists in your `ACCOUNT_MAPPINGS`
   - Verify the account ID spelling and case sensitivity

2. **Project Access Denied**
   - Ensure the project key is included in the account's project list
   - Verify the project exists in your Jira instance

3. **Default Account Behavior**
   - If no mappings are configured, all projects go to the "default" account
   - Check project filtering settings (`JIRA_PROJECTS_FILTER`)

### Debug Mode
Enable verbose logging to troubleshoot configuration issues:

```bash
MCP_VERBOSE=true
MCP_VERY_VERBOSE=true
```

## Migration Guide

### From Issue-Based to Account-Based Time Logging

1. **Identify Your Accounts**: Determine how you want to group your projects
2. **Create Account Mappings**: Define the `ACCOUNT_MAPPINGS` configuration
3. **Update Time Logging Workflows**: Modify your time logging to use the new `log_time` tool
4. **Test Configuration**: Verify that accounts and projects are correctly mapped
5. **Train Users**: Ensure users understand the new account-based workflow

### Backward Compatibility
- The existing `add_worklog` tool continues to work
- The new `log_time` tool provides enhanced account-based functionality
- Both tools can be used simultaneously during transition periods

## API Reference

### Environment Variables
- `ACCOUNT_MAPPINGS`: Account-to-project mappings configuration
- `JIRA_PROJECTS_FILTER`: Project filtering (still applies to account projects)
- `READ_ONLY_MODE`: Disables write operations including time logging

### Tool Tags
- `jira`: Standard Jira tools
- `accounts`: Account-based tools
- `read`: Read-only operations
- `write`: Write operations (requires write access)

### Error Codes
- `Authentication/Permission Error`: Authentication issues
- `Network or API Error`: Network connectivity issues
- `Configuration Error`: Invalid configuration or missing accounts 