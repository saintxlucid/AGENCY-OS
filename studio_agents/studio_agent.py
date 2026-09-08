import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from agents import Agent, Runner, function_tool
from agents import set_default_openai_client, set_default_openai_api
from PIL import Image

load_dotenv()

# --- Clients ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
set_default_openai_client(client)
set_default_openai_api("chat_completions")  # Use chat completions for broader model support

# --- Paths ---
STUDIO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = STUDIO_ROOT / "output"
TEMP_DIR = STUDIO_ROOT / "tmp"
PROMPTS_DIR = STUDIO_ROOT / "prompts"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# --- Studio Metadata ---
STUDIO_VERSION = "1.0.0"
STUDIO_NAME = "DAIRA Design Studio"


def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_json(data: dict, filepath: Path) -> Path:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return filepath


def load_prompt_template(name: str) -> str:
    template_path = PROMPTS_DIR / "templates" / f"{name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


# --- Tool: Generate Image via DALL-E ---
@function_tool
async def generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> str:
    """Generate an image using DALL-E 3.
    
    Args:
        prompt: Detailed description of the image to generate.
        size: Image size - '1024x1024', '1792x1024', or '1024x1792'.
        quality: 'standard' or 'hd'.
        style: 'vivid' (dramatic) or 'natural' (more realistic).
    """
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=1
    )
    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt
    
    result = {
        "url": image_url,
        "revised_prompt": revised_prompt,
        "size": size,
        "quality": quality,
        "style": style,
        "original_prompt": prompt,
        "timestamp": get_timestamp()
    }
    
    save_json(result, OUTPUT_DIR / f"image_{get_timestamp()}.json")
    return json.dumps(result, indent=2)


# --- Tool: Analyze Image ---
@function_tool
async def analyze_image(image_path_or_url: str, analysis_type: str = "general") -> str:
    """Analyze an image using GPT-4o vision.
    
    Args:
        image_path_or_url: Local file path or URL of the image.
        analysis_type: Type of analysis - 'general', 'design', 'color_palette', 'accessibility', 'composition'.
    """
    if not image_path_or_url.startswith("http"):
        image_path_or_url = f"data:image/jpeg;base64,{_encode_image(image_path_or_url)}"
    
    prompts = {
        "general": "Describe this image in detail including subject, style, mood, colors, and composition.",
        "design": "Analyze this image from a design perspective: typography, layout, spacing, color theory, visual hierarchy, balance, and overall aesthetic quality. Provide specific, actionable feedback.",
        "color_palette": "Extract the complete color palette from this image. Provide hex codes, RGB values, and describe the color relationships (complementary, analogous, etc.). Suggest how these colors could be used in a design system.",
        "accessibility": "Evaluate this image/design for accessibility: color contrast ratios, text legibility, visual clarity. Identify any WCAG violations and suggest fixes.",
        "composition": "Analyze the composition: rule of thirds, leading lines, focal points, negative space, symmetry/asymmetry, depth, and visual flow. Rate the composition quality."
    }
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompts.get(analysis_type, prompts["general"])},
                {"type": "image_url", "image_url": {"url": image_path_or_url, "detail": "high"}}
            ]
        }],
        max_tokens=1500
    )
    
    result = {
        "analysis_type": analysis_type,
        "result": response.choices[0].message.content,
        "timestamp": get_timestamp()
    }
    
    save_json(result, OUTPUT_DIR / f"analysis_{get_timestamp()}.json")
    return json.dumps(result, indent=2)


def _encode_image(image_path: str) -> str:
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# --- Tool: Upscale / Process Image ---
@function_tool
async def process_image(
    image_path: str, 
    operation: str = "info",
    width: int = 512,
    height: int = 512,
    size: int = 256,
    quality: int = 85
) -> str:
    """Process a local image: resize, convert format, get info, create thumbnail.
    
    Args:
        image_path: Path to the local image file.
        operation: 'info', 'resize', 'thumbnail', 'convert_png', 'convert_jpeg', 'compress'.
        width: Target width for resize operation.
        height: Target height for resize operation.
        size: Target size for thumbnail operation.
        quality: JPEG quality (1-100) for compress/convert operations.
    """
    img = Image.open(image_path)
    
    if operation == "info":
        result = {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
            "path": image_path
        }
    elif operation == "resize":
        resized = img.resize((width, height), Image.LANCZOS)
        out_path = str(OUTPUT_DIR / f"resized_{get_timestamp()}.png")
        resized.save(out_path)
        result = {"operation": "resize", "new_size": [width, height], "saved_to": out_path}
    elif operation == "thumbnail":
        img.thumbnail((size, size), Image.LANCZOS)
        out_path = str(OUTPUT_DIR / f"thumb_{get_timestamp()}.png")
        img.save(out_path)
        result = {"operation": "thumbnail", "size": size, "saved_to": out_path}
    elif operation == "convert_png":
        out_path = str(OUTPUT_DIR / f"converted_{get_timestamp()}.png")
        img.save(out_path, "PNG")
        result = {"operation": "convert_png", "saved_to": out_path}
    elif operation == "convert_jpeg":
        out_path = str(OUTPUT_DIR / f"converted_{get_timestamp()}.jpg")
        img.convert("RGB").save(out_path, "JPEG", quality=quality)
        result = {"operation": "convert_jpeg", "saved_to": out_path}
    elif operation == "compress":
        out_path = str(OUTPUT_DIR / f"compressed_{get_timestamp()}.jpg")
        img.convert("RGB").save(out_path, "JPEG", quality=quality, optimize=True)
        result = {"operation": "compress", "quality": quality, "saved_to": out_path}
    else:
        result = {"error": f"Unknown operation: {operation}"}
    
    return json.dumps(result, indent=2)


