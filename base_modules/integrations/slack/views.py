# base_modules/integrations/slack/views.py
"""
API Views for Slack integration.
Provides endpoints for interacting with Slack.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated

from .services import SlackService, SlackError, get_slack_service
from .serializers import (
    SendMessageSerializer,
    ReplyToThreadSerializer,
    GetMessagesSerializer,
    GetThreadRepliesSerializer,
    UpdateMessageSerializer,
    DeleteMessageSerializer,
    AddReactionSerializer,
    ChannelInfoSerializer,
    UserInfoSerializer,
)


class SlackViewSet(ViewSet):
    """
    ViewSet for Slack operations.
    
    Provides endpoints for:
    - Sending messages
    - Replying to threads
    - Fetching channel messages
    - Fetching thread replies
    - Managing messages (update, delete)
    - Adding/removing reactions
    - Getting channel/user info
    """
    permission_classes = [IsAuthenticated]
    
    def _get_service(self) -> SlackService:
        """Get or create Slack service instance."""
        return get_slack_service()
    
    def _handle_slack_error(self, e: SlackError) -> Response:
        """Handle Slack API errors uniformly."""
        return Response(
            {
                "error": str(e),
                "error_code": e.error_code,
                "details": e.response
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=["post"], url_path="send-message")
    def send_message(self, request):
        """
        Send a message to a Slack channel.
        
        POST /api/slack/send-message/
        {
            "channel_id": "C12345678",
            "text": "Hello, World!",
            "thread_ts": null,  // optional: for thread replies
            "blocks": [],  // optional: Block Kit blocks
            "reply_broadcast": false  // optional
        }
        """
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.send_message(
                channel_id=data["channel_id"],
                text=data["text"],
                thread_ts=data.get("thread_ts"),
                blocks=data.get("blocks"),
                reply_broadcast=data.get("reply_broadcast", False)
            )
            return Response({
                "ok": True,
                "ts": result.ts,
                "channel": result.channel,
                "text": result.text,
                "thread_ts": result.thread_ts
            }, status=status.HTTP_201_CREATED)
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="reply-thread")
    def reply_to_thread(self, request):
        """
        Reply to a Slack thread.
        
        POST /api/slack/reply-thread/
        {
            "channel_id": "C12345678",
            "thread_ts": "1234567890.123456",
            "text": "This is a reply",
            "blocks": [],  // optional
            "reply_broadcast": false  // optional
        }
        """
        serializer = ReplyToThreadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.reply_to_thread(
                channel_id=data["channel_id"],
                thread_ts=data["thread_ts"],
                text=data["text"],
                blocks=data.get("blocks"),
                reply_broadcast=data.get("reply_broadcast", False)
            )
            return Response({
                "ok": True,
                "ts": result.ts,
                "channel": result.channel,
                "text": result.text,
                "thread_ts": result.thread_ts
            }, status=status.HTTP_201_CREATED)
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="get-messages")
    def get_messages(self, request):
        """
        Fetch messages from a Slack channel.
        
        POST /api/slack/get-messages/
        {
            "channel_id": "C12345678",
            "limit": 100,  // optional
            "oldest": null,  // optional: Unix timestamp
            "latest": null,  // optional: Unix timestamp
            "cursor": null  // optional: pagination
        }
        """
        serializer = GetMessagesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.get_channel_messages(
                channel_id=data["channel_id"],
                limit=data.get("limit", 100),
                oldest=data.get("oldest"),
                latest=data.get("latest"),
                cursor=data.get("cursor")
            )
            return Response({
                "ok": True,
                "messages": result.get("messages", []),
                "has_more": result.get("has_more", False),
                "response_metadata": result.get("response_metadata", {})
            })
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="get-thread-replies")
    def get_thread_replies(self, request):
        """
        Fetch replies to a thread.
        
        POST /api/slack/get-thread-replies/
        {
            "channel_id": "C12345678",
            "thread_ts": "1234567890.123456",
            "limit": 100,  // optional
            "cursor": null  // optional
        }
        """
        serializer = GetThreadRepliesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.get_thread_replies(
                channel_id=data["channel_id"],
                thread_ts=data["thread_ts"],
                limit=data.get("limit", 100),
                cursor=data.get("cursor")
            )
            return Response({
                "ok": True,
                "messages": result.get("messages", []),
                "has_more": result.get("has_more", False),
                "response_metadata": result.get("response_metadata", {})
            })
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="update-message")
    def update_message(self, request):
        """
        Update an existing Slack message.
        
        POST /api/slack/update-message/
        {
            "channel_id": "C12345678",
            "ts": "1234567890.123456",
            "text": "Updated message text",
            "blocks": []  // optional
        }
        """
        serializer = UpdateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.update_message(
                channel_id=data["channel_id"],
                ts=data["ts"],
                text=data["text"],
                blocks=data.get("blocks")
            )
            return Response({
                "ok": True,
                "ts": result.ts,
                "channel": result.channel,
                "text": result.text
            })
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="delete-message")
    def delete_message(self, request):
        """
        Delete a Slack message.
        
        POST /api/slack/delete-message/
        {
            "channel_id": "C12345678",
            "ts": "1234567890.123456"
        }
        """
        serializer = DeleteMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            service.delete_message(
                channel_id=data["channel_id"],
                ts=data["ts"]
            )
            return Response({"ok": True})
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="add-reaction")
    def add_reaction(self, request):
        """
        Add a reaction to a message.
        
        POST /api/slack/add-reaction/
        {
            "channel_id": "C12345678",
            "ts": "1234567890.123456",
            "emoji": "thumbsup"
        }
        """
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            service.add_reaction(
                channel_id=data["channel_id"],
                ts=data["ts"],
                emoji=data["emoji"]
            )
            return Response({"ok": True})
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="remove-reaction")
    def remove_reaction(self, request):
        """
        Remove a reaction from a message.
        
        POST /api/slack/remove-reaction/
        {
            "channel_id": "C12345678",
            "ts": "1234567890.123456",
            "emoji": "thumbsup"
        }
        """
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            service.remove_reaction(
                channel_id=data["channel_id"],
                ts=data["ts"],
                emoji=data["emoji"]
            )
            return Response({"ok": True})
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="channel-info")
    def channel_info(self, request):
        """
        Get information about a Slack channel.
        
        POST /api/slack/channel-info/
        {
            "channel_id": "C12345678"
        }
        """
        serializer = ChannelInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = self._get_service()
            channel = service.get_channel_info(serializer.validated_data["channel_id"])
            return Response({"ok": True, "channel": channel})
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["post"], url_path="user-info")
    def user_info(self, request):
        """
        Get information about a Slack user.
        
        POST /api/slack/user-info/
        {
            "user_id": "U12345678"
        }
        """
        serializer = UserInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = self._get_service()
            user = service.get_user_info(serializer.validated_data["user_id"])
            return Response({"ok": True, "user": user})
        except SlackError as e:
            return self._handle_slack_error(e)
    
    @action(detail=False, methods=["get"], url_path="channels")
    def list_channels(self, request):
        """
        List channels the bot has access to.
        
        GET /api/slack/channels/
        Query params:
        - limit: int (default 100)
        - cursor: str (optional, for pagination)
        """
        limit = int(request.query_params.get("limit", 100))
        cursor = request.query_params.get("cursor")
        
        try:
            service = self._get_service()
            result = service.list_channels(limit=limit, cursor=cursor)
            return Response({
                "ok": True,
                "channels": result.get("channels", []),
                "response_metadata": result.get("response_metadata", {})
            })
        except SlackError as e:
            return self._handle_slack_error(e)
