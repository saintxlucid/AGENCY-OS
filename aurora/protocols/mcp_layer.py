"""
MCP/A2A Protocol Layer
Enables communication with external tools via Model Context Protocol
and Agent-to-Agent protocol for multi-agent coordination.
"""
from __future__ import annotations

import os
import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import httpx
import websockets


class ProtocolType(Enum):
    MCP = "mcp"
    A2A = "a2a"
    CUSTOM = "custom"


@dataclass
class MCPServer:
    """MCP Server configuration."""
    server_id: str
    name: str
    transport: str  # stdio, http, websocket
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    status: str = "disconnected"
    tools: List[Dict] = field(default_factory=list)
    resources: List[Dict] = field(default_factory=list)
    prompts: List[Dict] = field(default_factory=list)


@dataclass
class A2AAgent:
    """A2A Agent Card."""
    agent_id: str
    name: str
    description: str
    url: str
    version: str
    capabilities: List[str]
    skills: List[Dict] = field(default_factory=list)
    authentication: Optional[Dict] = None


@dataclass
class ProtocolMessage:
    """Unified protocol message."""
    message_id: str
    protocol: ProtocolType
    source: str
    target: str
    method: str
    params: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MCPLayer:
    """
    MCP (Model Context Protocol) Client Layer.
    
    Connects to MCP servers for tool access, resource reading,
    and prompt templates. Also supports A2A for agent coordination.
    """
    
    def __init__(self, aurora_core):
        self.core = aurora_core
        self.servers: Dict[str, MCPServer] = {}
        self.a2a_agents: Dict[str, A2AAgent] = {}
        self.connections: Dict[str, Any] = {}
        self.tool_registry: Dict[str, Callable] = {}
        self._server_processes: Dict[str, asyncio.subprocess.Process] = {}
    
    async def initialize(self):
        """Initialize protocol layer from config."""
        config_path = Path(".mcp.json")
        if config_path.exists():
            await self._load_config(config_path)
        
        # Connect to configured servers
        for server_id, server in self.servers.items():
            if server.status != "disabled":
                await self.connect_server(server_id)
    
    async def _load_config(self, config_path: Path):
        """Load MCP configuration."""
        with open(config_path) as f:
            config = json.load(f)
        
        for name, server_config in config.get("mcpServers", {}).items():
            server_id = name
            server = MCPServer(
                server_id=server_id,
                name=name,
                transport=server_config.get("transport", "stdio"),
                command=server_config.get("command"),
                args=server_config.get("args"),
                url=server_config.get("url"),
                env=server_config.get("env", {}),
            )
            self.servers[server_id] = server
    
    async def connect_server(self, server_id: str) -> bool:
        """Connect to an MCP server."""
        if server_id not in self.servers:
            return False
        
        server = self.servers[server_id]
        
        try:
            if server.transport == "stdio":
                await self._connect_stdio(server)
            elif server.transport == "http":
                await self._connect_http(server)
            elif server.transport == "websocket":
                await self._connect_websocket(server)
            
            # Fetch capabilities
            await self._fetch_capabilities(server_id)
            server.status = "connected"
            print(f"  🔗 Connected to MCP server: {server.name}")
            return True
            
        except Exception as e:
            server.status = f"error: {e}"
            print(f"  ❌ Failed to connect to {server.name}: {e}")
            return False
    
    async def _connect_stdio(self, server: MCPServer):
        """Connect via stdio transport."""
        if not server.command:
            raise ValueError("STDIO transport requires command")
        
        env = os.environ.copy()
        env.update(server.env)
        
        process = await asyncio.create_subprocess_exec(
            *server.command, *server.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        self._server_processes[server.server_id] = process
        self.connections[server.server_id] = {
            "type": "stdio",
            "process": process,
            "reader": process.stdout,
            "writer": process.stdin,
        }
        
        # Start reading responses
        asyncio.create_task(self._read_stdio_responses(server.server_id))
    
    async def _read_stdio_responses(self, server_id: str):
        """Read responses from stdio server."""
        conn = self.connections.get(server_id)
        if not conn:
            return
        
        reader = conn["reader"]
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                response = json.loads(line.decode())
                await self._handle_response(server_id, response)
            except Exception as e:
                print(f"STDIO read error: {e}")
                break
    
    async def _connect_http(self, server: MCPServer):
        """Connect via HTTP transport."""
        if not server.url:
            raise ValueError("HTTP transport requires URL")
        
        client = httpx.AsyncClient(base_url=server.url, timeout=30.0)
        self.connections[server.server_id] = {
            "type": "http",
            "client": client,
        }
    
    async def _connect_websocket(self, server: MCPServer):
        """Connect via WebSocket transport."""
        if not server.url:
            raise ValueError("WebSocket transport requires URL")
        
        ws = await websockets.connect(server.url)
        self.connections[server.server_id] = {
            "type": "websocket",
            "ws": ws,
        }
        asyncio.create_task(self._read_ws_responses(server.server_id))
    
    async def _read_ws_responses(self, server_id: str):
        """Read responses from WebSocket server."""
        conn = self.connections.get(server_id)
        if not conn:
            return
        
        ws = conn["ws"]
        try:
            async for message in ws:
                response = json.loads(message)
                await self._handle_response(server_id, response)
        except Exception as e:
            print(f"WebSocket read error: {e}")
    
    async def _fetch_capabilities(self, server_id: str):
        """Fetch tools, resources, prompts from server."""
        server = self.servers[server_id]
        
        # Initialize
        init_response = await self._send_request(server_id, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "aurora", "version": "1.0"}
        })
        
        if init_response:
            server.capabilities = init_response.get("capabilities", {})
        
        # List tools
        tools_response = await self._send_request(server_id, "tools/list", {})
        if tools_response:
            server.tools = tools_response.get("tools", [])
            for tool in server.tools:
                self.tool_registry[f"{server_id}:{tool['name']}"] = self._create_tool_wrapper(server_id, tool['name'])
        
        # List resources
        resources_response = await self._send_request(server_id, "resources/list", {})
        if resources_response:
            server.resources = resources_response.get("resources", [])
        
        # List prompts
        prompts_response = await self._send_request(server_id, "prompts/list", {})
        if prompts_response:
            server.prompts = prompts_response.get("prompts", [])
    
    def _create_tool_wrapper(self, server_id: str, tool_name: str) -> Callable:
        """Create a callable wrapper for an MCP tool."""
        async def tool_wrapper(**kwargs):
            return await self.call_tool(server_id, tool_name, kwargs)
        return tool_wrapper
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on an MCP server."""
        return await self._send_request(server_id, "tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
    
    async def read_resource(self, server_id: str, uri: str) -> Any:
        """Read a resource from an MCP server."""
        return await self._send_request(server_id, "resources/read", {"uri": uri})
    
    async def get_prompt(self, server_id: str, name: str, arguments: Dict) -> Any:
        """Get a prompt template from an MCP server."""
        return await self._send_request(server_id, "prompts/get", {
            "name": name,
            "arguments": arguments
        })
    
    async def _send_request(self, server_id: str, method: str, params: Dict) -> Any:
        """Send JSON-RPC request to server."""
        if server_id not in self.connections:
            raise ValueError(f"Not connected to server: {server_id}")
        
        conn = self.connections[server_id]
        request_id = str(uuid.uuid4())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        if conn["type"] == "stdio":
            writer = conn["writer"]
            writer.write((json.dumps(request) + "\n").encode())
            await writer.drain()
            # Response handled by _read_stdio_responses
            # For now, return placeholder
            return {"status": "sent", "request_id": request_id}
        
        elif conn["type"] == "http":
            client = conn["client"]
            response = await client.post("/", json=request)
            return response.json()
        
        elif conn["type"] == "websocket":
            ws = conn["ws"]
            await ws.send(json.dumps(request))
            # Response handled by _read_ws_responses
            return {"status": "sent", "request_id": request_id}
    
    async def _handle_response(self, server_id: str, response: Dict):
        """Handle incoming response."""
        # In production: correlate with pending requests
        print(f"  📨 Response from {server_id}: {response.get('method', 'result')}")
    
    # ─── A2A Support ───
    
    async def register_a2a_agent(self, agent: A2AAgent):
        """Register an A2A agent."""
        self.a2a_agents[agent.agent_id] = agent
        print(f"  🤝 Registered A2A agent: {agent.name}")
    
    async def discover_a2a_agents(self, registry_url: str) -> List[A2AAgent]:
        """Discover A2A agents from registry."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{registry_url}/agents")
            agents_data = response.json()
        
        agents = []
        for agent_data in agents_data:
            agent = A2AAgent(**agent_data)
            agents.append(agent)
            await self.register_a2a_agent(agent)
        
        return agents
    
    async def delegate_to_agent(self, agent_id: str, task: str, context: Dict) -> Any:
        """Delegate task to A2A agent."""
        if agent_id not in self.a2a_agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        agent = self.a2a_agents[agent_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{agent.url}/tasks",
                json={"task": task, "context": context},
                headers={"Authorization": f"Bearer {agent.authentication.get('token')}"} if agent.authentication else {}
            )
            return response.json()
    
    # ─── Tool Registry for Aurora ───
    
    def get_available_tools(self) -> List[Dict]:
        """Get all available tools from connected servers."""
        tools = []
        for server in self.servers.values():
            for tool in server.tools:
                tools.append({
                    "server_id": server.server_id,
                    "server_name": server.name,
                    **tool
                })
        return tools
    
    async def shutdown(self):
        """Shutdown all connections."""
        for server_id, process in self._server_processes.items():
            process.terminate()
            await process.wait()
        
        for conn in self.connections.values():
            if conn["type"] == "http":
                await conn["client"].aclose()
            elif conn["type"] == "websocket":
                await conn["ws"].close()
        
        print("🔌 Protocol layer shutdown complete")