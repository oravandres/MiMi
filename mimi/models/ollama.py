"""Ollama model integration for MiMi."""

import json
import requests
from typing import Any, Dict, List, Optional, Union

from mimi.utils.logger import logger


class OllamaModelError(Exception):
    """Exception raised when there's an error with the Ollama model."""

    pass


class OllamaClient:
    """Client for interacting with Ollama models."""

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        timeout: int = 120,
        suppress_log: bool = False,
        stream: bool = False,
    ) -> None:
        """Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use.
            base_url: Base URL for the Ollama API.
            temperature: Sampling temperature (0-1).
            timeout: Timeout in seconds for requests.
            suppress_log: Whether to suppress the initialization log.
            stream: Whether to use streaming mode with the API.
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self.stream = stream
        
        if not suppress_log:
            logger.info(f"Initialized Ollama client for model: {model_name}")

    def generate(
        self, 
        prompt: str, 
        system_prompt: str,
        max_tokens: Optional[int] = 8192,
    ) -> str:
        """Generate a response from the model.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            max_tokens: Maximum tokens to generate.
            
        Returns:
            The generated text response.
            
        Raises:
            OllamaModelError: If the model generation fails.
        """
        try:
            logger.debug(f"Sending request to Ollama API for model {self.model_name}")
            
            # Always use the generate endpoint
            request_url = f"{self.base_url}/api/generate"
                
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False,  # Always set to false for now to avoid streaming complexity
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
                
            if max_tokens:
                request_data["max_tokens"] = max_tokens
            
            logger.debug(f"Ollama request data: {json.dumps(request_data)[:200]}...")
            logger.debug(f"Using API endpoint: {request_url}")
            
            response = requests.post(
                request_url,
                json=request_data,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise OllamaModelError(error_msg)
            
            # Debug: Log raw response content length and sample
            content_length = len(response.text)
            logger.debug(f"Ollama API response: length={content_length}, sample={response.text[:100]}...")
            
            # Try to parse as single JSON response
            try:
                result = response.json()
                logger.debug("Successfully parsed response as single JSON object")
                return result.get("response", "")
            except json.JSONDecodeError as json_err:
                # Enhanced error logging with detailed response inspection
                logger.error(f"JSON decode error: {str(json_err)}")
                logger.error(f"Response content type: {type(response.text)}")
                logger.error(f"First 100 chars of response: {response.text[:100]}")
                logger.error(f"Last 100 chars of response: {response.text[-100:] if len(response.text) > 100 else response.text}")
                
                # Check if this is a streaming response with multiple JSON objects
                if '\n' in response.text:
                    logger.info("Response contains multiple lines, attempting to parse as streaming response")
                    full_response = ""
                    json_lines = [line for line in response.text.strip().split('\n') if line.strip()]
                    
                    for line in json_lines:
                        try:
                            line_obj = json.loads(line)
                            if "response" in line_obj:
                                full_response += line_obj["response"]
                        except:
                            # Skip failed lines
                            pass
                    
                    if full_response:
                        logger.info("Successfully extracted text from streaming response")
                        return full_response
                
                # If all parsing attempts fail, return the raw text as fallback
                logger.warning("Returning raw text from response as fallback")
                return response.text
                
        except Exception as e:
            logger.error(f"Error generating from Ollama model {self.model_name}: {str(e)}")
            raise OllamaModelError(f"Error generating from model: {str(e)}") from e


def get_ollama_client(
    model_name: str,
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    suppress_log: bool = False,
    stream: bool = False,
) -> OllamaClient:
    """Get an Ollama client for the specified model.
    
    Args:
        model_name: Name of the Ollama model.
        base_url: Base URL for the Ollama API.
        temperature: Sampling temperature (0-1).
        suppress_log: Whether to suppress the initialization log.
        stream: Whether to use streaming mode with the API.
        
    Returns:
        An initialized OllamaClient.
    """
    return OllamaClient(
        model_name=model_name,
        base_url=base_url,
        temperature=temperature,
        suppress_log=suppress_log,
        stream=stream,
    ) 