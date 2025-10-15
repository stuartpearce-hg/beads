# Devin Agent Example

A Python agent that uses the Devin API to autonomously work on beads issues.

## Features

- Finds ready work using `bd ready --json`
- Claims tasks by updating status
- Creates Devin sessions to execute coding tasks
- Polls Devin sessions for completion
- Discovers new issues based on Devin's work
- Links discovered issues with `discovered-from` dependency
- Completes tasks and moves to the next one

## Prerequisites

- Python 3.7+
- bd installed: `go install github.com/steveyegge/beads/cmd/bd@latest`
- A beads database initialized: `bd init`
- Devin API key (contact Devin team for access)
- Python package: `pip install requests`

## Configuration

### Using Environment Variables

Set your Devin API key as an environment variable:

```bash
export DEVIN_API_KEY='your-api-key-here'
```

Optionally, configure the Devin API URL (defaults to https://api.devin.ai/v1):

```bash
export DEVIN_API_URL='https://api.devin.ai/v1'
```

### Using .env File (Recommended)

For easier configuration, copy the example environment file and update it with your credentials:

```bash
cp .env.example .env
# Edit .env with your API key
```

The `.env` file is gitignored by default to prevent accidentally committing secrets.

## Installation

```bash
# Install dependencies
pip install requests

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
3. Creates a Devin session with task details
4. Devin autonomously works on the task (coding, testing, etc.)
5. Agent polls the session until Devin completes the work
6. Extracts any discovered issues from Devin's output
7. Creates new issues for discoveries and links them with `discovered-from`
8. Completes the original task
9. Repeats until no ready work remains

## Example Output

```
🚀 Devin Agent starting...

📡 Using Devin API at: https://api.devin.ai/v1

============================================================
Iteration 1/5
============================================================

📋 Claiming task: bd-1

🤖 Creating Devin session for: Implement user authentication (bd-1)
📡 Devin session created: devin-session-abc123
🔗 Session URL: https://app.devin.ai/sessions/devin-session-abc123

⏳ Waiting for Devin to complete work...
✓ Devin session completed

💡 Discovered: Follow-up: Bug discovered during implementation
✨ Creating issue: Follow-up: Bug discovered during implementation
🔗 Linking bd-2 ← discovered-from ← bd-1

✅ Completing task: bd-1 - Completed with Devin's assistance

🔄 New work discovered and linked. Running another cycle...
```

## How It Works

### Session Creation

The agent creates a Devin session by sending a POST request to `/v1/sessions` with:
- A detailed prompt including the task information
- Metadata for tracking (beads issue ID and title)

### Polling

The agent polls the session status every 10 seconds by calling GET `/v1/sessions/{session_id}` until:
- Status is "completed" (success)
- Status is "failed" or "cancelled" (failure)
- Timeout is reached (default 300 seconds)

### Discovery Extraction

When Devin completes work, the agent analyzes the output for:
- Mentions of bugs or issues discovered
- TODO items identified
- Problems that need follow-up

These are automatically converted to new beads issues.

## Integration with Real Projects

To integrate with a real project:

1. **Autonomous Work**: Devin can clone repos, write code, run tests, and create PRs
2. **Long-Running Tasks**: Devin sessions can run for several minutes to hours
3. **Context Tracking**: Use issue IDs to track which Devin sessions worked on what
4. **State Sharing**: Export/import JSONL to share state across different environments

## Advanced Usage

```python
# Create an agent with custom timeout
agent = DevinAgent()

# Create a session and get the session ID
session = agent.create_devin_session(issue)
session_id = session["session_id"]

# Poll with custom timeout (default is 300 seconds)
result = agent.poll_session_status(session_id, max_wait=600)

# Access session URL for monitoring
print(f"Monitor at: {session['url']}")
```

## Workflow Comparison

| Feature | Python Agent | Claude Code Agent | Devin Agent |
|---------|-------------|-------------------|-------------|
| Response Time | Instant | ~1-5 seconds | Minutes to hours |
| Autonomy | Simulated | Analysis only | Full autonomy |
| Code Execution | No | No | Yes |
| Repository Access | No | No | Yes |
| API Cost | Free | Pay per token | Pay per session |
| Best For | Testing | Quick analysis | Real implementation |

## Security Best Practices

- **Never commit API keys**: Always use environment variables
- **Rotate keys regularly**: Generate new API keys periodically
- **Use .env files**: For local development, store keys in `.env` (add to `.gitignore`)
- **Use secrets management**: In production, use tools like AWS Secrets Manager or HashiCorp Vault
- **Monitor sessions**: Watch Devin sessions to ensure they're working on intended tasks
- **Review code**: Always review code generated by Devin before merging

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEVIN_API_KEY` | Yes | - | Your Devin API key |
| `DEVIN_API_URL` | No | `https://api.devin.ai/v1` | Devin API base URL |

## Troubleshooting

### "DEVIN_API_KEY environment variable is required"
Set your API key: `export DEVIN_API_KEY='your-key'`

### "Error running bd"
Make sure bd is installed and in your PATH: `go install github.com/steveyegge/beads/cmd/bd@latest`

### Session Timeouts
Devin sessions can take a while. If you're hitting timeouts:
- Increase `max_wait` parameter in `poll_session_status()`
- Break larger tasks into smaller subtasks
- Monitor sessions via the session URL

### API Rate Limits
The Devin API has rate limits. If you hit them:
- Reduce `max_iterations` in the agent
- Add delays between session creations
- Contact Devin team to increase limits

## See Also

- [../python-agent/](../python-agent/) - Simple Python agent without AI
- [../claude-code-agent/](../claude-code-agent/) - Agent that uses Claude Code API
- [../claude-desktop-mcp/](../claude-desktop-mcp/) - MCP server for Claude Desktop
- [Devin Documentation](https://docs.devin.ai/)

## License

MIT License - see repository root for details
