from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from chainlit.context import context
from chainlit.step import Step
from chainlit.sync import run_sync
from haystack.agents import Agent, Tool
from haystack.agents.agent_step import AgentStep

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def __len__(self):
        return len(self.items)

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

    def peek(self) -> T:
        return self.items[-1]

    def clear(self) -> None:
        self.items.clear()


class HaystackAgentCallbackHandler:
    stack: Stack[Step]
    last_step: Optional[Step]

    def __init__(self, agent: Agent):
        agent.callback_manager.on_agent_start += self.on_agent_start
        agent.callback_manager.on_agent_step += self.on_agent_step
        agent.callback_manager.on_agent_finish += self.on_agent_finish
        agent.callback_manager.on_new_token += self.on_new_token

        agent.tm.callback_manager.on_tool_start += self.on_tool_start
        agent.tm.callback_manager.on_tool_finish += self.on_tool_finish
        agent.tm.callback_manager.on_tool_error += self.on_tool_error

    def on_agent_start(self, **kwargs: Any) -> None:
        # Prepare agent step message for streaming
        self.agent_name = kwargs.get("name", "Agent")
        self.stack = Stack[Step]()
        root_message = context.session.root_message
        parent_id = root_message.id if root_message else None
        run_step = Step(name=self.agent_name, type="run", parent_id=parent_id)
        run_step.start = datetime.utcnow().isoformat()
        run_step.input = kwargs

        run_sync(run_step.send())

        self.stack.push(run_step)

    def on_agent_finish(self, agent_step: AgentStep, **kwargs: Any) -> None:
        run_step = self.stack.pop()
        run_step.end = datetime.utcnow().isoformat()
        run_step.output = agent_step.prompt_node_response
        run_sync(run_step.update())

    # This method is called when a step has finished
    def on_agent_step(self, agent_step: AgentStep, **kwargs: Any) -> None:
        # Send previous agent step message
        self.last_step = self.stack.pop()

        # If token streaming is disabled
        if self.last_step.output == "":
            self.last_step.output = agent_step.prompt_node_response
        self.last_step.end = datetime.utcnow().isoformat()
        run_sync(self.last_step.update())

        if not agent_step.is_last():
            # Prepare step for next agent step
            step = Step(name=self.agent_name, parent_id=self.stack.peek().id)
            self.stack.push(step)

    def on_new_token(self, token, **kwargs: Any) -> None:
        # Stream agent step tokens
        run_sync(self.stack.peek().stream_token(token))

    def on_tool_start(self, tool_input: str, tool: Tool, **kwargs: Any) -> None:
        # Tool started, create step
        parent_id = self.stack.items[0].id if self.stack.items[0] else None
        tool_step = Step(name=tool.name, type="tool", parent_id=parent_id)
        tool_step.input = tool_input
        tool_step.start = datetime.utcnow().isoformat()
        self.stack.push(tool_step)

    def on_tool_finish(
        self,
        tool_result: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        # Tool finished, send step with tool_result
        tool_step = self.stack.pop()
        tool_step.output = tool_result
        tool_step.end = datetime.utcnow().isoformat()
        run_sync(tool_step.update())

    def on_tool_error(self, exception: Exception, tool: Tool, **kwargs: Any) -> None:
        # Tool error, send error message
        error_step = self.stack.pop()
        error_step.is_error = True
        error_step.output = str(exception)
        error_step.end = datetime.utcnow().isoformat()
        run_sync(error_step.update())
