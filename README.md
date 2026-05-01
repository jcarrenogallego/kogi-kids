# Kogi Kids - AI Video Generation for Children

AI-powered children's video generation from stories using multi-agent orchestration and MidJourney.

## 🎯 Purpose

Transform story text into short-form videos for children ages 2-10 by orchestrating specialized AI agents that handle:
- Character design and consistency
- Age-appropriate dialogue writing
- Scene and set design
- Cinematography and shot composition
- Script assembly
- MidJourney prompt generation

## 🏗️ Architecture

Multi-agent orchestration with sequential phases and human validation gates:

```
Story Text Input
    ↓
Character Agent → [Human Review] → Character Descriptions
    ↓
Dialogue Agent → [Human Review] → Dialogue Script
    ↓
Scenography Agent → [Human Review] → Scene Descriptions
    ↓
Cinematography Agent → [Human Review] → Shot List
    ↓
Scriptwriter Agent → [Human Review] → Full Script
    ↓
Prompt Engineer Agent → [Human Review] → MidJourney Prompts
    ↓
Video Prompts Output
```

## 🛠️ Tech Stack (Proposed)

- **Python 3.11+**: LLM workflows, prompt engineering
- **LangGraph**: Multi-agent orchestration with human-in-the-loop
- **FastAPI**: REST API for story input, progress streaming
- **PostgreSQL**: State persistence for long-running workflows
- **MidJourney**: AI image generation via prompts

## 📚 Skills & Capabilities

### Installed Skills (7)
- **character-design-sheet**: Turnaround views, expression sheets, visual consistency
- **midjourney-prompt-engineering**: MJ V7 prompts, style references, scoring
- **kids-book-writer**: Age-appropriate content for ages 2-9
- **storytelling**: SCAR framework, narrative structure
- **mockumentary-screenplay**: Fountain format, dialogue, scene description
- **prompt-engineering-patterns**: Few-shot, chain-of-thought, structured outputs
- **workflow-orchestration-patterns**: Temporal workflows, saga patterns, human-in-the-loop

### Architecture Skills (19)
- LangChain/LangGraph fundamentals
- Clean Architecture, DDD, Architecture Patterns
- FastAPI, Python testing, Docker
- Git workflows, PR/issue creation
- And more...

See `.atl/skill-registry.md` for complete catalog.

## 🚀 Current Status

**Phase**: Initialization & Planning
- ✅ SDD workflow initialized (Engram mode)
- ✅ Skill registry created with 26+ skills
- ✅ Domain-specific skills installed (character design, MidJourney, kids content)
- ⏳ Testing infrastructure (pending: pytest, ruff, mypy)
- ⏳ Stack implementation (pending: Python setup)
- ⏳ Agent architecture exploration (next phase)

## 📋 Next Steps

1. **Explore Architecture**: `/sdd-explore multi-agent-video-pipeline`
2. **Install Testing**: `pip install pytest pytest-asyncio pytest-cov ruff mypy`
3. **Create Missing Skills**: Cinematography & Scenography (if needed)
4. **Start Implementation**: `/sdd-new character-agent-implementation`

## 🔧 Development Setup

```bash
# Clone repository (when remote exists)
git clone <repository-url>
cd kogi-kids

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt

# Run tests (when tests exist)
pytest --cov=src --cov-report=term-missing
```

## 📖 Documentation

- **Skill Registry**: `.atl/skill-registry.md`
- **Project Context**: Stored in Engram (topic: `sdd-init/kogi-kids`)
- **Testing Capabilities**: Stored in Engram (topic: `sdd/kogi-kids/testing-capabilities`)

## 🤝 Contributing

This project uses Spec-Driven Development (SDD) workflow:
- All changes go through proposal → specs → design → tasks → implementation → verification
- Human validation required at each phase transition
- Strict TDD Mode (when enabled): tests before implementation

## 📄 License

TBD

## 🙏 Acknowledgments

- Skills ecosystem contributors
- LangGraph/LangChain teams
- MidJourney community
