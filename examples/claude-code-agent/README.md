# Claude Code Agent Example

A Python agent that uses the Anthropic Claude API to analyze and work on beads issues.

## Features

- Finds ready work using `bd ready --json`
- Claims tasks by updating status
- Uses Claude Code API to analyze tasks and suggest solutions
- Discovers new issues based on Claude's analysis
- Links discovered issues with `discovered-from` dependency
- Completes tasks and moves to the next one

## Prerequisites

- Python 3.7+
- bd installed: `go install github.com/steveyegge/beads/cmd/bd@latest`
- A beads database initialized: `bd init`
- Anthropic API key (get one at https://console.anthropic.com/)
- Python package: `pip install anthropic`

## Configuration

Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Optionally, configure the Claude model to use (defaults to claude-3-5-sonnet-20241022):

```bash
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
```

## Installation

```bash
# Install dependencies
pip install anthropic

# Make the script executable
chmod +x agent.py
```

## Usage

```bash
# Run the agent
./agent.py
```

## What It Does

1. Queries for ready work (no blocking dependencies)
2. Claims the highest priority task
3. Sends task details to Claude Code API for analysis
4. Claude analyzes the task and suggests a solution
5. Claude identifies potential issues, bugs, or related tasks
6. Creates new issues for any discoveries and links them with `discovered-from`
7. Completes the original task
8. Repeats until no ready work remains

## Example Output

```
🚀 Claude Code Agent starting...

📡 Using model: claude-3-5-sonnet-20241022

============================================================
Iteration 1/10
============================================================

📋 Claiming task: bd-1
🤖 Asking Claude about: Implement user authentication (bd-1)
💡 Claude's response received

📝 Solution approach:
   To implement user authentication, I recommend using JWT tokens with bcrypt for password hashing. Key components include...

💡 Discovered: Add unit tests for authentication endpoints
✨ Creating issue: Add unit tests for authentication endpoints
🔗 Linking bd-2 ← discovered-from ← bd-1

💡 Discovered: Security audit for authentication flow
✨ Creating issue: Security audit for authentication flow
🔗 Linking bd-3 ← discovered-from ← bd-1

✅ Completing task: bd-1 - Analyzed and completed with Claude's assistance

🔄 New work discovered and linked. Running another cycle...
```

## Integration with Real Projects

To integrate with a real project:

1. **Task Analysis**: Claude analyzes each task and provides implementation approaches
2. **Issue Discovery**: Claude identifies related tasks, potential bugs, or missing components
3. **Context Tracking**: Use issue IDs to maintain context across agent sessions
4. **State Sharing**: Export/import JSONL to share state across different environments

## Advanced Usage

```python
# Create an agent with custom model
import os
os.environ["CLAUDE_MODEL"] = "claude-3-opus-20240229"

agent = ClaudeCodeAgent()

# Customize the prompt sent to Claude
result = agent.ask_claude(issue)
print(result["solution"])
print(result["discovered_issues"])
```

## Security Best Practices

- **Never commit API keys**: Always use environment variables
- **Rotate keys regularly**: Generate new API keys periodically
- **Use .env files**: For local development, store keys in `.env` (add to `.gitignore`)
- **Use secrets management**: In production, use tools like AWS Secrets Manager or HashiCorp Vault

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Your Anthropic API key |
| `CLAUDE_MODEL` | No | `claude-3-5-sonnet-20241022` | Claude model to use |

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable is required"
Set your API key: `export ANTHROPIC_API_KEY='your-key'`

### "Error running bd"
Make sure bd is installed and in your PATH: `go install github.com/steveyegge/beads/cmd/bd@latest`

### API Rate Limits
The Anthropic API has rate limits. If you hit them, the agent will report errors. Consider:
- Reducing `max_iterations`
- Adding delays between iterations
- Upgrading your API plan

## See Also

- [../python-agent/](../python-agent/) - Simple Python agent without AI
- [../devin-agent/](../devin-agent/) - Agent that uses Devin API
- [../claude-desktop-mcp/](../claude-desktop-mcp/) - MCP server for Claude Desktop
- [Anthropic API Documentation](https://docs.anthropic.com/)

## License

MIT License - see repository root for details
