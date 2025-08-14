# Contributing to Whisper Transcription Web Service

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3)
- Python 3.8+
- Node.js (for development tools, optional)
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/whisper_transcription.git
   cd whisper_transcription
   ```

2. **Install Dependencies**
   ```bash
   # Install system dependencies
   brew install whisper-cpp ffmpeg

   # Run setup script
   ./setup.sh
   ```

3. **Start Development Server**
   ```bash
   ./run.sh
   ```

4. **Verify Installation**
   - Open http://localhost:8000
   - Test with a small audio file
   - Check browser console for errors

## 🎯 How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
- Check existing issues to avoid duplicates
- Test with the latest version
- Try with a fresh installation

**When reporting bugs, please include:**
- macOS version and chip type (M1/M2/M3)
- Browser version
- Audio file format and size
- Complete error messages
- Steps to reproduce
- Expected vs actual behavior

### Suggesting Features

**Feature requests should include:**
- Clear description of the problem it solves
- Detailed explanation of the proposed solution
- Consider how it fits with existing functionality
- Any technical constraints or considerations

### Code Contributions

**We welcome contributions for:**
- Bug fixes
- Performance improvements
- New audio format support
- UI/UX enhancements
- Accessibility improvements
- Documentation updates

## 📝 Development Guidelines

### Code Style

**Python (Backend)**
```python
# Use type hints
async def transcribe_audio(file_path: Path) -> AsyncGenerator[dict, None]:
    pass

# Follow PEP 8
# Use descriptive variable names
# Add docstrings for functions

# Use f-strings for formatting
message = f"Processing {file_name} ({file_size})"
```

**JavaScript (Frontend)**
```javascript
// Use modern ES6+ features
class TranscriptionApp {
    constructor() {
        this.fileInput = document.getElementById('fileInput');
    }

    // Use descriptive method names
    async handleFileUpload(files) {
        // Implementation
    }
}

// Use const/let, avoid var
const API_URL = '/api/upload';
let currentSession = null;
```

**HTML/CSS**
```html
<!-- Use semantic HTML -->
<main role="main">
    <section aria-labelledby="upload-heading">
        <h2 id="upload-heading">Upload Files</h2>
    </section>
</main>

<!-- Include accessibility attributes -->
<button aria-label="Start transcription" disabled>
    Process Audio
</button>
```

### Git Workflow

**Branch Naming:**
- `feature/batch-processing`
- `fix/websocket-connection`
- `docs/update-readme`

**Commit Messages:**
```
feat: add batch processing support

- Implement multi-file upload endpoint
- Add queue management for sequential processing
- Update UI for batch progress tracking

Fixes #123
```

**Pull Request Process:**
1. Create feature branch from main
2. Make changes with descriptive commits
3. Update documentation if needed
4. Test thoroughly on macOS
5. Create pull request with detailed description
6. Address review feedback promptly

### Testing

**Manual Testing Checklist:**
- [ ] Single file upload works
- [ ] Batch upload works with multiple files
- [ ] Progress updates display correctly
- [ ] Error handling works gracefully
- [ ] Accessibility features work (keyboard navigation)
- [ ] Mobile interface is responsive
- [ ] Files save to correct locations

**Automated Testing (Future):**
```bash
# Run tests (when implemented)
python -m pytest tests/

# Run linting
flake8 *.py
eslint static/app.js
```

### Performance Considerations

**Backend:**
- Async/await for I/O operations
- Proper resource cleanup
- Memory-efficient file handling
- Sequential processing to prevent overheating

**Frontend:**
- Minimal DOM manipulation
- Efficient progress updates
- Proper WebSocket handling
- Mobile-first responsive design

## 🏗️ Architecture Overview

### Key Components

```
Frontend (Vanilla JS)
├── File Upload Handler
├── WebSocket Manager
├── Progress UI Controller
└── Batch Queue Manager

Backend (FastAPI)
├── Upload Endpoints (/upload, /batch-upload)
├── WebSocket Handlers (/ws/{id})
├── Transcription Service (transcriber.py)
└── File Management (config.py)

External Dependencies
├── whisper.cpp (AI transcription)
├── ffmpeg (audio conversion)
└── Python virtual environment
```

### Key Design Decisions

- **Sequential Processing**: Prevents thermal throttling on Apple Silicon
- **Local Storage**: Files save next to originals for easy access
- **WebSocket Updates**: Real-time progress without polling
- **Vanilla JavaScript**: No build tools, keeps it simple
- **Accessibility First**: WCAG 2.1 AA compliance from the start

## 📋 Code Review Guidelines

**Reviewers should check:**
- Code follows style guidelines
- Changes include appropriate tests
- Documentation is updated
- Accessibility is maintained
- Performance impact is considered
- Error handling is robust

**Authors should:**
- Test changes thoroughly
- Update relevant documentation
- Add comments for complex logic
- Keep PRs focused and small
- Respond to feedback constructively

## 🎉 Recognition

Contributors will be:
- Listed in GitHub contributors
- Mentioned in release notes for significant contributions
- Credited in documentation for major features

## 📞 Getting Help

**For development questions:**
- Create a GitHub issue with `question` label
- Join discussions in existing issues
- Review existing code and documentation

**For quick questions:**
- Check the README.md first
- Search closed issues
- Review the changelog

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make audio transcription more accessible and private! 🎙️