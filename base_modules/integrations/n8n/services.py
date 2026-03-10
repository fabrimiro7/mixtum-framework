# base_modules/integrations/n8n/services.py
"""
n8n Integration Service
Provides primitives for calling n8n webhooks with custom payloads.
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    """Supported HTTP methods for webhook calls."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class WebhookResponse:
    """Represents a response from an n8n webhook."""
    status_code: int
    success: bool
    data: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "success": self.success,
            "data": self.data,
            "headers": dict(self.headers),
            "elapsed_ms": self.elapsed_ms,
            "error": self.error
        }


class N8nError(Exception):
    """Custom exception for n8n API errors."""
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response_data: Any = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class N8nService:
    """
    Service class for n8n webhook interactions.
    
    Usage:
        n8n = N8nService()
        # or with custom base URL:
        n8n = N8nService(base_url="https://n8n.example.com")
        
        response = n8n.call_webhook("my-webhook", {"key": "value"})
        response = n8n.trigger_workflow("workflow-id", {"data": "payload"})
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize N8nService.
        
        Args:
            base_url: n8n instance base URL (e.g., https://n8n.example.com).
                      If not provided, uses N8N_BASE_URL from environment/settings.
            api_key: Optional API key for authenticated webhooks.
                     Uses N8N_API_KEY from environment if not provided.
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.base_url = (
            base_url or 
            getattr(settings, 'N8N_BASE_URL', None) or 
            os.environ.get('N8N_BASE_URL', '')
        ).rstrip('/')
        
        self.api_key = (
            api_key or 
            getattr(settings, 'N8N_API_KEY', None) or 
            os.environ.get('N8N_API_KEY')
        )
        
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        if not self.base_url:
            raise N8nError("n8n base URL not configured. Set N8N_BASE_URL environment variable.")
    
    def _build_headers(
        self, 
        custom_headers: Optional[Dict[str, str]] = None,
        include_api_key: bool = True
    ) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if include_api_key and self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def call_webhook(
        self,
        webhook_path: str,
        payload: Optional[Dict[str, Any]] = None,
        method: Union[str, HttpMethod] = HttpMethod.POST,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        raise_on_error: bool = False
    ) -> WebhookResponse:
        """
        Call an n8n webhook.
        
        Args:
            webhook_path: Webhook path/ID (e.g., "my-webhook" or "production/my-webhook").
                          Will be appended to base_url/webhook/
            payload: JSON payload to send (for POST/PUT/PATCH)
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            query_params: Optional query parameters
            headers: Optional additional headers
            timeout: Request timeout (overrides instance default)
            raise_on_error: If True, raise N8nError on non-2xx responses
            
        Returns:
            WebhookResponse object with response details
        """
        # Normalize method
        if isinstance(method, str):
            method = HttpMethod(method.upper())
        
        # Build URL
        webhook_path = webhook_path.lstrip('/')
        url = f"{self.base_url}/webhook/{webhook_path}"
        
        # Build headers
        request_headers = self._build_headers(headers)
        
        try:
            response = requests.request(
                method=method.value,
                url=url,
                json=payload if method in (HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH) else None,
                params=query_params,
                headers=request_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
            
            elapsed_ms = response.elapsed.total_seconds() * 1000
            
            # Try to parse JSON response
            try:
                data = response.json()
            except ValueError:
                data = response.text
            
            success = 200 <= response.status_code < 300
            
            result = WebhookResponse(
                status_code=response.status_code,
                success=success,
                data=data,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                error=None if success else f"HTTP {response.status_code}"
            )
            
            if raise_on_error and not success:
                raise N8nError(
                    f"Webhook call failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=data
                )
            
            return result
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"n8n webhook timeout: {url}")
            if raise_on_error:
                raise N8nError(f"Request timeout: {str(e)}")
            return WebhookResponse(
                status_code=0,
                success=False,
                error=f"Request timeout: {str(e)}"
            )
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"n8n webhook request failed: {url}")
            if raise_on_error:
                raise N8nError(f"Request failed: {str(e)}")
            return WebhookResponse(
                status_code=0,
                success=False,
                error=f"Request failed: {str(e)}"
            )
    
    def call_webhook_test(
        self,
        webhook_path: str,
        payload: Optional[Dict[str, Any]] = None,
        method: Union[str, HttpMethod] = HttpMethod.POST,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        raise_on_error: bool = False
    ) -> WebhookResponse:
        """
        Call an n8n TEST webhook (used during workflow development).
        
        Same as call_webhook but uses /webhook-test/ endpoint.
        
        Args:
            Same as call_webhook
            
        Returns:
            WebhookResponse object
        """
        if isinstance(method, str):
            method = HttpMethod(method.upper())
        
        webhook_path = webhook_path.lstrip('/')
        url = f"{self.base_url}/webhook-test/{webhook_path}"
        
        request_headers = self._build_headers(headers)
        
        try:
            response = requests.request(
                method=method.value,
                url=url,
                json=payload if method in (HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH) else None,
                params=query_params,
                headers=request_headers,
                timeout=timeout or self.timeout,
                verify=self.verify_ssl
            )
            
            elapsed_ms = response.elapsed.total_seconds() * 1000
            
            try:
                data = response.json()
            except ValueError:
                data = response.text
            
            success = 200 <= response.status_code < 300
            
            result = WebhookResponse(
                status_code=response.status_code,
                success=success,
                data=data,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                error=None if success else f"HTTP {response.status_code}"
            )
            
            if raise_on_error and not success:
                raise N8nError(
                    f"Test webhook call failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=data
                )
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"n8n test webhook request failed: {url}")
            if raise_on_error:
                raise N8nError(f"Request failed: {str(e)}")
            return WebhookResponse(
                status_code=0,
                success=False,
                error=f"Request failed: {str(e)}"
            )
    
    def trigger_workflow(
        self,
        workflow_id: str,
        payload: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = False
    ) -> WebhookResponse:
        """
        Trigger a workflow by ID (requires API access).
        
        Note: This uses n8n's API, not webhooks. Requires N8N_API_KEY.
        
        Args:
            workflow_id: The workflow ID to trigger
            payload: Optional data to pass to the workflow
            wait_for_completion: If True, wait for workflow to complete
            
        Returns:
            WebhookResponse with execution details
        """
        if not self.api_key:
            raise N8nError("API key required for triggering workflows by ID")
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-N8N-API-KEY": self.api_key
        }
        
        body = {}
        if payload:
            body["data"] = payload
        if wait_for_completion:
            body["waitForCompletion"] = True
        
        try:
            response = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=self.timeout if not wait_for_completion else 300,
                verify=self.verify_ssl
            )
            
            elapsed_ms = response.elapsed.total_seconds() * 1000
            
            try:
                data = response.json()
            except ValueError:
                data = response.text
            
            success = 200 <= response.status_code < 300
            
            return WebhookResponse(
                status_code=response.status_code,
                success=success,
                data=data,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                error=None if success else f"HTTP {response.status_code}"
            )
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"n8n workflow trigger failed: {workflow_id}")
            raise N8nError(f"Request failed: {str(e)}")
    
    def get_execution_status(self, execution_id: str) -> WebhookResponse:
        """
        Get the status of a workflow execution.
        
        Args:
            execution_id: The execution ID to check
            
        Returns:
            WebhookResponse with execution status
        """
        if not self.api_key:
            raise N8nError("API key required for checking execution status")
        
        url = f"{self.base_url}/api/v1/executions/{execution_id}"
        
        headers = {
            "Accept": "application/json",
            "X-N8N-API-KEY": self.api_key
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            elapsed_ms = response.elapsed.total_seconds() * 1000
            
            try:
                data = response.json()
            except ValueError:
                data = response.text
            
            success = 200 <= response.status_code < 300
            
            return WebhookResponse(
                status_code=response.status_code,
                success=success,
                data=data,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                error=None if success else f"HTTP {response.status_code}"
            )
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"n8n execution status check failed: {execution_id}")
            raise N8nError(f"Request failed: {str(e)}")


# -----------------------------------------------------------------------------
# Module-level convenience functions
# -----------------------------------------------------------------------------

_default_service: Optional[N8nService] = None


def get_n8n_service(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> N8nService:
    """
    Get or create an N8nService instance.
    
    Args:
        base_url: Optional base URL. If provided, creates a new instance.
        api_key: Optional API key.
        
    Returns:
        N8nService instance
    """
    global _default_service
    
    if base_url or api_key:
        return N8nService(base_url=base_url, api_key=api_key)
    
    if _default_service is None:
        _default_service = N8nService()
    
    return _default_service


def call_n8n_webhook(
    webhook_path: str,
    payload: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    query_params: Optional[Dict[str, str]] = None,
    raise_on_error: bool = False
) -> WebhookResponse:
    """
    Convenience function to call an n8n webhook.
    
    Args:
        webhook_path: Webhook path/ID
        payload: JSON payload to send
        method: HTTP method (default POST)
        query_params: Optional query parameters
        raise_on_error: If True, raise on non-2xx response
        
    Returns:
        WebhookResponse object
    """
    service = get_n8n_service()
    return service.call_webhook(
        webhook_path=webhook_path,
        payload=payload,
        method=method,
        query_params=query_params,
        raise_on_error=raise_on_error
    )


def trigger_n8n_workflow(
    workflow_id: str,
    payload: Optional[Dict[str, Any]] = None,
    wait: bool = False
) -> WebhookResponse:
    """
    Convenience function to trigger an n8n workflow.
    
    Args:
        workflow_id: Workflow ID to trigger
        payload: Data to pass to the workflow
        wait: Wait for completion
        
    Returns:
        WebhookResponse object
    """
    service = get_n8n_service()
    return service.trigger_workflow(
        workflow_id=workflow_id,
        payload=payload,
        wait_for_completion=wait
    )
