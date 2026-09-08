"""
Media Generation Pipeline for Design Studio
Supports: image generation, batch generation, variation chains, style transfers.
"""
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from PIL import Image
import io

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

STUDIO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = STUDIO_ROOT / "output"
TEMP_DIR = STUDIO_ROOT / "tmp"
PROMPTS_DIR = STUDIO_ROOT / "prompts"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class MediaPipeline:
    """Multi-provider media generation pipeline."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    # ─── DALL-E Image Generation ───
    
    async def generate_dalle(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        save_metadata: bool = True
    ) -> dict:
        """Generate image using DALL-E 3."""
        response = await self.openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1
        )
        
        result = {
            "provider": "openai",
            "model": "dall-e-3",
            "url": response.data[0].url,
            "revised_prompt": response.data[0].revised_prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "original_prompt": prompt,
            "timestamp": get_timestamp()
        }
        
        if save_metadata:
            meta_path = OUTPUT_DIR / f"dalle_{get_timestamp()}.json"
            with open(meta_path, "w") as f:
                json.dump(result, f, indent=2)
        
        return result
    
    # ─── Batch Generation ───
    
    async def batch_generate(
        self,
        prompts: list[str],
        size: str = "1024x1024",
        style: str = "vivid"
    ) -> list[dict]:
        """Generate multiple images from a list of prompts."""
        results = []
        for i, prompt in enumerate(prompts):
            print(f"  🎨 [{i+1}/{len(prompts)}] Generating: {prompt[:60]}...")
            result = await self.generate_dalle(prompt, size=size, style=style)
            results.append(result)
        return results
    
    # ─── Variation Chain ───
    
    async def variation_chain(
        self,
        base_prompt: str,
        variations: list[str],
        size: str = "1024x1024"
    ) -> list[dict]:
        """Generate a base image + styled variations.
        
        Args:
            base_prompt: Core subject/descriptor
            variations: List of style modifiers to append
            size: Image dimensions
        """
        results = []
        
        # Generate base
        print(f"  🎨 [BASE] {base_prompt}")
        base = await self.generate_dalle(base_prompt, size=size)
        base["variant"] = "base"
        results.append(base)
        
        # Generate variations
        for i, var in enumerate(variations):
            full_prompt = f"{base_prompt}, {var}"
            print(f"  🎨 [VAR {i+1}] {var}")
            result = await self.generate_dalle(full_prompt, size=size)
            result["variant"] = var
            results.append(result)
        
        # Save chain metadata
        chain_meta = {
            "base_prompt": base_prompt,
            "variations": variations,
            "results": results,
            "timestamp": get_timestamp()
        }
        meta_path = OUTPUT_DIR / f"chain_{get_timestamp()}.json"
        with open(meta_path, "w") as f:
            json.dump(chain_meta, f, indent=2, default=str)
        
        return results
    
    # ─── Style Reference Prompts ───
    
    @staticmethod
    def build_style_prompt(
        subject: str,
        style: str = "modern minimalist",
        medium: str = "digital art",
        color_palette: str = "vibrant",
        mood: str = "professional",
        composition: str = "centered",
        extra: str = ""
    ) -> str:
        """Build a detailed prompt from style parameters."""
        prompt = f"{subject}, in the style of {style} {medium}"
        prompt += f", {color_palette} color palette"
        prompt += f", {mood} mood"
        prompt += f", {composition} composition"
        if extra:
            prompt += f", {extra}"
        return prompt
    
    # ─── Image Analysis via Claude Vision ───
    
    async def analyze_with_claude(
        self,
        image_path_or_url: str,
        question: str = "Describe this image in detail."
    ) -> str:
        """Analyze an image using Claude's vision capabilities."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        if image_path_or_url.startswith("http"):
            # Download image
            import httpx
            response = await httpx.AsyncClient().get(image_path_or_url)
            image_data = response.content
            media_type = "image/png"
        else:
            with open(image_path_or_url, "rb") as f:
                image_data = f.read()
            ext = Path(image_path_or_url).suffix.lower()
            media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        
        import base64
        b64 = base64.b64encode(image_data).decode()
        
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": question}
                ]
            }]
        )
        
        return message.content[0].text


# ─── Quick Generation Helpers ───

async def quick_generate(prompt: str) -> dict:
    """One-shot image generation."""
    pipeline = MediaPipeline()
    return await pipeline.generate_dalle(prompt)


async def quick_chain(base: str, variations: list[str]) -> list[dict]:
    """One-shot variation chain."""
    pipeline = MediaPipeline()
    return await pipeline.variation_chain(base, variations)


# ─── CLI ───

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Media Pipeline — Usage:")
        print("  python media_pipeline.py generate \"a futuristic city\"")
        print("  python media_pipeline.py batch \"prompt1\" \"prompt2\" \"prompt3\"")
        print("  python media_pipeline.py chain \"base prompt\" \"variation 1\" \"variation 2\"")
        print("  python media_pipeline.py style \"subject\" --style \"minimalist\" --mood \"calm\"")
        return
    
    pipeline = MediaPipeline()
    command = sys.argv[1]
    
    if command == "generate":
        prompt = " ".join(sys.argv[2:])
        result = await pipeline.generate_dalle(prompt)
        print(f"\n✅ Generated: {result['url']}")
        print(f"   Revised: {result.get('revised_prompt', 'N/A')}")
    
    elif command == "batch":
        prompts = sys.argv[2:]
        results = await pipeline.batch_generate(prompts)
        print(f"\n✅ Generated {len(results)} images")
        for r in results:
            print(f"   - {r['url']}")
    
    elif command == "chain":
        base = sys.argv[2]
        variations = sys.argv[3:]
        results = await pipeline.variation_chain(base, variations)
        print(f"\n✅ Generated {len(results)} images (base + {len(variations)} variations)")
        for r in results:
            print(f"   [{r.get('variant', 'base')}] {r['url']}")
    
    elif command == "style":
        subject = sys.argv[2]
        # Parse optional flags
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i].startswith("--") and i + 1 < len(sys.argv):
                kwargs[sys.argv[i][2:]] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        prompt = pipeline.build_style_prompt(subject, **kwargs)
        print(f"📝 Built prompt: {prompt}")
        result = await pipeline.generate_dalle(prompt)
        print(f"\n✅ Generated: {result['url']}")


if __name__ == "__main__":
    asyncio.run(main())
