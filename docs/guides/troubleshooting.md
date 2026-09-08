# Help & Troubleshooting

**AGENCY OS — Common Issues and Solutions**

---

## Quick Diagnostic

Run the built-in diagnostic to identify common issues:

```bash
python aurora/cli.py status --diagnostic
```

**Output:**
```
🔍 AGENCY OS Diagnostic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Python 3.11.9
✅ Virtual environment active
✅ OpenAI API key configured
⚠️  Anthropic API key missing (optional)
✅ ChromaDB connected
✅ Memory graph: 3,891 nodes, 12,450 edges
✅ MCP servers: 2/12 connected
⚠️  npx not found (required for MCP servers)
✅ Disk space: 45.2 GB free
✅ Memory: 8.2 GB available

Recommendations:
  • Install npx for MCP server support: npm install -g npx
  • Add Anthropic API key for Claude fallback
```

---

## Installation Issues

### Python Version

**Problem:** `python: command not found` or wrong version

**Solution:**
```bash
# Check version
python --version  # Needs 3.10+

# If wrong version, use pyenv
pyenv install 3.11.9
pyenv local 3.11.9
```

### pip Install Fails

**Problem:** `pip install -r requirements.txt` fails

**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# If specific package fails, try without version pin
pip install openai anthropic chromadb

# On Windows, some packages need Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Virtual Environment Issues

**Problem:** `venv` module not found or activation fails

**Solution:**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# If execution policy blocks activation
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## API Key Issues

### OpenAI API Key Not Working

**Problem:** `AuthenticationError: Incorrect API key provided`

**Solution:**
1. Verify key at https://platform.ly/api-keys
2. Ensure no extra spaces in `.env` file
3. Check key hasn't expired
4. Verify billing is set up

```bash
# Test key directly
python -c "import openai; c = openai.Client(); print(c.models.list())"
```

### Anthropic API Key

**Problem:** `AuthenticationError` with Claude

**Solution:**
1. Get key from https://console.anthropic.com/
2. Ensure `ANTHROPIC_API_KEY` is set in `.env`
3. Check API access is enabled

### Rate Limiting

**Problem:** `RateLimitError: Rate limit exceeded`

**Solution:**
- Reduce request frequency
- Upgrade API tier
- Implement retry with exponential backoff
- Use multiple API keys with rotation

---

## Memory & Storage Issues

### ChromaDB Errors

**Problem:** `chromadb.errors.InvalidDimensionException`

**Solution:**
```bash
# Clear and rebuild memory
rm -rf aurora_memory/
python aurora/cli.py status  # Rebuilds automatically
```

### Disk Space

**Problem:** `OSError: [Errno 28] No space left on device`

**Solution:**
```bash
# Check disk usage
du -sh aurora_memory/
du -sh agency_os_data/
du -sh output/

# Clear temporary files
rm -rf tmp/
rm -rf output/

# Clear memory graph (keep ChromaDB)
rm aurora_memory/graph.gpickle
```

### Memory Graph Corruption

**Problem:** `pickle.UnpicklingError` on startup

**Solution:**
```bash
# Reset memory graph (keeps ChromaDB data)
rm aurora_memory/graph.gpickle
# Restart — graph will rebuild from ChromaDB on next store
```

---

## MCP Server Issues

### npx Not Found

**Problem:** `FileNotFoundError: [WinError 2] The system cannot find the file specified`

**Solution:**
```bash
# Install Node.js (includes npx)
# https://nodejs.org/ (LTS version recommended)

# Verify
npx --version

# If still not found, add to PATH
# Windows: Add C:\Program Files\nodejs\ to PATH
# macOS/Linux: Add /usr/local/bin to PATH
```

### MCP Server Won't Start

**Problem:** Server shows `error: ...` status

**Solution:**
```bash
# Check server logs
python aurora/cli.py mcp status

# Try starting manually
npx -y @modelcontextprotocol/server-filesystem ./

# If permissions issue (Linux/macOS)
chmod +x $(which npx)
```

### MCP Tool Not Available

**Problem:** `Tool not found` when calling MCP tool

**Solution:**
1. Check server is connected: `python aurora/cli.py mcp list`
2. Verify tool name matches server definition
3. Restart MCP server
4. Check `.mcp.json` configuration

---

## Performance Issues

### Slow Interpretation

**Problem:** Media interpretation takes too long

**Solution:**
```yaml
# Reduce quality for speed
intelligence:
  engines:
    visual:
      model: gpt-4o-mini  # Faster, less detailed
    narrative:
      enabled: false      # Disable unused engines

# Or use smaller images
from PIL import Image
img = Image.open("large.png")
img.thumbnail((1024, 1024))
img.save("smaller.png")
```

### High Memory Usage

**Problem:** Process uses too much RAM

