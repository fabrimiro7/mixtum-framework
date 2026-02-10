# integrations/n8n/views.py
"""
API Views for n8n integration.
Provides endpoints for calling n8n webhooks with custom payloads.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated

from .services import N8nService, N8nError, get_n8n_service
from .serializers import (
    CallWebhookSerializer,
    TriggerWorkflowSerializer,
    ExecutionStatusSerializer,
    BatchWebhookSerializer,
)


class N8nViewSet(ViewSet):
    """
    ViewSet for n8n operations.
    
    Provides endpoints for:
    - Calling webhooks with custom payloads
    - Triggering workflows by ID
    - Checking execution status
    - Batch webhook calls
    """
    permission_classes = [IsAuthenticated]
    
    def _get_service(self) -> N8nService:
        """Get or create n8n service instance."""
        return get_n8n_service()
    
    def _handle_n8n_error(self, e: N8nError) -> Response:
        """Handle n8n API errors uniformly."""
        return Response(
            {
                "error": str(e),
                "status_code": e.status_code,
                "response_data": e.response_data
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=["post"], url_path="call-webhook")
    def call_webhook(self, request):
        """
        Call an n8n webhook with a custom payload.
        
        POST /api/n8n/call-webhook/
        {
            "webhook_path": "my-webhook",
            "payload": {"key": "value"},
            "method": "POST",  // optional, default POST
            "query_params": {},  // optional
            "headers": {},  // optional
            "timeout": 30,  // optional
            "is_test": false  // optional, use test endpoint
        }
        """
        serializer = CallWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            
            if data.get("is_test"):
                result = service.call_webhook_test(
                    webhook_path=data["webhook_path"],
                    payload=data.get("payload"),
                    method=data.get("method", "POST"),
                    query_params=data.get("query_params"),
                    headers=data.get("headers"),
                    timeout=data.get("timeout")
                )
            else:
                result = service.call_webhook(
                    webhook_path=data["webhook_path"],
                    payload=data.get("payload"),
                    method=data.get("method", "POST"),
                    query_params=data.get("query_params"),
                    headers=data.get("headers"),
                    timeout=data.get("timeout")
                )
            
            response_status = (
                status.HTTP_200_OK if result.success 
                else status.HTTP_502_BAD_GATEWAY
            )
            
            return Response(result.to_dict(), status=response_status)
            
        except N8nError as e:
            return self._handle_n8n_error(e)
    
    @action(detail=False, methods=["post"], url_path="trigger-workflow")
    def trigger_workflow(self, request):
        """
        Trigger an n8n workflow by ID.
        
        Note: Requires N8N_API_KEY to be configured.
        
        POST /api/n8n/trigger-workflow/
        {
            "workflow_id": "123",
            "payload": {"key": "value"},  // optional
            "wait_for_completion": false  // optional
        }
        """
        serializer = TriggerWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.trigger_workflow(
                workflow_id=data["workflow_id"],
                payload=data.get("payload"),
                wait_for_completion=data.get("wait_for_completion", False)
            )
            
            response_status = (
                status.HTTP_200_OK if result.success 
                else status.HTTP_502_BAD_GATEWAY
            )
            
            return Response(result.to_dict(), status=response_status)
            
        except N8nError as e:
            return self._handle_n8n_error(e)
    
    @action(detail=False, methods=["post"], url_path="execution-status")
    def execution_status(self, request):
        """
        Get the status of a workflow execution.
        
        Note: Requires N8N_API_KEY to be configured.
        
        POST /api/n8n/execution-status/
        {
            "execution_id": "12345"
        }
        """
        serializer = ExecutionStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            service = self._get_service()
            result = service.get_execution_status(data["execution_id"])
            
            response_status = (
                status.HTTP_200_OK if result.success 
                else status.HTTP_502_BAD_GATEWAY
            )
            
            return Response(result.to_dict(), status=response_status)
            
        except N8nError as e:
            return self._handle_n8n_error(e)
    
    @action(detail=False, methods=["post"], url_path="batch-webhook")
    def batch_webhook(self, request):
        """
        Call multiple webhooks in sequence.
        
        POST /api/n8n/batch-webhook/
        {
            "webhooks": [
                {"webhook_path": "hook1", "payload": {}},
                {"webhook_path": "hook2", "payload": {}}
            ],
            "parallel": false  // not yet implemented
        }
        """
        serializer = BatchWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        results = []
        all_success = True
        
        try:
            service = self._get_service()
            
            for webhook_config in data["webhooks"]:
                try:
                    if webhook_config.get("is_test"):
                        result = service.call_webhook_test(
                            webhook_path=webhook_config["webhook_path"],
                            payload=webhook_config.get("payload"),
                            method=webhook_config.get("method", "POST"),
                            query_params=webhook_config.get("query_params"),
                            headers=webhook_config.get("headers"),
                            timeout=webhook_config.get("timeout")
                        )
                    else:
                        result = service.call_webhook(
                            webhook_path=webhook_config["webhook_path"],
                            payload=webhook_config.get("payload"),
                            method=webhook_config.get("method", "POST"),
                            query_params=webhook_config.get("query_params"),
                            headers=webhook_config.get("headers"),
                            timeout=webhook_config.get("timeout")
                        )
                    
                    results.append({
                        "webhook_path": webhook_config["webhook_path"],
                        **result.to_dict()
                    })
                    
                    if not result.success:
                        all_success = False
                        
                except N8nError as e:
                    all_success = False
                    results.append({
                        "webhook_path": webhook_config["webhook_path"],
                        "success": False,
                        "error": str(e),
                        "status_code": e.status_code
                    })
            
            response_status = (
                status.HTTP_200_OK if all_success 
                else status.HTTP_207_MULTI_STATUS
            )
            
            return Response({
                "all_success": all_success,
                "results": results,
                "total": len(results),
                "successful": sum(1 for r in results if r.get("success"))
            }, status=response_status)
            
        except N8nError as e:
            return self._handle_n8n_error(e)
    
    @action(detail=False, methods=["get"], url_path="health")
    def health_check(self, request):
        """
        Check if n8n service is configured and reachable.
        
        GET /api/n8n/health/
        """
        try:
            service = self._get_service()
            return Response({
                "configured": True,
                "base_url": service.base_url,
                "has_api_key": bool(service.api_key)
            })
        except N8nError as e:
            return Response({
                "configured": False,
                "error": str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
