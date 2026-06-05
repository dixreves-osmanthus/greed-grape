"""
Mistral API Client Module

Handles communication with the Mistral API for LaTeX transcription.
Supports both the Mistral API and compatible endpoints.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class MistralResponse:
    """Represents a response from the Mistral API."""
    content: str
    model: str
    finish_reason: str
    usage: Dict[str, int]
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessage:
    """Represents a message in a chat conversation."""
    role: str  # "user", "assistant", "system"
    content: str


class MistralClient:
    """
    Client for interacting with the Mistral API.
    
    Supports:
    - Mistral's official API (api.mistral.ai)
    - Compatible endpoints (LocalAI, etc.)
    - Automatic retry with exponential backoff
    - Streaming responses
    - Conversation history management
    """
    
    API_BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-large-latest"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3
    ):
        """
        Initialize the Mistral client.
        
        Args:
            api_key: Mistral API key
            base_url: Custom API base URL (default: Mistral official API)
            model: Model to use (default: mistral-large-latest)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url or self.API_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize HTTP client
        self._client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Mistral API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self._client.request(
                method,
                url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        stream: bool = False
    ) -> MistralResponse:
        """
        Get a chat completion from the Mistral API.
        
        Args:
            messages: List of chat messages
            model: Model to use (overrides default)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter (0-1)
            stream: Whether to stream the response
            
        Returns:
            MistralResponse object
        """
        endpoint = "/chat/completions"
        
        payload = {
            "model": model or self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if stream:
            payload["stream"] = True
        
        response_data = self._make_request("POST", endpoint, data=payload)
        
        # Parse response
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices in response")
        
        choice = choices[0]
        message = choice.get("message", {})
        
        return MistralResponse(
            content=message.get("content", ""),
            model=response_data.get("model", self.model),
            finish_reason=choice.get("finish_reason", "unknown"),
            usage=response_data.get("usage", {}),
            raw_response=response_data
        )
    
    def completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None
    ) -> MistralResponse:
        """
        Get a text completion from the Mistral API.
        
        Args:
            prompt: The prompt text
            model: Model to use (overrides default)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter (0-1)
            stop: Stop sequences
            
        Returns:
            MistralResponse object
        """
        endpoint = "/completions"
        
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if stop:
            payload["stop"] = stop
        
        response_data = self._make_request("POST", endpoint, data=payload)
        
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices in response")
        
        choice = choices[0]
        
        return MistralResponse(
            content=choice.get("text", ""),
            model=response_data.get("model", self.model),
            finish_reason=choice.get("finish_reason", "unknown"),
            usage=response_data.get("usage", {}),
            raw_response=response_data
        )
    
    def transcribe_to_latex(
        self,
        text: str,
        context: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Transcribe text containing mathematical expressions to LaTeX.
        
        Uses a specialized prompt to guide the model in producing
        accurate LaTeX output.
        
        Args:
            text: Text containing mathematical expressions
            context: Additional context about the document
            temperature: Sampling temperature (lower for more deterministic)
            
        Returns:
            LaTeX transcription
        """
        system_prompt = """You are an expert LaTeX transcriber. Your task is to convert mathematical expressions and equations from plain text or PDF-extracted text into proper LaTeX code.

Guidelines:
1. Use appropriate LaTeX environments: $...$ for inline math, \\[...\\] or equation* for display math
2. Use proper LaTeX commands: \\frac, \\sqrt, \\sum, \\int, \\lim, etc.
3. Use Greek letters: \\alpha, \\beta, \\gamma, \\delta, etc.
4. Use proper spacing and formatting
5. Preserve the mathematical meaning and structure
6. For multi-line equations, use align*, gather*, or multline* environments
7. Use \\text{} for text within math mode
8. Be precise and accurate

Examples:
- "x squared plus y squared equals z squared" -> $x^2 + y^2 = z^2$
- "the integral from a to b of f(x) dx" -> $\\int_a^b f(x) \\, dx$
- "the sum from i=1 to n of i squared" -> $\\sum_{i=1}^n i^2$
- "alpha plus beta equals gamma" -> $\\alpha + \\beta = \\gamma$

Always respond with only the LaTeX code, without any additional text or explanations."""

        user_prompt = f"Convert the following mathematical text to LaTeX:\n\n{text}"
        
        if context:
            user_prompt += f"\n\nContext: {context}"
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        return response.content
    
    def transcribe_page_to_latex(
        self,
        page_text: str,
        page_number: int = 1,
        total_pages: int = 1,
        temperature: float = 0.3
    ) -> str:
        """
        Transcribe a single PDF page to LaTeX.
        
        Args:
            page_text: Text content of the page
            page_number: Current page number
            total_pages: Total number of pages
            temperature: Sampling temperature
            
        Returns:
            LaTeX transcription of the page
        """
        system_prompt = f"""You are an expert LaTeX document transcriber. Convert the following PDF page content to proper LaTeX code.

The document has {total_pages} pages total, and this is page {page_number}.

Guidelines:
1. Preserve the document structure (sections, subsections, paragraphs)
2. Convert all mathematical expressions to proper LaTeX math mode
3. Use appropriate LaTeX environments and commands
4. Maintain the original meaning and formatting as much as possible
5. Use \\section{{}}, \\subsection{{}}, etc. for headings
6. Use \\begin{{itemize}}...\\end{{itemize}} for bullet lists
7. Use \\begin{{enumerate}}...\\end{{enumerate}} for numbered lists
8. Use \\begin{{equation}}...\\end{{equation}} for numbered equations
9. Use \\[...\\] for unnumbered display equations
10. Use $...$ for inline mathematical expressions

Always respond with only the LaTeX code, without any additional text or explanations."""

        user_prompt = f"Convert the following PDF page to LaTeX:\n\n{page_text}"
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=4000
        )
        
        return response.content
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from the Mistral API.
        
        Returns:
            List of model information dictionaries
        """
        endpoint = "/models"
        response_data = self._make_request("GET", endpoint)
        return response_data.get("data", [])
    
    def check_health(self) -> bool:
        """
        Check if the API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            self.list_models()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
