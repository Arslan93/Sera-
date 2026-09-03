
import logging
import json
from typing import Iterator, List, Optional, Any, Callable
from models.message import Message
from memory.memory_store import MemoryStore, memory_store
from core.llm_client import LLMProvider, get_llm_client
from tools.tool_registry import tool_registry as default_tool_registry

logger = logging.getLogger(__name__)

MAX_DEBUG_ITERATIONS = 4

class Orchestrator:
    """
    The central brain of the application.
    """
    def __init__(self, llm_client: LLMProvider, memory: MemoryStore, tool_registry: Optional[Any] = None, system_prompt: str = ""):
        """
        Initializes the Orchestrator.
        """
        self.llm_client = llm_client
        self.memory = memory
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.session_id: int = self.memory.create_session()
        logger.info(f"Orchestrator initialized for session {self.session_id}")

    def handle_user_message(self, user_message: str, on_tool_call: Optional[Callable[[str, dict], None]] = None) -> Iterator[str]:
        """
        Handles a user message, generates a response, and saves the conversation.
        """
        # 1. Save user message
        self.memory.save_message(Message(session_id=self.session_id, role="user", content=user_message))

        tool_schemas = self.tool_registry.get_tool_schemas() if self.tool_registry else None

        if tool_schemas:
            step = 0
            while step < MAX_DEBUG_ITERATIONS:
                step += 1
                # Retrieve current conversation history (including past tool results)
                history = self.memory.get_conversation_history(self.session_id)
                llm_messages = self._prepare_llm_messages(history, include_tool_results=True)

                # Generate response from LLM with tools
                response = self.llm_client.generate_response(llm_messages, tools=tool_schemas, stream=False)
                response_message = response.choices[0].message

                # Check for tool calls
                if response_message.tool_calls:
                    logger.info(f"[Orchestrator Step {step}/{MAX_DEBUG_ITERATIONS}] LLM requested {len(response_message.tool_calls)} tool call(s)")
                    self.memory.save_message(
                        Message(
                            session_id=self.session_id,
                            role=response_message.role,
                            content=response_message.content or "",
                            tool_calls=response_message.tool_calls
                        )
                    )
                    # Execute tools and save results with post-mortem logging
                    self._execute_tool_calls(response_message.tool_calls, step=step, on_tool_call=on_tool_call)
                    # Continue loop to let LLM process tool result and decide next step
                    continue

                # No tool calls: Assistant generated final text response
                final_content = response_message.content or "Action completed."
                self.memory.save_message(Message(session_id=self.session_id, role="assistant", content=final_content))
                yield final_content
                return

            # Safety cap reached
            cap_fallback = (
                f"⚠️ **Self-Debug Limit Reached ({MAX_DEBUG_ITERATIONS} iterations)**: "
                "I attempted to resolve the task and fix execution issues autonomously, but encountered persistent errors. "
                "Please review the latest error output or provide guidance on how to proceed."
            )
            logger.warning(f"Self-debug safety cap ({MAX_DEBUG_ITERATIONS}) reached for session {self.session_id}.")
            self.memory.save_message(Message(session_id=self.session_id, role="assistant", content=cap_fallback))
            yield cap_fallback
            return

        # Direct streaming for text-only chat when no tools
        history = self.memory.get_conversation_history(self.session_id)
        llm_messages = self._prepare_llm_messages(history, include_tool_results=True)
        response_stream = self.llm_client.generate_response(llm_messages, tools=None, stream=True)
        yield from self._stream_and_save_assistant_response(response_stream)

    def _stream_and_save_assistant_response(self, response_iterator: Iterator) -> Iterator[str]:
        """Streams response chunks to the caller and saves the full message."""
        assistant_response = ""
        for chunk in response_iterator:
            delta = chunk.choices[0].delta if chunk.choices else None
            content = delta.content if delta and hasattr(delta, "content") else None
            if content:
                assistant_response += content
                yield content
        
        self.memory.save_message(Message(session_id=self.session_id, role="assistant", content=assistant_response))
        logger.info("Successfully handled user message and saved conversation.")

    def _execute_tool_calls(self, tool_calls: List, step: int = 1, on_tool_call: Optional[Callable[[str, dict], None]] = None):
        """Executes tool calls and records results with post-mortem logging."""
        if not self.tool_registry:
            return
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            if on_tool_call:
                try:
                    on_tool_call(tool_name, tool_args)
                except Exception as e:
                    logger.debug(f"on_tool_call error: {e}")
            logger.info(f"[Debug/Step {step}] Executing tool '{tool_name}' with args: {tool_args}")
            result = self.tool_registry.execute_tool(tool_name, **tool_args)
            
            # Post-mortem log preview
            result_str = str(result)
            preview = result_str[:250] + "..." if len(result_str) > 250 else result_str
            logger.info(f"[Debug/Step {step}] Tool '{tool_name}' output: {preview}")

            # Save tool result as a message
            self.memory.save_message(Message(session_id=self.session_id, role="tool", content=result_str, tool_call_id=tool_call.id, name=tool_name))

    def _prepare_llm_messages(self, history: List[Message], include_tool_results: bool = False) -> List[dict]:
        """
        Prepares the list of messages to be sent to the LLM.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in history:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.role == "assistant" and msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id if hasattr(tc, 'id') else tc.get('id'),
                        "type": tc.type if hasattr(tc, 'type') else tc.get('type', 'function'),
                        "function": {
                            "name": tc.function.name if hasattr(tc, 'function') else tc.get('function', {}).get('name'),
                            "arguments": tc.function.arguments if hasattr(tc, 'function') else tc.get('function', {}).get('arguments')
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.role == "tool" and include_tool_results:
                message_dict["tool_call_id"] = msg.tool_call_id
                message_dict["name"] = msg.name
            
            messages.append(message_dict)
        return messages

    def new_session(self):
        """
        Starts a new conversation session.
        """
        self.session_id = self.memory.create_session()
        logger.info(f"Started new session: {self.session_id}")
        
def load_system_prompt():
    try:
        with open("prompts/system_prompt.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("system_prompt.txt not found. Using default prompt.")
        return "You are SERA, a fast and helpful personal AI desktop assistant."

def get_orchestrator(tool_registry: Optional[Any] = None) -> Orchestrator:
    """
    Factory function to create an Orchestrator instance.
    """
    llm_client = get_llm_client()
    system_prompt = load_system_prompt()
    actual_registry = tool_registry if tool_registry is not None else default_tool_registry
    return Orchestrator(llm_client=llm_client, memory=memory_store, tool_registry=actual_registry, system_prompt=system_prompt)
