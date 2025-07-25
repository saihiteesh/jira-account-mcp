"""Jira API module for mcp_atlassian.

This module provides various Jira API client implementations.
"""

# flake8: noqa

# Re-export the Jira class for backward compatibility
from atlassian.jira import Jira

from .accounts import AccountsMixin
from .attachments import AttachmentsMixin
from .boards import BoardsMixin
from .client import JiraClient
from .comments import CommentsMixin
from .config import JiraConfig
from .epics import EpicsMixin
from .fields import FieldsMixin
from .formatting import FormattingMixin
from .issues import IssuesMixin
from .links import LinksMixin
from .projects import ProjectsMixin
from .search import SearchMixin
from .sprints import SprintsMixin
from .transitions import TransitionsMixin
from .users import UsersMixin
from .worklog import WorklogMixin


class JiraFetcher(
    AccountsMixin,
    ProjectsMixin,
    FieldsMixin,
    FormattingMixin,
    TransitionsMixin,
    WorklogMixin,
    EpicsMixin,
    CommentsMixin,
    SearchMixin,
    IssuesMixin,
    UsersMixin,
    BoardsMixin,
    SprintsMixin,
    AttachmentsMixin,
    LinksMixin,
):
    """
    The main Jira client class providing access to all Jira operations.

    This class inherits from multiple mixins that provide specific functionality:
    - AccountsMixin: Account-based time logging and project management
    - ProjectsMixin: Project-related operations
    - FieldsMixin: Field-related operations
    - FormattingMixin: Content formatting utilities
    - TransitionsMixin: Issue transition operations
    - WorklogMixin: Worklog operations
    - EpicsMixin: Epic operations
    - CommentsMixin: Comment operations
    - SearchMixin: Search operations
    - IssuesMixin: Issue operations
    - UsersMixin: User operations
    - BoardsMixin: Board operations
    - SprintsMixin: Sprint operations
    - AttachmentsMixin: Attachment download operations
    - LinksMixin: Issue link operations

    The class structure is designed to maintain backward compatibility while
    improving code organization and maintainability.
    """

    pass


__all__ = ["JiraFetcher", "JiraConfig", "JiraClient", "Jira"]
