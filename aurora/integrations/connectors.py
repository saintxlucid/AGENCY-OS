"""
AGENCY OS — Integration Connectors
Pre-built connectors for creative tools, developer tools, and productivity apps.
"""
from __future__ import annotations
import os, json, base64
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

import httpx


class Integration(ABC):
    """Base class for all integrations."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.client = httpx.AsyncClient(timeout=30.0)
        self._connected = False

    @property
    def name(self) -> str:
        return "base"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def health(self) -> Dict:
        pass

    async def disconnect(self):
        await self.client.aclose()
        self._connected = False


# ═══════════════════════════════════════════════════════════
# FIGMA INTEGRATION
# ═══════════════════════════════════════════════════════════

class FigmaIntegration(Integration):
    """Figma design tool integration."""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.access_token = self.config.get("access_token", os.getenv("FIGMA_ACCESS_TOKEN", ""))
        self.team_id = self.config.get("team_id", os.getenv("FIGMA_TEAM_ID", ""))
        self.base_url = "https://api.figma.com/v1"

    @property
    def name(self) -> str:
        return "figma"

    async def connect(self) -> bool:
        """Verify Figma connection."""
        if not self.access_token:
            return False
        try:
            resp = await self.client.get(
                f"{self.base_url}/me",
                headers={"X-Figma-Token": self.access_token}
            )
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            return False

    async def health(self) -> Dict:
        return {"name": "figma", "connected": self.is_connected}

    async def get_files(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get Figma files."""
        if not self._connected:
            await self.connect()

        if project_id:
            resp = await self.client.get(
                f"{self.base_url}/projects/{project_id}/files",
                headers={"X-Figma-Token": self.access_token}
            )
        else:
            resp = await self.client.get(
                f"{self.base_url}/teams/{self.team_id}/projects",
                headers={"X-Figma-Token": self.access_token}
            )

        if resp.status_code == 200:
            data = resp.json()
            return data.get("projects", []) or data.get("files", [])
        return []

    async def get_file(self, file_key: str) -> Optional[Dict]:
        """Get a specific Figma file."""
        if not self._connected:
            await self.connect()

        resp = await self.client.get(
            f"{self.base_url}/files/{file_key}",
            headers={"X-Figma-Token": self.access_token}
        )
        return resp.json() if resp.status_code == 200 else None

    async def get_file_nodes(self, file_key: str, node_ids: List[str]) -> Optional[Dict]:
        """Get specific nodes from a Figma file."""
        resp = await self.client.get(
            f"{self.base_url}/files/{file_key}/nodes",
            params={"ids": ",".join(node_ids)},
            headers={"X-Figma-Token": self.access_token}
        )
        return resp.json() if resp.status_code == 200 else None

    async def get_images(self, file_key: str, node_ids: List[str], format: str = "png") -> Dict:
        """Get rendered images of Figma nodes."""
        resp = await self.client.get(
            f"{self.base_url}/images/{file_key}",
            params={"ids": ",".join(node_ids), "format": format, "scale": "2"},
            headers={"X-Figma-Token": self.access_token}
        )
        return resp.json().get("images", {}) if resp.status_code == 200 else {}

    async def get_comments(self, file_key: str) -> List[Dict]:
        """Get comments on a Figma file."""
        resp = await self.client.get(
            f"{self.base_url}/files/{file_key}/comments",
            headers={"X-Figma-Token": self.access_token}
        )
        return resp.json().get("comments", []) if resp.status_code == 200 else []

    async def post_comment(self, file_key: str, message: str) -> Optional[Dict]:
        """Post a comment to a Figma file."""
        resp = await self.client.post(
            f"{self.base_url}/files/{file_key}/comments",
            json={"message": message},
            headers={"X-Figma-Token": self.access_token, "Content-Type": "application/json"}
        )
        return resp.json() if resp.status_code == 200 else None

    async def get_components(self, file_key: str) -> List[Dict]:
        """Extract components from a Figma file."""
        file_data = await self.get_file(file_key)
        if not file_data:
            return []

        components = []
        def traverse(node):
            if node.get("type") == "COMPONENT":
                components.append({
                    "id": node["id"],
                    "name": node.get("name", ""),
                    "type": node.get("type"),
                    "description": node.get("description", "")
                })
            for child in node.get("children", []):
                traverse(child)

        if "document" in file_data:
            traverse(file_data["document"])
        return components

    async def extract_design_tokens(self, file_key: str) -> Dict:
        """Extract design tokens (colors, typography, spacing) from a Figma file."""
        file_data = await self.get_file(file_key)
        tokens = {"colors": [], "typography": [], "spacing": []}

        if not file_data:
            return tokens

        # Extract styles
        styles = file_data.get("styles", {})
        for style_id, style in styles.items():
            if style.get("styleType") == "FILL":
                tokens["colors"].append({
                    "name": style.get("name", ""),
                    "type": "color",
                    "description": style.get("description", "")
                })
            elif style.get("styleType") == "TEXT":
                tokens["typography"].append({
                    "name": style.get("name", ""),
                    "type": "typography",
                    "description": style.get("description", "")
                })

        return tokens


