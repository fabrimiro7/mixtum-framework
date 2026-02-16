# base_modules/integrations/slack/services.py
"""
Slack Integration Service
Provides primitives for interacting with Slack API:
- Fetching messages from channels
- Sending messages
- Replying to threads
- Getting channel/user info
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """Represents a Slack message."""
    ts: str  # Slack timestamp (message ID)
    channel: str
    text: str
    user: Optional[str] = None
    thread_ts: Optional[str] = None
    reply_count: int = 0
    reactions: Optional[List[Dict]] = None
    files: Optional[List[Dict]] = None
    raw: Optional[Dict] = None


class SlackError(Exception):
    """Custom exception for Slack API errors."""
    def __init__(self, message: str, error_code: Optional[str] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.response = response


class SlackService:
    """
    Service class for Slack API interactions.
    
    Usage:
        slack = SlackService()
        # or with custom token:
        slack = SlackService(bot_token="xoxb-...")
        
        messages = slack.get_channel_messages("C12345678")
        slack.send_message("C12345678", "Hello!")
        slack.reply_to_thread("C12345678", "1234567890.123456", "Reply text")
    """
    
    BASE_URL = "https://slack.com/api"
    
    def __init__(
        self, 
        bot_token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize SlackService.
        
        Args:
            bot_token: Slack Bot Token (xoxb-...). If not provided, 
                       uses SLACK_BOT_TOKEN from environment/settings.
            timeout: Request timeout in seconds.
        """
        self.bot_token = bot_token or getattr(settings, 'SLACK_BOT_TOKEN', None) or os.environ.get('SLACK_BOT_TOKEN')
        self.timeout = timeout
        
        if not self.bot_token:
            raise SlackError("Slack bot token not configured. Set SLACK_BOT_TOKEN environment variable.")
    
    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a request to Slack API."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                error = result.get("error", "unknown_error")
                raise SlackError(
                    f"Slack API error: {error}",
                    error_code=error,
                    response=result
                )
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.exception("Slack API request failed")
            raise SlackError(f"Request failed: {str(e)}")
    
    # -------------------------------------------------------------------------
    # Channel Operations
    # -------------------------------------------------------------------------
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Get information about a channel.
        
        Args:
            channel_id: The Slack channel ID (e.g., C12345678)
            
        Returns:
            Channel info dictionary
        """
        result = self._request("GET", "conversations.info", params={"channel": channel_id})
        return result.get("channel", {})
    
    def list_channels(
        self, 
        types: str = "public_channel,private_channel",
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List channels the bot has access to.
        
        Args:
            types: Comma-separated channel types (public_channel, private_channel, mpim, im)
            limit: Number of channels to return (max 1000)
            cursor: Pagination cursor
            
        Returns:
            Dict with 'channels' list and 'response_metadata' for pagination
        """
        params = {"types": types, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        return self._request("GET", "conversations.list", params=params)
    
    # -------------------------------------------------------------------------
    # Message Operations
    # -------------------------------------------------------------------------
    
    def get_channel_messages(
        self, 
        channel_id: str,
        limit: int = 100,
        cursor: Optional[str] = None,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        inclusive: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch messages from a channel.
        
        Args:
            channel_id: The Slack channel ID
            limit: Number of messages to return (max 1000)
            cursor: Pagination cursor for next page
            oldest: Only messages after this Unix timestamp
            latest: Only messages before this Unix timestamp
            inclusive: Include messages with oldest/latest timestamps
            
        Returns:
            Dict with 'messages' list and 'response_metadata' for pagination
        """
        params = {
            "channel": channel_id,
            "limit": limit,
            "inclusive": inclusive
        }
        if cursor:
            params["cursor"] = cursor
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
        
        result = self._request("GET", "conversations.history", params=params)
        return result
    
    def get_thread_replies(
        self, 
        channel_id: str, 
        thread_ts: str,
        limit: int = 100,
        cursor: Optional[str] = None,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        inclusive: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch replies to a thread.
        
        Args:
            channel_id: The Slack channel ID
            thread_ts: Timestamp of the parent message (thread root)
            limit: Number of replies to return
            cursor: Pagination cursor
            oldest: Only messages after this Unix timestamp
            latest: Only messages before this Unix timestamp
            inclusive: Include messages with oldest/latest timestamps
            
        Returns:
            Dict with 'messages' list (first is parent, rest are replies)
        """
        params = {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": limit,
            "inclusive": inclusive
        }
        if cursor:
            params["cursor"] = cursor
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
        
        result = self._request("GET", "conversations.replies", params=params)
        return result
    
    def send_message(
        self,
        channel_id: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        reply_broadcast: bool = False,
        unfurl_links: bool = True,
        unfurl_media: bool = True,
        mrkdwn: bool = True
    ) -> SlackMessage:
        """
        Send a message to a channel.
        
        Args:
            channel_id: The Slack channel ID
            text: Message text (also used as fallback for blocks)
            blocks: Slack Block Kit blocks for rich formatting
            attachments: Legacy attachments
            thread_ts: If set, sends as reply to this thread
            reply_broadcast: Also post to channel when replying to thread
            unfurl_links: Enable link unfurling
            unfurl_media: Enable media unfurling
            mrkdwn: Enable Slack markdown parsing
            
        Returns:
            SlackMessage object with the sent message details
        """
        data = {
            "channel": channel_id,
            "text": text,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
            "mrkdwn": mrkdwn
        }
        
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        if thread_ts:
            data["thread_ts"] = thread_ts
            data["reply_broadcast"] = reply_broadcast
        
        result = self._request("POST", "chat.postMessage", data=data)
        
        return SlackMessage(
            ts=result.get("ts", ""),
            channel=result.get("channel", channel_id),
            text=text,
            thread_ts=thread_ts,
            raw=result
        )
    
    def reply_to_thread(
        self,
        channel_id: str,
        thread_ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
        reply_broadcast: bool = False
    ) -> SlackMessage:
        """
        Reply to a thread (convenience wrapper around send_message).
        
        Args:
            channel_id: The Slack channel ID
            thread_ts: Timestamp of the parent message (thread root)
            text: Reply text
            blocks: Slack Block Kit blocks
            attachments: Legacy attachments
            reply_broadcast: Also post to main channel
            
        Returns:
            SlackMessage object with the sent reply details
        """
        return self.send_message(
            channel_id=channel_id,
            text=text,
            blocks=blocks,
            attachments=attachments,
            thread_ts=thread_ts,
            reply_broadcast=reply_broadcast
        )
    
    def update_message(
        self,
        channel_id: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> SlackMessage:
        """
        Update an existing message.
        
        Args:
            channel_id: The Slack channel ID
            ts: Timestamp of the message to update
            text: New message text
            blocks: New Block Kit blocks
            attachments: New attachments
            
        Returns:
            SlackMessage with updated message details
        """
        data = {
            "channel": channel_id,
            "ts": ts,
            "text": text
        }
        
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        
        result = self._request("POST", "chat.update", data=data)
        
        return SlackMessage(
            ts=result.get("ts", ts),
            channel=result.get("channel", channel_id),
            text=text,
            raw=result
        )
    
    def delete_message(self, channel_id: str, ts: str) -> bool:
        """
        Delete a message.
        
        Args:
            channel_id: The Slack channel ID
            ts: Timestamp of the message to delete
            
        Returns:
            True if deleted successfully
        """
        self._request("POST", "chat.delete", data={"channel": channel_id, "ts": ts})
        return True
    
    # -------------------------------------------------------------------------
    # User Operations
    # -------------------------------------------------------------------------
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user_id: The Slack user ID (e.g., U12345678)
            
        Returns:
            User info dictionary
        """
        result = self._request("GET", "users.info", params={"user": user_id})
        return result.get("user", {})
    
    def list_users(
        self, 
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workspace users.
        
        Args:
            limit: Number of users to return
            cursor: Pagination cursor
            
        Returns:
            Dict with 'members' list and 'response_metadata'
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        return self._request("GET", "users.list", params=params)
    
    # -------------------------------------------------------------------------
    # Reactions
    # -------------------------------------------------------------------------
    
    def add_reaction(self, channel_id: str, ts: str, emoji: str) -> bool:
        """
        Add a reaction to a message.
        
        Args:
            channel_id: The Slack channel ID
            ts: Message timestamp
            emoji: Emoji name without colons (e.g., 'thumbsup')
            
        Returns:
            True if added successfully
        """
        self._request("POST", "reactions.add", data={
            "channel": channel_id,
            "timestamp": ts,
            "name": emoji
        })
        return True
    
    def remove_reaction(self, channel_id: str, ts: str, emoji: str) -> bool:
        """
        Remove a reaction from a message.
        
        Args:
            channel_id: The Slack channel ID
            ts: Message timestamp
            emoji: Emoji name without colons
            
        Returns:
            True if removed successfully
        """
        self._request("POST", "reactions.remove", data={
            "channel": channel_id,
            "timestamp": ts,
            "name": emoji
        })
        return True


# -----------------------------------------------------------------------------
# Module-level convenience functions
# -----------------------------------------------------------------------------

_default_service: Optional[SlackService] = None


def get_slack_service(bot_token: Optional[str] = None) -> SlackService:
    """
    Get or create a SlackService instance.
    
    Args:
        bot_token: Optional bot token. If provided, creates a new instance.
                   If not, returns/creates a singleton.
    """
    global _default_service
    
    if bot_token:
        return SlackService(bot_token=bot_token)
    
    if _default_service is None:
        _default_service = SlackService()
    
    return _default_service


def send_slack_message(
    channel_id: str,
    text: str,
    thread_ts: Optional[str] = None,
    blocks: Optional[List[Dict]] = None
) -> SlackMessage:
    """
    Convenience function to send a Slack message.
    
    Args:
        channel_id: The Slack channel ID
        text: Message text
        thread_ts: Optional thread timestamp for replies
        blocks: Optional Block Kit blocks
        
    Returns:
        SlackMessage object
    """
    service = get_slack_service()
    return service.send_message(
        channel_id=channel_id,
        text=text,
        thread_ts=thread_ts,
        blocks=blocks
    )


def get_slack_messages(
    channel_id: str,
    limit: int = 100,
    oldest: Optional[str] = None,
    latest: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to fetch messages from a channel.
    
    Args:
        channel_id: The Slack channel ID
        limit: Number of messages to fetch
        oldest: Only messages after this timestamp
        latest: Only messages before this timestamp
        
    Returns:
        List of message dictionaries
    """
    service = get_slack_service()
    result = service.get_channel_messages(
        channel_id=channel_id,
        limit=limit,
        oldest=oldest,
        latest=latest
    )
    return result.get("messages", [])
