"""
Jira data models for the MCP Atlassian integration.

This package provides Pydantic models for Jira API data structures,
organized by entity type for better maintainability and clarity.
"""

from .account import Account, TimeLogEntry
from .agile import JiraBoard, JiraSprint
from .comment import JiraComment
from .common import (
    JiraAttachment,
    JiraIssueType,
    JiraPriority,
    JiraResolution,
    JiraStatus,
    JiraStatusCategory,
    JiraTimetracking,
    JiraUser,
)
from .issue import JiraIssue
from .link import (
    JiraIssueLink,
    JiraIssueLinkType,
    JiraLinkedIssue,
    JiraLinkedIssueFields,
)
from .project import JiraProject
from .search import JiraSearchResult
from .workflow import JiraTransition
from .worklog import JiraWorklog

__all__ = [
    # Account models
    "Account",
    "TimeLogEntry",
    # Common models
    "JiraUser",
    "JiraStatusCategory",
    "JiraStatus",
    "JiraIssueType",
    "JiraPriority",
    "JiraAttachment",
    "JiraResolution",
    "JiraTimetracking",
    # Entity-specific models
    "JiraComment",
    "JiraWorklog",
    "JiraProject",
    "JiraTransition",
    "JiraBoard",
    "JiraSprint",
    "JiraIssue",
    "JiraSearchResult",
    "JiraIssueLinkType",
    "JiraIssueLink",
    "JiraLinkedIssue",
    "JiraLinkedIssueFields",
]