# ═══════════════════════════════════════════════════════════
# ADOBE CREATIVE CLOUD INTEGRATION
# ═══════════════════════════════════════════════════════════

class AdobeIntegration(Integration):
    """Adobe Creative Cloud integration."""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.client_id = self.config.get("client_id", os.getenv("ADOBE_CLIENT_ID", ""))
        self.client_secret = self.config.get("client_secret", os.getenv("ADOBE_CLIENT_SECRET", ""))
        self.access_token = self.config.get("access_token", "")
        self.base_url = "https://cc-api-storage.adobe.io"

    @property
    def name(self) -> str:
        return "adobe"

    async def connect(self) -> bool:
        """Verify Adobe connection."""
        if not self.access_token:
            return False
        try:
            resp = await self.client.get(
                f"{self.base_url}/id",
                headers={"Authorization": f"Bearer {self.access_token}", "x-api-key": self.client_id}
            )
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            return False

    async def health(self) -> Dict:
        return {"name": "adobe", "connected": self.is_connected}

    async def get_assets(self, limit: int = 50) -> List[Dict]:
        """Get Adobe Creative Cloud assets."""
        if not self._connected:
            await self.connect()

        resp = await self.client.get(
            f"{self.base_url}/assets",
            params={"limit": limit},
            headers={"Authorization": f"Bearer {self.access_token}", "x-api-key": self.client_id}
        )
        return resp.json().get("assets", []) if resp.status_code == 200 else []

    async def get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get a specific Adobe asset."""
        resp = await self.client.get(
            f"{self.base_url}/assets/{asset_id}",
            headers={"Authorization": f"Bearer {self.access_token}", "x-api-key": self.client_id}
        )
        return resp.json() if resp.status_code == 200 else None


# ═══════════════════════════════════════════════════════════
# GITHUB INTEGRATION
# ═══════════════════════════════════════════════════════════

class GitHubIntegration(Integration):
    """GitHub integration for code repositories."""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.token = self.config.get("token", os.getenv("GITHUB_TOKEN", ""))
        self.org = self.config.get("org", os.getenv("GITHUB_ORG", ""))
        self.base_url = "https://api.github.com"

    @property
    def name(self) -> str:
        return "github"

    def _headers(self) -> Dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def connect(self) -> bool:
        """Verify GitHub connection."""
        if not self.token:
            return False
        try:
            resp = await self.client.get(f"{self.base_url}/user", headers=self._headers())
            self._connected = resp.status_code == 200
            return self._connected
        except Exception:
            return False

    async def health(self) -> Dict:
        return {"name": "github", "connected": self.is_connected}

    async def get_repos(self) -> List[Dict]:
        """Get repositories."""
        if self.org:
            resp = await self.client.get(
                f"{self.base_url}/orgs/{self.org}/repos",
                headers=self._headers(),
                params={"per_page": 100}
            )
        else:
            resp = await self.client.get(
                f"{self.base_url}/user/repos",
                headers=self._headers(),
                params={"per_page": 100}
            )
        return resp.json() if resp.status_code == 200 else []

    async def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository details."""
        resp = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}",
            headers=self._headers()
        )
        return resp.json() if resp.status_code == 200 else None

    async def get_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """Get repository issues."""
        resp = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            headers=self._headers(),
            params={"state": state, "per_page": 100}
        )
        return resp.json() if resp.status_code == 200 else []

    async def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """Get pull requests."""
        resp = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls",
            headers=self._headers(),
            params={"state": state, "per_page": 100}
        )
        return resp.json() if resp.status_code == 200 else []

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Optional[Dict]:
        """Create an issue."""
        resp = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            json={"title": title, "body": body, "labels": labels or []},
            headers=self._headers()
        )
        return resp.json() if resp.status_code == 201 else None

    async def get_commits(self, owner: str, repo: str, since: Optional[str] = None) -> List[Dict]:
        """Get commit history."""
        params = {"per_page": 100}
        if since:
            params["since"] = since
        resp = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/commits",
            headers=self._headers(),
            params=params
        )
        return resp.json() if resp.status_code == 200 else []


