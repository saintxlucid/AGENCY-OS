"""
MCP Server Manager for Design Studio
Start individual or all MCP servers for media/design workflows.
"""
import subprocess
import sys
import json
import os
from pathlib import Path

MCP_CONFIG_PATH = Path(__file__).parent.parent / ".mcp.json"


def load_config() -> dict:
    with open(MCP_CONFIG_PATH, "r") as f:
        return json.load(f)


def list_servers() -> list[str]:
    config = load_config()
    servers = config.get("mcpServers", {})
    print(f"\n📦 Available MCP Servers ({len(servers)}):\n")
    for name, cfg in servers.items():
        status = "✅" if _check_env(cfg) else "⚠️  (needs env vars)"
        print(f"  {status} {name}: {' '.join(cfg.get('args', []))}")
    print()


def _check_env(cfg: dict) -> bool:
    """Check if required env vars are set."""
    env = cfg.get("env", {})
    for key in env:
        if not os.getenv(key) and not env[key]:
            return False
    return True


def start_server(name: str):
    """Start a specific MCP server."""
    config = load_config()
    servers = config.get("mcpServers", {})
    
    if name not in servers:
        print(f"❌ Server '{name}' not found. Available: {list(servers.keys())}")
        return
    
    cfg = servers[name]
    cmd = [cfg["command"]] + cfg.get("args", [])
    env = os.environ.copy()
    for k, v in cfg.get("env", {}).items():
        env[k] = os.getenv(k, v)
    
    print(f"🚀 Starting MCP server: {name}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, env=env)
    except FileNotFoundError:
        print(f"❌ Command not found: {cfg['command']}. Is it installed?")
    except KeyboardInterrupt:
        print(f"\n⏹  Stopped {name}")


def start_all():
    """Start all configured MCP servers."""
    config = load_config()
    servers = config.get("mcpServers", {})
    
    print(f"🚀 Starting all MCP servers...\n")
    for name in servers:
        if _check_env(servers[name]):
            print(f"  ✅ {name}")
        else:
            print(f"  ⚠️  {name} (skipped — missing env vars)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python mcp_manager.py list")
        print("  python mcp_manager.py start <server_name>")
        print("  python mcp_manager.py start-all")
        list_servers()
    elif sys.argv[1] == "list":
        list_servers()
    elif sys.argv[1] == "start":
        start_server(sys.argv[2])
    elif sys.argv[1] == "start-all":
        start_all()
    else:
        print(f"Unknown command: {sys.argv[1]}")