# --- Tool: Web Search for Research ---
@function_tool
async def research_topic(query: str, focus: str = "general") -> str:
    """Research a topic using web search via GPT-4o.
    
    Args:
        query: What to research.
        focus: 'general', 'design_trends', 'ai_tools', 'color_trends', 'competitor_analysis'.
    """
    focus_prompts = {
        "general": f"Research: {query}. Provide comprehensive, up-to-date information.",
        "design_trends": f"Research the latest design trends related to: {query}. Focus on 2025-2026 trends, tools, and techniques.",
        "ai_tools": f"Find the best AI tools for: {query}. Compare features, pricing, and use cases.",
        "color_trends": f"Research current color trends and palettes for: {query}. Include hex codes and usage recommendations.",
        "competitor_analysis": f"Analyze competitors and similar products/services to: {query}. Include strengths, weaknesses, and positioning."
    }
    
    response = await client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[{"role": "user", "content": focus_prompts.get(focus, focus_prompts["general"])}],
        max_tokens=2000
    )
    
    result = {
        "query": query,
        "focus": focus,
        "result": response.choices[0].message.content,
        "timestamp": get_timestamp()
    }
    
    save_json(result, OUTPUT_DIR / f"research_{get_timestamp()}.json")
    return json.dumps(result, indent=2)


# --- Tool: Save Project Brief ---
@function_tool
async def save_project_brief(project_name: str, brief: str, tags: str = "") -> str:
    """Save a design brief or project notes to the studio.
    
    Args:
        project_name: Name of the project.
        brief: The brief content (markdown supported).
        tags: Comma-separated tags for categorization.
    """
    project_dir = STUDIO_ROOT / "projects" / project_name.replace(" ", "_").lower()
    project_dir.mkdir(parents=True, exist_ok=True)
    
    brief_data = {
        "project_name": project_name,
        "brief": brief,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "created_at": get_timestamp(),
        "status": "active"
    }
    
    filepath = project_dir / "brief.json"
    save_json(brief_data, filepath)
    
    # Also save markdown version
    md_path = project_dir / "brief.md"
    md_content = f"# {project_name}\n\n**Tags:** {tags}\n\n**Created:** {brief_data['created_at']}\n\n{brief}"
    md_path.write_text(md_content, encoding="utf-8")
    
    return f"Project brief saved to {filepath}"


# --- Core Design Studio Agent ---
design_studio_agent = Agent(
    name="DesignStudio",
    instructions="""You are DAIRA Design Studio — an AI-powered creative intelligence system.

You have access to these capabilities:
1. **generate_image** — Create images via DALL-E 3
2. **analyze_image** — Analyze images with GPT-4o vision (design, color, composition, accessibility)
3. **process_image** — Resize, convert, compress, thumbnail local images
4. **research_topic** — Research design trends, tools, color trends, competitors
5. **save_project_brief** — Save project briefs and notes

Your workflow:
- When asked to design/create: research first if needed, then generate, then analyze/refine
- When asked to analyze: use analyze_image with the right analysis_type
- When asked to research: use research_topic with appropriate focus
- Always save important outputs to the project brief
- Be concise but thorough — creative professionals value speed

Current project context and any active briefs will be provided in the conversation.""",
    tools=[generate_image, analyze_image, process_image, research_topic, save_project_brief],
    model="gpt-4o"
)


# --- Run Agent ---
async def run_studio(user_input: str, session_context: dict = None) -> str:
    """Run the design studio agent with user input."""
    context_str = ""
    if session_context:
        context_str = f"\n\n[Session Context]\n{json.dumps(session_context, indent=2, default=str)}"
    
    result = await Runner.run(design_studio_agent, input=user_input + context_str)
    return result.final_output


if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        print(f"╔══════════════════════════════════════════╗")
        print(f"║  {STUDIO_NAME} v{STUDIO_VERSION}            ║")
        print(f"║  AI-Powered Creative Intelligence       ║")
        print(f"╚══════════════════════════════════════════╝")
        print(f"\nType your creative prompts below. Commands:")
        print(f"  /quit — Exit")
        print(f"  /new  — New project")
        print(f"\n")
        
        async def interactive():
            session = {}
            while True:
                try:
                    user_input = input("\n🎨 Prompt> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break
                    
                if not user_input:
                    continue
                if user_input == "/quit":
                    print("\nGoodbye!")
                    break
                if user_input == "/new":
                    session = {}
                    print("New session started.")
                    continue
                
                print("\n⏳ Working...\n")
                result = await run_studio(user_input, session)
                print(f"\n{result}")
                
                # Save to session log
                log_entry = {"timestamp": get_timestamp(), "input": user_input, "output": result}
                session.setdefault("history", []).append(log_entry)
        
        asyncio.run(interactive())
