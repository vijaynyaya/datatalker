from typing import Literal, Optional, Dict, List, Any, Union, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    THOUGHT = "thought"


class ResponseType(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "HTML"
    IMAGE = "image"
    JSON = "json"
    DATA = "data"
    VISUALIZATION = "visualization"
    STREAM = "stream"
    OBJECT = "object"

class ResourceMetadata(TypedDict):
    title: str
    url: str

class Resource(TypedDict):
    id: str
    long_text: str
    relevance_rationale: str
    metadatas: ResourceMetadata

@dataclass
class Message:
    role: MessageRole
    type: ResponseType
    content: Union[str, Dict[str, Any], bytes]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_thought(self) -> bool:
        """Check if this message is an internal thought"""
        return self.role == MessageRole.THOUGHT
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content if isinstance(self.content, str) else str(self.content),
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


Thought = lambda content: Message(role=MessageRole.THOUGHT, content=content)
SystemLog = lambda content: Message(role=MessageRole.SYSTEM, content=content)

@dataclass
class Context:
    """A mechanism for sharing variables across the workflow"""
    resources: Dict[str, Any] = field(default_factory=dict)
    dataframes: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    user_message: Message = field(default_factory=Message)
    history: List[Message] = field(default_factory=list)

    
    async def store_variable(self, key: str, value: Any) -> None:
        """Store a variable in the shared context"""
        self.variables[key] = value
        
    async def get_variable(self, key: str, default: Any = None) -> Any:
        """Retrieve a variable from context with optional default"""
        return self.variables.get(key, default)

    def add_message(self, msg: Message):
        self.history.append(msg)
        if msg.role == MessageRole.USER:
            self.user_message = msg
