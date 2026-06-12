# Contributing to CODEFORGE

Thank you for your interest in contributing!

## How to contribute

### Report a bug
Open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

### Request a feature
Open an issue describing:
- The use case
- What you'd expect it to do
- Any alternatives you've considered

### Submit a pull request

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run the test suite: `python3 tests/test_suite.py`
5. Ensure all 20 tests pass
6. Open a PR with a clear description of what changed and why

## Development setup

```bash
git clone https://github.com/vignesh2027/CODEFORGE.git
cd CODEFORGE
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
python3 tests/test_suite.py  # verify setup
```

## Adding a new agent

1. Create `agents/your_agent.py` following the pattern of existing agents
2. Add state fields to `state/schema.py` if needed
3. Register the node in `graph/workflow.py`
4. Add routing logic if the agent introduces conditional edges
5. Write at least one unit test in `tests/test_suite.py`

## Adding a new tool

1. Create `tools/your_tool.py`
2. Import and bind it in the Coder agent (`agents/coder.py`) or a new agent
3. Add a test that verifies the tool works end-to-end

## Code style

- Python 3.10+
- No type stubs required but type hints are encouraged
- Keep agent files focused — one responsibility per agent
- No global state outside of `AgentState`

## Questions

Open an issue or reach out via GitHub.
