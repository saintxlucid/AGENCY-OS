"""
Live Creative Observation System
Watches files/applications in real-time and provides continuous creative review.
"""
from __future__ import annotations

import os
import asyncio
import hashlib
import inspect
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class WatchTargetType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    APPLICATION = "application"
    SCREEN_REGION = "screen_region"


@dataclass
class WatchTarget:
    """A target to observe."""
    target_id: str
    target_type: WatchTargetType
    path: str
    name: str
    interval: float = 5.0
    enabled: bool = True
    filters: List[str] = field(default_factory=list)  # File extensions to watch
    callback: Optional[Callable] = None


@dataclass
class ObservationEvent:
    """An event from live observation."""
    event_id: str
    target_id: str
    event_type: str  # created, modified, deleted, accessed
    timestamp: str
    file_path: Optional[str] = None
    changes: Optional[Dict] = None
    interpretation: Optional[Any] = None
    insights: List[Any] = field(default_factory=list)


class FileWatcher(FileSystemEventHandler):
    """Watchdog handler for file system events."""
    
    def __init__(self, observer: 'LiveObserver'):
        self.observer = observer
        self.last_hashes: Dict[str, str] = {}
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.observer._handle_file_change(event.src_path, "modified"))
    
    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(self.observer._handle_file_change(event.src_path, "created"))
    
    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(self.observer._handle_file_change(event.src_path, "deleted"))


