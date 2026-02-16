# base_modules/integrations/slack/serializers.py
"""
Serializers for Slack integration API endpoints.
"""
from rest_framework import serializers


class SlackMessageSerializer(serializers.Serializer):
    """Serializer for Slack message output."""
    ts = serializers.CharField(read_only=True, help_text="Message timestamp (ID)")
    channel = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)
    user = serializers.CharField(read_only=True, allow_null=True)
    thread_ts = serializers.CharField(read_only=True, allow_null=True)
    reply_count = serializers.IntegerField(read_only=True, default=0)
    type = serializers.CharField(read_only=True, default="message")
    subtype = serializers.CharField(read_only=True, allow_null=True)


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a Slack message."""
    channel_id = serializers.CharField(
        required=True, 
        help_text="Slack channel ID (e.g., C12345678)"
    )
    text = serializers.CharField(
        required=True, 
        help_text="Message text"
    )
    thread_ts = serializers.CharField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        help_text="Thread timestamp for replies"
    )
    blocks = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True,
        help_text="Slack Block Kit blocks for rich formatting"
    )
    reply_broadcast = serializers.BooleanField(
        required=False, 
        default=False,
        help_text="Also post to channel when replying to thread"
    )


class ReplyToThreadSerializer(serializers.Serializer):
    """Serializer for replying to a Slack thread."""
    channel_id = serializers.CharField(
        required=True, 
        help_text="Slack channel ID"
    )
    thread_ts = serializers.CharField(
        required=True, 
        help_text="Thread timestamp (parent message ts)"
    )
    text = serializers.CharField(
        required=True, 
        help_text="Reply text"
    )
    blocks = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True,
        help_text="Slack Block Kit blocks"
    )
    reply_broadcast = serializers.BooleanField(
        required=False, 
        default=False,
        help_text="Also post to main channel"
    )


class GetMessagesSerializer(serializers.Serializer):
    """Serializer for fetching channel messages."""
    channel_id = serializers.CharField(
        required=True, 
        help_text="Slack channel ID"
    )
    limit = serializers.IntegerField(
        required=False, 
        default=100, 
        min_value=1, 
        max_value=1000,
        help_text="Number of messages to fetch"
    )
    oldest = serializers.CharField(
        required=False, 
        allow_null=True,
        help_text="Only messages after this Unix timestamp"
    )
    latest = serializers.CharField(
        required=False, 
        allow_null=True,
        help_text="Only messages before this Unix timestamp"
    )
    cursor = serializers.CharField(
        required=False, 
        allow_null=True,
        help_text="Pagination cursor"
    )


class GetThreadRepliesSerializer(serializers.Serializer):
    """Serializer for fetching thread replies."""
    channel_id = serializers.CharField(
        required=True, 
        help_text="Slack channel ID"
    )
    thread_ts = serializers.CharField(
        required=True, 
        help_text="Thread timestamp (parent message ts)"
    )
    limit = serializers.IntegerField(
        required=False, 
        default=100, 
        min_value=1, 
        max_value=1000,
        help_text="Number of replies to fetch"
    )
    cursor = serializers.CharField(
        required=False, 
        allow_null=True,
        help_text="Pagination cursor"
    )


class UpdateMessageSerializer(serializers.Serializer):
    """Serializer for updating a Slack message."""
    channel_id = serializers.CharField(required=True)
    ts = serializers.CharField(
        required=True, 
        help_text="Message timestamp to update"
    )
    text = serializers.CharField(required=True)
    blocks = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True
    )


class DeleteMessageSerializer(serializers.Serializer):
    """Serializer for deleting a Slack message."""
    channel_id = serializers.CharField(required=True)
    ts = serializers.CharField(
        required=True, 
        help_text="Message timestamp to delete"
    )


class AddReactionSerializer(serializers.Serializer):
    """Serializer for adding a reaction to a message."""
    channel_id = serializers.CharField(required=True)
    ts = serializers.CharField(required=True, help_text="Message timestamp")
    emoji = serializers.CharField(
        required=True, 
        help_text="Emoji name without colons (e.g., 'thumbsup')"
    )


class ChannelInfoSerializer(serializers.Serializer):
    """Serializer for channel info request."""
    channel_id = serializers.CharField(required=True, help_text="Slack channel ID")


class UserInfoSerializer(serializers.Serializer):
    """Serializer for user info request."""
    user_id = serializers.CharField(required=True, help_text="Slack user ID")
