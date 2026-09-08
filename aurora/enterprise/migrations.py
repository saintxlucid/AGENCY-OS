"""
AGENCY OS — Database Migration System
Lightweight migration framework for enterprise data.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable


class Migration:
    """A single migration step."""

    def __init__(self, version: str, description: str, up: Callable, down: Optional[Callable] = None):
        self.version = version
        self.description = description
        self.up = up
        self.down = down
        self.applied_at: Optional[str] = None


class MigrationManager:
    """
    Manages database migrations for AGENCY OS.
    
    Migrations are stored as JSON files in the migrations directory.
    Each migration has a version, description, and up/down functions.
    """

    def __init__(self, migrations_dir: str = "./migrations", state_file: str = "./migrations/state.json"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._migrations: Dict[str, Migration] = {}
        self._load_state()

    def _load_state(self):
        """Load migration state from disk."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)
                self._applied = set(state.get("applied", []))
        else:
            self._applied = set()

    def _save_state(self):
        """Save migration state to disk."""
        state = {
            "applied": sorted(list(self._applied)),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def register(self, version: str, description: str, up: Callable, down: Optional[Callable] = None):
        """Register a migration."""
        self._migrations[version] = Migration(version, description, up, down)

    def migrate(self, target_version: Optional[str] = None):
        """Run all pending migrations up to target_version."""
        pending = self._get_pending(target_version)
        results = []
        for version in pending:
            migration = self._migrations[version]
            try:
                migration.up()
                migration.applied_at = datetime.now().isoformat()
                self._applied.add(version)
                results.append({"version": version, "status": "applied", "description": migration.description})
            except Exception as e:
                results.append({"version": version, "status": "failed", "error": str(e)})
                break
        self._save_state()
        return results

    def rollback(self, version: str):
        """Rollback to a specific version."""
        results = []
        for v in sorted(self._applied, reverse=True):
            if v > version:
                migration = self._migrations.get(v)
                if migration and migration.down:
                    try:
                        migration.down()
                        self._applied.discard(v)
                        results.append({"version": v, "status": "rolled_back"})
                    except Exception as e:
                        results.append({"version": v, "status": "failed", "error": str(e)})
                        break
        self._save_state()
        return results

    def _get_pending(self, target_version: Optional[str] = None) -> List[str]:
        """Get list of pending migrations."""
        all_versions = sorted(self._migrations.keys())
        pending = [v for v in all_versions if v not in self._applied]
        if target_version:
            pending = [v for v in pending if v <= target_version]
        return pending

    def status(self) -> Dict:
        """Get migration status."""
        all_versions = sorted(self._migrations.keys())
        return {
            "total": len(all_versions),
            "applied": len(self._applied),
            "pending": len(all_versions) - len(self._applied),
            "current_version": max(self._applied) if self._applied else None,
            "latest_version": max(all_versions) if all_versions else None,
            "migrations": [
                {
                    "version": v,
                    "description": self._migrations[v].description,
                    "applied": v in self._applied,
                    "applied_at": self._migrations[v].applied_at
                }
                for v in all_versions
            ]
        }


# ─── Default Migrations ───

def create_default_migrations(manager: MigrationManager):
    """Register default AGENCY OS migrations."""

    def init_schema():
        """Initialize base schema."""
        pass  # Schema is handled by dataclasses

    def add_org_settings():
        """Add settings field to organizations."""
        pass  # Already in dataclass

    def add_user_preferences():
        """Add preferences field to users."""
        pass  # Already in dataclass

    def add_project_priority():
        """Add priority field to projects."""
        pass  # Already in dataclass

    def add_invoice_currency():
        """Add currency field to invoices."""
        pass  # Already in dataclass

    manager.register("0.1.0", "Initialize base schema", init_schema)
    manager.register("0.2.0", "Add organization settings", add_org_settings)
    manager.register("0.3.0", "Add user preferences", add_user_preferences)
    manager.register("0.4.0", "Add project priority", add_project_priority)
    manager.register("0.5.0", "Add invoice currency", add_invoice_currency)


# ─── Singleton ───

_manager: Optional[MigrationManager] = None


def get_migration_manager() -> MigrationManager:
    """Get or create the migration manager singleton."""
    global _manager
    if _manager is None:
        _manager = MigrationManager()
        create_default_migrations(_manager)
    return _manager