**Solution:**
```bash
# Limit ChromaDB memory
export CHROMA_SERVER_NOFILE=65536

# Use smaller embedding model
# In config:
memory:
  embedding_model: all-MiniLM-L6-v2  # 80MB, vs 1.5GB for larger

# Process in smaller batches
python aurora/cli.py batch ./assets --extensions png  # Not png,jpg,mp4
```

### Slow Queries

**Problem:** Memory queries are slow

**Solution:**
```yaml
# Reduce search scope
memory:
  max_results: 5  # Default: 10

# Use specific domain
python aurora/cli.py query "question" --domain visual
```

---

## CLI Issues

### Command Not Found

**Problem:** `aurora: command not found`

**Solution:**
```bash
# Run directly
python aurora/cli.py --help

# Or create alias
alias aurora='python /path/to/aurora/cli.py'

# Or install as package
pip install -e .
```

### JSON Parse Errors

**Problem:** `json.decoder.JSONDecodeError` on output

**Solution:**
```bash
# Ensure output directory exists
mkdir -p output

# Use text output instead
python aurora/cli.py interpret asset.png -o text

# Check file encoding
file -i asset.png
```

---

## Intelligence Engine Issues

### No Insights Generated

**Problem:** Interpretation returns 0 insights

**Solution:**
```python
# Check media type detection
from aurora.core import MediaType
interpretation = await aurora.interpret("file.xyz")
print(interpretation.media_type)  # May be wrong

# Force media type
interpretation = await aurora.interpret("file.xyz", media_type=MediaType.IMAGE)

# Check if engines are loaded
print(aurora._intelligence_engines)  # Should show 6 engines
```

### Low Quality Scores

**Problem:** All assets score below 5.0

**Solution:**
- This may be correct — low-quality assets score low
- Check if media is loading correctly
- Verify vision API is working
- Compare with known-good reference images

---

## Enterprise Issues

### Permission Denied

**Problem:** `ValueError: Organization has reached max projects`

**Solution:**
```python
# Check current limits
core.get_org_stats("org_123")

# Upgrade plan
org.billing_plan = "enterprise"
org.max_projects = 9999

# Or archive old projects
project.status = "archived"
org.project_count -= 1
```

### User Can't Access Organization

**Problem:** `User has no role in organization`

**Solution:**
```python
# Check user roles
user = core.users["user_123"]
print(user.roles)  # Should include org_id

# Add to org
user.add_to_org("org_123", Role.DESIGNER)
```

---

## Getting More Help

### Community

- **Discord:** https://discord.gg/agencyos
- **GitHub Issues:** https://github.com/agency-os/agency-os/issues
- **Documentation:** https://docs.agencyos.com
- **Email:** support@agencyos.com

### Debug Mode

Run with verbose logging:

```bash
# Set log level
export AGENCY_OS_LOG_LEVEL=DEBUG

# Or on command line
python aurora/cli.py interpret asset.png --verbose
```

### Collecting Debug Info

```bash
# Generate debug report
python aurora/cli.py status --debug > debug_report.txt

# Include:
# - Python version
# - Installed packages
# - Environment variables (sanitized)
# - System info
# - Recent errors
```

### Reporting Bugs

When reporting a bug, include:

1. **AGENCY OS version:** `python aurora/cli.py --version`
2. **Python version:** `python --version`
3. **Operating system:** Windows/macOS/Linux
4. **Steps to reproduce**
5. **Expected behavior**
6. **Actual behavior**
7. **Error messages / stack traces**
8. **Debug report** (from above)

---

## FAQ

**Q: Can I use AGENCY OS without API keys?**
A: Limited functionality is available. Local embedding models work without keys, but AI interpretation requires at least one provider key.

**Q: How much does it cost to run?**
A: AGENCY OS itself is free. You pay only for AI API usage. Approximate costs:
- Image analysis: ~$0.01-0.03 per image
- Text generation: ~$0.001-0.01 per query
- Embeddings: ~$0.0001 per document

**Q: Can I use local models?**
A: Yes. ChromaDB uses local embeddings by default. For LLM tasks, you can use Ollama with local models.

**Q: How do I backup my data?**
A: Backup these directories:
- `./aurora_memory/` — Creative memory
- `./agency_os_data/` — Enterprise data
- `.env` — API keys (securely)

**Q: Can multiple users share an organization?**
A: Yes. Organizations support multiple members with role-based access control.

**Q: What file formats are supported?**
A: 9 media types: images (png, jpg, webp), video (mp4, mov), audio (mp3, wav), documents (pdf, docx), code (py, js, ts), design files (fig, sketch), 3D models (blend, fbx), and project files (aep, prproj).

**Q: How do I update AGENCY OS?**
A: Pull the latest code and reinstall dependencies:
```bash
git pull
pip install -r requirements.txt --upgrade
```

---

**For detailed guides, see:**
- [Getting Started](getting-started.md)
- [CLI Reference](cli.md)
- [Configuration](configuration.md)
- [Module Reference](../modules/index.md)