class LiveObserver:
    """
    Live Creative Observation System.
    
    Watches creative files and applications, providing continuous
    interpretation and critique as work progresses.
    """
    
    def __init__(self, aurora_core):
        self.core = aurora_core
        self.targets: Dict[str, WatchTarget] = {}
        self.events: List[ObservationEvent] = []
        self.running = False
        self.observer: Optional[Observer] = None
        self.file_watcher = FileWatcher(self)
        self._watch_task: Optional[asyncio.Task] = None
        self._debounce: Dict[str, float] = {}
        self.debounce_interval = 2.0  # seconds
        self._sentinel_sinks: List[Callable] = []  # PHASE 1 seam 4: Sentinel subscriptions
    
    async def start(self, targets: List[str], interval: float = 5.0):
        """Start observing targets."""
        print(f"👁️  Starting live observation on {len(targets)} targets...")
        
        # Register targets
        for target_path in targets:
            await self._register_target(target_path, interval)
        
        # Start file system observer
        self.observer = Observer()
        for target in self.targets.values():
            if target.target_type in (WatchTargetType.FILE, WatchTargetType.DIRECTORY):
                path = Path(target.path).parent if target.target_type == WatchTargetType.FILE else Path(target.path)
                self.observer.schedule(self.file_watcher, str(path), recursive=True)
        
        self.observer.start()
        self.running = True
        
        # Start periodic check task
        self._watch_task = asyncio.create_task(self._periodic_check())
        
        print("✅ Live observation active")
    
    async def stop(self):
        """Stop observation."""
        self.running = False
        
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        print("⏹️  Live observation stopped")
    
    async def _register_target(self, target_path: str, interval: float):
        """Register a watch target."""
        path = Path(target_path)
        target_id = hashlib.md5(target_path.encode()).hexdigest()[:8]
        
        if path.is_file():
            target_type = WatchTargetType.FILE
        elif path.is_dir():
            target_type = WatchTargetType.DIRECTORY
        else:
            # Could be application name
            target_type = WatchTargetType.APPLICATION
        
        target = WatchTarget(
            target_id=target_id,
            target_type=target_type,
            path=str(path),
            name=path.name,
            interval=interval
        )
        
        self.targets[target_id] = target
        print(f"  📌 Registered: {target.name} ({target_type.value})")
    
    async def _periodic_check(self):
        """Periodic check for application-level observation."""
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                for target in self.targets.values():
                    if target.target_type == WatchTargetType.APPLICATION:
                        await self._check_application(target)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Observation check error: {e}")
    
    async def _check_application(self, target: WatchTarget):
        """Check application state (placeholder for app integration)."""
        # In production: integrate with OS accessibility APIs
        # macOS: AXUIElement, Windows: UI Automation, Linux: AT-SPI
        pass
    
    async def _handle_file_change(self, file_path: str, event_type: str):
        """Handle file system change with debouncing."""
        now = time.time()
        
        # Debounce
        if file_path in self._debounce:
            if now - self._debounce[file_path] < self.debounce_interval:
                return
        
        self._debounce[file_path] = now
        
        # Find matching target
        target = None
        for t in self.targets.values():
            if t.target_type == WatchTargetType.FILE and t.path == file_path:
                target = t
                break
            elif t.target_type == WatchTargetType.DIRECTORY and file_path.startswith(t.path):
                target = t
                break
        
        if not target or not target.enabled:
            return
        
        print(f"🔄 Change detected: {Path(file_path).name} ({event_type})")
        
        # Interpret the changed file
        try:
            interpretation = await self.core.interpret(file_path)
            
            # Generate critique
            critiques = await self.core.critique(interpretation)
            
            # Generate improvements
            improvements = await self.core.improve(interpretation)
            
            # Create event
            event = ObservationEvent(
                event_id=hashlib.md5(f"{file_path}{now}".encode()).hexdigest()[:12],
                target_id=target.target_id,
                event_type=event_type,
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                interpretation=interpretation,
                insights=critiques + improvements
            )
            
            self.events.append(event)

            # PHASE 1 seam 4: fan out to Sentinel subscribers (subscription, not polling).
            # Sentinel owns hashing/log/staging; failures here never break observation.
            for sink in list(self._sentinel_sinks):
                try:
                    out = sink(event)
                    if inspect.isawaitable(out):
                        await out
                except Exception as e:
                    print(f"  ⚠️  sentinel sink error: {e}")

            # Print summary
            print(f"  📝 Live critique for {Path(file_path).name}:")
            for insight in (critiques + improvements)[:3]:
                print(f"    • [{insight.domain.value}] {insight.finding[:80]}...")
            
            # Trigger callback if set
            if target.callback:
                await target.callback(event)
                
        except Exception as e:
            print(f"  ⚠️  Observation interpretation error: {e}")
    
    def get_recent_events(self, limit: int = 20) -> List[ObservationEvent]:
        """Get recent observation events."""
        return self.events[-limit:]
    
    def get_target_status(self, target_id: str) -> Optional[Dict]:
        """Get status of a watch target."""
        if target_id not in self.targets:
            return None
        
        t = self.targets[target_id]
        target_events = [e for e in self.events if e.target_id == target_id]
        
        return {
            "target_id": target_id,
            "name": t.name,
            "type": t.target_type.value,
            "path": t.path,
            "enabled": t.enabled,
            "interval": t.interval,
            "event_count": len(target_events),
            "last_event": target_events[-1].timestamp if target_events else None,
        }
    
    def enable_target(self, target_id: str):
        """Enable a watch target."""
        if target_id in self.targets:
            self.targets[target_id].enabled = True
    
    def disable_target(self, target_id: str):
        """Disable a watch target."""
        if target_id in self.targets:
            self.targets[target_id].enabled = False
    
    async def set_callback(self, target_id: str, callback: Callable):
        """Set callback for target events."""
        if target_id in self.targets:
            self.targets[target_id].callback = callback

    # ─── PHASE 1 seam 4: Sentinel subscription ───

    def subscribe_sentinel(self, sentinel: Any) -> Callable:
        """Subscribe a Sentinel (or any sink with ingest_event). Returns unsub fn."""
        fn = getattr(sentinel, "ingest_event", None)
        sink = fn if callable(fn) else sentinel  # allow raw callable(event)
        self._sentinel_sinks.append(sink)
        def _unsub():
            try:
                self._sentinel_sinks.remove(sink)
            except ValueError:
                pass
        return _unsub