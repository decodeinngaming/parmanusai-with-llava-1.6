# Contributing to ParManus

Thank you for your interest in contributing to ParManus! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/parmanus.git
   cd parmanus
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and modular

### Testing

- Write tests for new features
- Ensure existing tests pass
- Test with both GPU and CPU configurations
- Test browser automation features thoroughly

### Commit Messages

Use clear, descriptive commit messages:
```
feat: add new browser automation capability
fix: resolve model loading timeout issue
docs: update installation instructions
refactor: improve agent coordination logic
```

## Types of Contributions

### 🐛 Bug Reports

When reporting bugs, please include:
- Operating system and version
- Python version
- GPU/CPU configuration
- Steps to reproduce
- Expected vs actual behavior
- Relevant log files

### ✨ Feature Requests

For new features:
- Describe the use case
- Explain the expected behavior
- Consider implementation complexity
- Check if similar functionality exists

### 🔧 Code Contributions

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the coding guidelines
   - Add tests if applicable
   - Update documentation

3. **Test your changes**:
   ```bash
   python -m pytest tests/
   python test_browser_fallback.py
   python test_complete_workflow_new.py
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: your descriptive message"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Use a clear title and description
   - Reference any related issues
   - Include screenshots if relevant

### 📚 Documentation

Help improve documentation by:
- Fixing typos and grammar
- Adding usage examples
- Improving setup instructions
- Creating tutorials

## Project Structure

```
parmanus/
├── app/
│   ├── agent/          # Agent implementations
│   ├── tool/           # Tool definitions
│   ├── prompt/         # Prompt templates
│   └── llm.py         # LLM interface
├── config/            # Configuration examples
├── scripts/           # Utility scripts
├── tests/             # Test files
├── main.py           # Main entry point
└── requirements.txt  # Dependencies
```

## Key Areas for Contribution

### High Priority
- **Browser Automation**: Improve web scraping and navigation
- **Model Optimization**: Better GPU utilization and performance
- **Error Handling**: More robust error recovery
- **Documentation**: Usage examples and tutorials

### Medium Priority
- **New Agents**: Additional specialized agents
- **Tool Integration**: New tools and capabilities
- **Configuration**: Better config management
- **Testing**: Expanded test coverage

### Ideas Welcome
- **Multi-language Support**: Internationalization
- **UI/Web Interface**: Web-based interface
- **Plugin System**: Extensible architecture
- **Cloud Integration**: Cloud deployment options

## Technical Guidelines

### Adding New Agents

1. **Create agent class** in `app/agent/`
2. **Inherit from BaseAgent**
3. **Implement required methods**:
   - `step()`: Main execution logic
   - `think()`: Decision making
4. **Add to router** configuration
5. **Create tests**

### Adding New Tools

1. **Create tool class** in `app/tool/`
2. **Inherit from BaseTool**
3. **Implement `__call__` method**
4. **Add error handling**
5. **Update agent tool collections**

### Model Integration

1. **Update LLM interface** if needed
2. **Add model-specific configurations**
3. **Test with different model sizes**
4. **Document model requirements**

## Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Ask questions** when unsure
- **Share knowledge** and experiences
- **Give constructive feedback**

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/parsu/parmanus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/parsu/parmanus/discussions)
- **Email**: [Contact maintainer]

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to ParManus! 🚀

---

**Created by Parsu** | Building the future of AI agents
