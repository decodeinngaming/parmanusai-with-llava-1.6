# Files to Include in GitHub Repository

## Core Application Files ✅
- main.py
- requirements.txt
- setup.py

## Application Code ✅
- app/ (entire directory)
  - agent/
  - tool/
  - prompt/
  - mcp/
  - flow/
  - voice/
  - sandbox/
  - *.py files (llm.py, config.py, etc.)

## Configuration ✅
- config/config.example-llava.toml (rename to config.example.toml)
- config/config.example-model-*.toml (keep as examples)

## Documentation ✅
- README_NEW.md (rename to README.md)
- CONTRIBUTING.md
- LICENSE
- CODE_OF_CONDUCT.md

## Scripts ✅
- scripts_new/download_model.py (rename to scripts/)

## Git Configuration ✅
- .gitignore_new (rename to .gitignore)
- .gitattributes

## Assets ✅
- assets/ (if contains logos/images needed for README)

---

## Files to EXCLUDE ❌

### Large Model Files
- models/ (entire directory)
- *.gguf files
- *.bin files
- *.safetensors files

### Test Files (Development Only)
- test_*.py
- debug_*.py
- simple_*.py
- verify_*.py
- validate_*.py

### Temporary/Generated Files
- logs/
- sessions/
- workspace/
- .venv/
- __pycache__/

### Backup Files
- *.backup
- *.bak
- main.py.backup_*
- *_optimized.py

### Documentation (Development)
- optimization_docs/
- final_fixes_*.md
- *_summary.md
- *_analysis.md
- issues_analysis.md
- MODEL_CONFIG.md
- NEWS_TRAINING_GUIDE.md

### Development Scripts
- fix_*.py
- run_flow.py
- run_mcp.py
- run_mcp_server.py
- llava_*.py

### PDF Files
- *.pdf

### IDE/Editor Files
- .vscode/ (keep basic settings if needed)
- .idea/

### Build/Distribution
- build/
- dist/
- *.egg-info/

### Docker (Optional - can be included if desired)
- docker-compose.yml
- Dockerfile
- docker_gpu_guide.md

### Examples (Optional - can be included)
- examples/ (large benchmark data should be excluded)

### Language Variants
- README_ja.md
- README_ko.md
- README_zh.md

### PowerShell Scripts
- *.ps1
