"""Ollama model integration for MiMi."""

import json
import os
import requests
import time
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
        timeout: int = 300,  # Increased from 120 to 300 seconds
        suppress_log: bool = False,
        stream: bool = False,
        max_retries: int = 3,
        retry_delay: int = 5,
    ) -> None:
        """Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use.
            base_url: Base URL for the Ollama API.
            temperature: Sampling temperature (0-1).
            timeout: Timeout in seconds for requests.
            suppress_log: Whether to suppress the initialization log.
            stream: Whether to use streaming mode with the API.
            max_retries: Maximum number of retries for failed requests.
            retry_delay: Delay in seconds between retries.
        """
        # Check environment variables for configuration, prioritize env vars over parameters
        self.model_name = model_name
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url)
        self.temperature = float(os.environ.get("OLLAMA_TEMPERATURE", temperature))
        self.timeout = int(os.environ.get("OLLAMA_TIMEOUT", timeout))
        self.stream = os.environ.get("OLLAMA_STREAM", str(stream)).lower() == "true"
        self.max_retries = int(os.environ.get("OLLAMA_MAX_RETRIES", max_retries))
        self.retry_delay = int(os.environ.get("OLLAMA_RETRY_DELAY", retry_delay))
        
        if not suppress_log:
            logger.info(f"Initialized Ollama client for model: {model_name} (timeout: {self.timeout}s, max_retries: {self.max_retries})")
            # If environment variables were used, log that
            if self.base_url != base_url:
                logger.info(f"Using OLLAMA_BASE_URL from environment: {self.base_url}")
            if self.timeout != timeout:
                logger.info(f"Using OLLAMA_TIMEOUT from environment: {self.timeout}")
            if self.max_retries != max_retries:
                logger.info(f"Using OLLAMA_MAX_RETRIES from environment: {self.max_retries}")

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
            OllamaModelError: If the model generation fails after all retries.
        """
        # First check if Ollama server is running
        try:
            self.initialize_connection()
        except OllamaModelError as e:
            # Rethrow with more context
            raise OllamaModelError(f"Cannot generate response: {str(e)}")
        
        retries = 0
        last_exception = None
        
        while retries <= self.max_retries:
            try:
                if retries > 0:
                    logger.warning(f"Retry {retries}/{self.max_retries} for Ollama API request")
                    # Increase timeout for retries
                    current_timeout = self.timeout * (1 + retries * 0.5)  # Increase timeout by 50% each retry
                    logger.debug(f"Using increased timeout of {current_timeout}s for retry")
                else:
                    current_timeout = self.timeout
                
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
                logger.debug(f"Request timeout set to {current_timeout} seconds")
                
                response = requests.post(
                    request_url,
                    json=request_data,
                    timeout=current_timeout,
                )
                
                if response.status_code != 200:
                    error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    # Only retry on 5xx errors (server errors) or specific timeout errors
                    if response.status_code >= 500 or response.status_code == 408:
                        last_exception = OllamaModelError(error_msg)
                        retries += 1
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        # Don't retry on client errors (4xx) except timeout (408)
                        raise OllamaModelError(error_msg)
                
                content_length = len(response.text)
                logger.debug(f"Ollama API response: {response.text[:50]}")
                
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
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # These are the most likely exceptions to be resolved by retrying
                logger.warning(f"Request error (attempt {retries+1}/{self.max_retries+1}): {str(e)}")
                last_exception = e
                retries += 1
                
                if retries <= self.max_retries:
                    # Wait longer between each retry
                    retry_wait = self.retry_delay * retries
                    logger.info(f"Waiting {retry_wait} seconds before retry...")
                    time.sleep(retry_wait)
                else:
                    logger.error(f"Maximum retries ({self.max_retries}) exceeded. Giving up.")
                    break
                    
            except Exception as e:
                # For other exceptions, only retry a limited number of times
                logger.error(f"Error generating from Ollama model {self.model_name}: {str(e)}")
                last_exception = e
                
                # Only retry on specific exceptions that might be transient
                if isinstance(e, (requests.exceptions.RequestException, ConnectionError)):
                    retries += 1
                    if retries <= self.max_retries:
                        time.sleep(self.retry_delay * retries)
                        continue
                
                # For other exceptions, don't retry
                raise OllamaModelError(f"Error generating from model: {str(e)}") from e
        
        # If we've exhausted all retries, raise the last exception
        if last_exception:
            raise OllamaModelError(f"Error generating from model after {self.max_retries} retries: {str(last_exception)}") from last_exception
        
        # This should never happen as we either return a result or raise an exception
        return ""

    def health_check(self) -> bool:
        """Check if the Ollama server is running.
        
        Returns:
            True if the server is running, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama server health check failed: {str(e)}")
            return False

    def initialize_connection(self) -> None:
        """Initialize connection to Ollama server or raise an error.
        
        Raises:
            OllamaModelError: If server not running or configured properly.
        """
        if not self.health_check():
            error_msg = f"Ollama server not running at {self.base_url}. Is the Ollama server started?"
            logger.error(error_msg)
            
            # Provide helpful message for common setup issues
            if self.base_url == "http://localhost:11434":
                logger.error("To start Ollama locally, run: ollama serve")
                logger.error("Make sure you have installed Ollama: https://ollama.com/download")
            elif ":" not in self.base_url:
                logger.error(f"Invalid Ollama URL: {self.base_url} - URL should include port number")
            
            raise OllamaModelError(error_msg)


def get_ollama_client(
    model_name: str,
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    timeout: int = 800,  # Increased from default 120 to 300
    suppress_log: bool = False,
    stream: bool = False,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> OllamaClient:
    """Get an Ollama client for the specified model.
    
    Args:
        model_name: Name of the Ollama model.
        base_url: Base URL for the Ollama API.
        temperature: Sampling temperature (0-1).
        timeout: Timeout in seconds for requests.
        suppress_log: Whether to suppress the initialization log.
        stream: Whether to use streaming mode with the API.
        max_retries: Maximum number of retries for failed requests.
        retry_delay: Delay in seconds between retries.
        
    Returns:
        An initialized OllamaClient.
    """
    return OllamaClient(
        model_name=model_name,
        base_url=base_url,
        temperature=temperature,
        timeout=timeout,
        suppress_log=suppress_log,
        stream=stream,
        max_retries=max_retries,
        retry_delay=retry_delay,
    ) 