from typing import List, Callable, Literal, Dict, Any, Optional, TypeVar
import dspy

# Define a type for the handler function
F = TypeVar('F', bound=Callable[..., Any])

class IntentResult:
    """Class to hold intent classification results."""
    def __init__(self, category: str, confidence: float):
        self.category = category
        self.confidence = confidence

def build_intent_classifier(intents: List[str]) -> Callable[[str], IntentResult]:
    """
    Build an intent classifier using DSPy that returns an IntentResult object.
    
    Args:
        intents: List of possible intent categories
        
    Returns:
        A callable that takes a message string and returns an IntentResult
    """
    if not intents:
        raise ValueError("Intent list cannot be empty")
    
    class Categorize(dspy.Signature):
        """Categorize user intent."""
        message: str = dspy.InputField()
        category: Literal[tuple(intents)] = dspy.OutputField()  # Use tuple unpacking for Literal
        confidence: float = dspy.OutputField()
    
    predict_func = dspy.ChainOfThought(Categorize)
    
    def classify(message: str) -> IntentResult:
        try:
            result = predict_func(message=message)
            return IntentResult(result.category, result.confidence)
        except Exception as e:
            # Fallback to a default intent or raise a custom exception
            raise IntentClassificationError(f"Failed to classify intent: {str(e)}") from e
    
    return classify

class IntentClassificationError(Exception):
    """Exception raised for errors in the intent classification process."""
    pass

class RouteNotFoundError(Exception):
    """Exception raised when no matching route is found."""
    pass

class Router:
    """
    A router class that dispatches messages to handler functions based on intent classification.
    """
    def __init__(self, confidence_threshold: float = 0.7, default_handler: Optional[Callable] = None):
        """
        Initialize the router.
        
        Args:
            confidence_threshold: Minimum confidence required to accept an intent classification
            default_handler: Handler to call when no intent matches or confidence is too low
        """
        self.routes: Dict[str, Callable] = {}
        self.intent_classifier: Optional[Callable[[str], IntentResult]] = None
        self.confidence_threshold = confidence_threshold
        self.default_handler = default_handler

    def route(self, path: str) -> Callable[[F], F]:
        """
        Decorator that registers a function with a path pattern.
        
        Args:
            path: The intent path/category to match
            
        Returns:
            A decorator function
        """
        def decorator(func: F) -> F:
            if not path:
                raise ValueError("Route path cannot be empty")
                
            if path in self.routes:
                raise ValueError(f"Route '{path}' is already registered")
                
            self.routes[path] = func
            # Rebuild classifier with updated routes
            self._rebuild_classifier()
            return func
        return decorator

    def _rebuild_classifier(self) -> None:
        """Rebuild the intent classifier with the current routes."""
        if self.routes:
            self.intent_classifier = build_intent_classifier(list(self.routes.keys()))

    def dispatch(self, message: str, *args: Any, **kwargs: Any) -> Any:
        """
        Dispatch to the appropriate handler based on classified intent.
        
        Args:
            message: The user message to classify
            *args: Additional positional arguments to pass to the handler
            **kwargs: Additional keyword arguments to pass to the handler
            
        Returns:
            The result of the handler function
            
        Raises:
            RouteNotFoundError: If no matching route is found and no default handler exists
            IntentClassificationError: If intent classification fails
        """
        if not self.intent_classifier:
            raise ValueError("No routes have been registered, cannot dispatch")
            
        try:
            intent_result = self.intent_classifier(message)
            print(f"Classified intent: {intent_result.category} (confidence: {intent_result.confidence:.2f})")
            
            # Check if we have a matching route with sufficient confidence
            if (intent_result.category in self.routes and 
                intent_result.confidence >= self.confidence_threshold):
                handler = self.routes[intent_result.category]
                return handler(message, *args, **kwargs)
                
            # Fall back to default handler if available
            if self.default_handler:
                return self.default_handler(message, intent_result, *args, **kwargs)
                
            raise RouteNotFoundError(
                f"No matching route found for intent '{intent_result.category}' "
                f"(confidence: {intent_result.confidence:.2f})"
            )

        except Exception as e:
            # Handle unexpected errors
            raise

    def get_registered_intents(self) -> List[str]:
        """Get a list of all registered intent paths."""
        return list(self.routes.keys())