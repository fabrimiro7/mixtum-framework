# integrations/n8n/serializers.py
"""
Serializers for n8n integration API endpoints.
"""
from rest_framework import serializers


class WebhookResponseSerializer(serializers.Serializer):
    """Serializer for webhook response output."""
    status_code = serializers.IntegerField(read_only=True)
    success = serializers.BooleanField(read_only=True)
    data = serializers.JSONField(read_only=True, allow_null=True)
    elapsed_ms = serializers.FloatField(read_only=True)
    error = serializers.CharField(read_only=True, allow_null=True)


class CallWebhookSerializer(serializers.Serializer):
    """Serializer for calling an n8n webhook."""
    webhook_path = serializers.CharField(
        required=True,
        help_text="Webhook path/ID (e.g., 'my-webhook' or 'production/my-webhook')"
    )
    payload = serializers.JSONField(
        required=False,
        allow_null=True,
        default=None,
        help_text="JSON payload to send to the webhook"
    )
    method = serializers.ChoiceField(
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        default="POST",
        required=False,
        help_text="HTTP method to use"
    )
    query_params = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional query parameters"
    )
    headers = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional additional headers"
    )
    timeout = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=300,
        help_text="Request timeout in seconds (default 30)"
    )
    is_test = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If True, use test webhook endpoint (/webhook-test/)"
    )


class TriggerWorkflowSerializer(serializers.Serializer):
    """Serializer for triggering an n8n workflow by ID."""
    workflow_id = serializers.CharField(
        required=True,
        help_text="The n8n workflow ID to trigger"
    )
    payload = serializers.JSONField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Data to pass to the workflow"
    )
    wait_for_completion = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Wait for the workflow to complete before returning"
    )


class ExecutionStatusSerializer(serializers.Serializer):
    """Serializer for getting execution status."""
    execution_id = serializers.CharField(
        required=True,
        help_text="The execution ID to check"
    )


class BatchWebhookSerializer(serializers.Serializer):
    """Serializer for calling multiple webhooks."""
    webhooks = serializers.ListField(
        child=CallWebhookSerializer(),
        min_length=1,
        max_length=10,
        help_text="List of webhook configurations to call"
    )
    parallel = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Execute webhooks in parallel (not yet implemented)"
    )