# ═══════════════════════════════════════════════════════════
# SLACK INTEGRATION
# ═══════════════════════════════════════════════════════════

class SlackIntegration(Integration):
    """Slack messaging integration."""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.bot_token = self.config.get("bot_token", os.getenv("SLACK_BOT_TOKEN", ""))
        self.base_url = "https://slack.com/api"

    @property
    def name(self) -> str:
        return "slack"

    def _headers(self) -> Dict:
        return {"Authorization": f"Bearer {self.bot_token}"}

    async def connect(self) -> bool:
        """Verify Slack connection."""
        if not self.bot_token:
            return False
        try:
            resp = await self.client.post(f"{self.base_url}/auth.test", headers=self._headers())
            data = resp.json()
            self._connected = data.get("ok", False)
            return self._connected
        except Exception:
            return False

    async def health(self) -> Dict:
        return {"name": "slack", "connected": self.is_connected}

    async def send_message(self, channel: str, text: str, blocks: List[Dict] = None) -> Optional[Dict]:
        """Send a message to a channel."""
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        resp = await self.client.post(
            f"{self.base_url}/chat.postMessage",
            json=payload,
            headers=self._headers()
        )
        return resp.json() if resp.status_code == 200 else None

    async def get_channels(self) -> List[Dict]:
        """Get list of channels."""
        resp = await self.client.get(
            f"{self.base_url}/conversations.list",
            headers=self._headers(),
            params={"types": "public_channel,private_channel"}
        )
        return resp.json().get("channels", []) if resp.status_code == 200 else []

    async def get_channel_history(self, channel: str, limit: int = 100) -> List[Dict]:
        """Get channel message history."""
        resp = await self.client.get(
            f"{self.base_url}/conversations.history",
            headers=self._headers(),
            params={"channel": channel, "limit": limit}
        )
        return resp.json().get("messages", []) if resp.status_code == 200 else []


# ═══════════════════════════════════════════════════════════
# INTEGRATION MANAGER
# ═══════════════════════════════════════════════════════════

class IntegrationManager:
    """Manages all integrations for AGENCY OS."""

    def __init__(self):
        self.integrations: Dict[str, Integration] = {}

    def register(self, integration: Integration):
        """Register an integration."""
        self.integrations[integration.name] = integration

    def get(self, name: str) -> Optional[Integration]:
        """Get an integration by name."""
        return self.integrations.get(name)

    async def connect_all(self) -> Dict[str, bool]:
        """Connect all integrations."""
        results = {}
        for name, integration in self.integrations.items():
            results[name] = await integration.connect()
        return results

    async def health_all(self) -> List[Dict]:
        """Get health status of all integrations."""
        results = []
        for name, integration in self.integrations.items():
            results.append(await integration.health())
        return results

    async def disconnect_all(self):
        """Disconnect all integrations."""
        for integration in self.integrations.values():
            await integration.disconnect()

    def list_integrations(self) -> List[str]:
        """List all registered integrations."""
        return list(self.integrations.keys())

    @classmethod
    def create_default(cls, config: Dict = None) -> 'IntegrationManager':
        """Create manager with default integrations."""
        manager = cls()
        config = config or {}

        # Register all integrations
        if config.get("figma"):
            manager.register(FigmaIntegration(config["figma"]))
        if config.get("adobe"):
            manager.register(AdobeIntegration(config["adobe"]))
        if config.get("github"):
            manager.register(GitHubIntegration(config["github"]))
        if config.get("slack"):
            manager.register(SlackIntegration(config["slack"]))

        return manager


# ─── Export ───

__all__ = [
    "Integration", "IntegrationManager",
    "FigmaIntegration", "AdobeIntegration",
    "GitHubIntegration", "SlackIntegration"
]