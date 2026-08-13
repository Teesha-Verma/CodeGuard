import time
import random
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RetryEngine:
    """Engine for executing functions with exponential backoff and jitter."""
    
    def execute_with_retry(
        self, 
        func: Callable, 
        *args: Any, 
        max_retries: int = 3, 
        retry_delay: float = 1.0, 
        **kwargs: Any
    ) -> Any:
        """
        Execute a function with retry logic for transient errors.
        
        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            max_retries: Maximum number of times to retry.
            retry_delay: Base delay between retries in seconds.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The result of the function call.
            
        Raises:
            Exception: The last exception encountered if all retries fail.
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                is_transient = self._is_transient_error(e)
                
                if not is_transient or attempt == max_retries:
                    if attempt == max_retries:
                        logger.error(f"Execution failed after {attempt} retries: {str(e)}")
                    else:
                        logger.error(f"Non-transient error encountered: {str(e)}")
                    raise e
                    
                # Exponential backoff with jitter
                sleep_time = retry_delay * (2 ** attempt)
                jitter = random.uniform(0, 0.1 * sleep_time)
                total_sleep = sleep_time + jitter
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {total_sleep:.2f} seconds..."
                )
                time.sleep(total_sleep)
                
        raise last_exception if last_exception else Exception("Unknown error during execution")
        
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient and should be retried.
        
        Args:
            error: The exception to check.
            
        Returns:
            True if the error is transient, False otherwise.
        """
        error_str = str(error).lower()
        
        # Checking for common transient errors
        # 429: Too Many Requests (Rate Limit)
        if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
            return True
            
        # Timeouts
        if "timeout" in error_str:
            return True
            
        # Connection Errors
        if "connection" in error_str or "network" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
            return True
            
        return False
