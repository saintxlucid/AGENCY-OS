"""
AURORA CLI — Command-line interface for the Universal Creative Intelligence Platform.
"""
from __future__ import annotations

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aurora.core import AuroraCore, MediaType, IntelligenceDomain, ProjectContext


class AuroraCLI:
    """Main CLI application."""
    
    def __init__(self):
        self.aurora: Optional[AuroraCore] = None
    
    async def initialize(self):
        """Initialize Aurora core."""
        print("🌅 Initializing AURORA...")
        self.aurora = AuroraCore()
        await self.aurora.initialize()
    
    async def shutdown(self):
        """Shutdown Aurora."""
        if self.aurora:
            await self.aurora.shutdown()
    
    # ─── Commands ───
    
    async def cmd_interpret(self, args):
        """Interpret media file(s)."""
        if not args.files:
            print("Error: No files specified")
            return
        
        for file_path in args.files:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ File not found: {file_path}")
                continue
            
            media_type = None
            if args.type:
                try:
                    media_type = MediaType(args.type)
                except ValueError:
                    print(f"⚠️  Unknown media type: {args.type}, auto-detecting")
            
            print(f"\n🔍 Interpreting: {path.name}")
            interpretation = await self.aurora.interpret(path, media_type)
            
            print(f"  ✅ Media ID: {interpretation.media_id}")
            print(f"  📝 Summary: {interpretation.summary}")
            print(f"  ⭐ Quality: {interpretation.quality_score}/10")
            print(f"  🏷️  Tags: {', '.join(interpretation.tags)}")
            print(f"  💡 Insights ({len(interpretation.insights)}):")
            for insight in interpretation.insights[:5]:
                print(f"    • [{insight.domain.value}] {insight.finding}")
            
            if args.critique:
                print(f"\n  📋 Critique:")
                critiques = await self.aurora.critique(interpretation)
                for c in critiques[:5]:
                    print(f"    • [{c.domain.value}] {c.finding}")
            
            if args.improve:
                print(f"\n  🚀 Improvements:")
                improvements = await self.aurora.improve(interpretation)
                for i in improvements[:5]:
                    print(f"    • [{i.domain.value}] {i.finding}")
    
    async def cmd_project(self, args):
        """Project management."""
        if args.action == "create":
            project = await self.aurora.create_project(
                name=args.name,
                description=args.description or "",
                brief=args.brief,
                target_audience=args.audience,
                goals=args.goals.split(",") if args.goals else []
            )
            print(f"✅ Project created: {project.name} ({project.project_id})")
        
        elif args.action == "list":
            # Would query memory for projects
            print("📁 Projects: (query memory for full list)")
        
        elif args.action == "switch":
            print(f"🔄 Switching project: {args.name}")
            # Would load project from memory
    
    async def cmd_observe(self, args):
        """Start live observation."""
        if not args.targets:
            print("Error: No targets specified")
            return
        
        interval = args.interval or 5.0
        
        print(f"👁️  Starting observation on {len(args.targets)} targets (interval: {interval}s)")
        print("   Press Ctrl+C to stop\n")
        
        await self.aurora.start_observation(args.targets, interval)
        
        try:
            while self.aurora.observation_active:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping observation...")
            await self.aurora.stop_observation()
    
    async def cmd_query(self, args):
        """Query creative memory."""
        if not args.question:
            print("Error: No question specified")
            return
        
        domain = None
        if args.domain:
            try:
                domain = IntelligenceDomain(args.domain)
            except ValueError:
                print(f"⚠️  Unknown domain: {args.domain}")
        
        print(f"🔍 Querying: {args.question}")
        result = await self.aurora.query(args.question, domain)
        print(f"\n{result}")
    
    async def cmd_status(self, args):
        """Show system status."""
        status = self.aurora.status()
        print(json.dumps(status, indent=2))
    
    async def cmd_export(self, args):
        """Export interpretation to external format."""
        if not args.media_id or not args.target:
            print("Error: media_id and target required")
            return
        
        result = await self.aurora.export_to(args.media_id, args.target, args.format)
        print(f"Exported to {args.target}: {result}")
    
    async def cmd_batch(self, args):
        """Batch interpret multiple files."""
        if not args.directory:
            print("Error: Directory required")
            return
        
        path = Path(args.directory)
        if not path.exists():
            print(f"❌ Directory not found: {path}")
            return
        
        extensions = args.extensions.split(",") if args.extensions else [".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov"]
        files = []
        for ext in extensions:
            files.extend(path.rglob(f"*{ext}"))
        
        print(f"📦 Batch processing {len(files)} files...")
        
        for i, file_path in enumerate(files):
            print(f"\n[{i+1}/{len(files)}] {file_path.name}")
            try:
                await self.aurora.interpret(file_path)
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print(f"\n✅ Batch complete: {len(files)} files processed")
    
    def build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser."""
        parser = argparse.ArgumentParser(
            prog="aurora",
            description="AURORA — Universal Creative Intelligence Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  aurora interpret image.png --critique --improve
  aurora interpret video.mp4 --type video
  aurora project create "Brand Campaign" --audience "Gen Z" --goals "awareness,conversion"
  aurora observe ./designs --interval 3
  aurora query "What color palettes work for fintech?" --domain marketing
  aurora batch ./assets --extensions png,jpg,mp4
  aurora status
        """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # interpret
        p_interpret = subparsers.add_parser("interpret", aliases=["i"], help="Interpret media file")
        p_interpret.add_argument("files", nargs="+", help="Media files to interpret")
        p_interpret.add_argument("--type", "-t", choices=[m.value for m in MediaType], help="Media type (auto-detect if omitted)")
        p_interpret.add_argument("--critique", "-c", action="store_true", help="Generate critique")
        p_interpret.add_argument("--improve", action="store_true", help="Generate improvements")
        
        # project
        p_project = subparsers.add_parser("project", aliases=["p"], help="Project management")
        p_project.add_argument("action", choices=["create", "list", "switch"])
        p_project.add_argument("--name", "-n", help="Project name")
        p_project.add_argument("--description", "-d", help="Project description")
        p_project.add_argument("--brief", "-b", help="Project brief")
        p_project.add_argument("--audience", "-a", help="Target audience")
        p_project.add_argument("--goals", "-g", help="Comma-separated goals")
        
        # observe
        p_observe = subparsers.add_parser("observe", aliases=["o", "watch"], help="Live observation")
        p_observe.add_argument("targets", nargs="+", help="Files/directories to watch")
        p_observe.add_argument("--interval", "-i", type=float, default=5.0, help="Check interval (seconds)")
        
        # query
        p_query = subparsers.add_parser("query", aliases=["q", "ask"], help="Query creative memory")
        p_query.add_argument("question", help="Question to ask")
        p_query.add_argument("--domain", "-d", choices=[d.value for d in IntelligenceDomain], help="Focus domain")
        
        # status
        subparsers.add_parser("status", aliases=["s"], help="System status")
        
        # export
        p_export = subparsers.add_parser("export", aliases=["e"], help="Export to external tool")
        p_export.add_argument("--media-id", required=True, help="Media ID to export")
        p_export.add_argument("--target", required=True, help="Target integration (figma, webflow, etc.)")
        p_export.add_argument("--format", default="json", help="Export format")
        
        # batch
        p_batch = subparsers.add_parser("batch", help="Batch process directory")
        p_batch.add_argument("directory", help="Directory to process")
        p_batch.add_argument("--extensions", help="Comma-separated extensions (default: png,jpg,jpeg,webp,mp4,mov)")
        
        return parser
    
    async def run(self, argv: List[str] = None):
        """Run CLI."""
        parser = self.build_parser()
        args = parser.parse_args(argv)
        
        if not args.command:
            parser.print_help()
            return
        
        await self.initialize()
        
        try:
            cmd_map = {
                "interpret": self.cmd_interpret,
                "i": self.cmd_interpret,
                "project": self.cmd_project,
                "p": self.cmd_project,
                "observe": self.cmd_observe,
                "o": self.cmd_observe,
                "watch": self.cmd_observe,
                "query": self.cmd_query,
                "q": self.cmd_query,
                "ask": self.cmd_query,
                "status": self.cmd_status,
                "s": self.cmd_status,
                "export": self.cmd_export,
                "e": self.cmd_export,
                "batch": self.cmd_batch,
            }
            
            if args.command in cmd_map:
                await cmd_map[args.command](args)
            else:
                print(f"Unknown command: {args.command}")
        
        finally:
            await self.shutdown()


async def main():
    cli = AuroraCLI()
    await cli.run(sys.argv[1:])


if __name__ == "__main__":
    asyncio.run(main())