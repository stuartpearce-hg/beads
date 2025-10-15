#!/usr/bin/env python3
"""
AI agent that uses Claude Code API to perform work on beads issues.

This demonstrates how an agent can:
1. Find ready work from beads
2. Claim and execute tasks using Claude Code API
3. Discover new issues during work
4. Link discoveries back to parent tasks
5. Complete work and move on

The agent uses Claude's API to analyze tasks and generate code/solutions.
"""

import json
import os
import subprocess
import sys
from typing import Optional, Dict, Any
import anthropic


class ClaudeCodeAgent:
    """Agent that uses Claude Code API to work on beads issues."""

    def __init__(self):
        """Initialize the agent with Claude API client."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Set it with: export ANTHROPIC_API_KEY='your-api-key'"
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self.current_task = None

    def run_bd(self, *args) -> dict:
        """
        Run bd command and parse JSON output.
        
        Args:
            *args: Command arguments to pass to bd
            
        Returns:
            Parsed JSON response from bd command
        """
        cmd = ["bd"] + list(args) + ["--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.stdout.strip():
            return json.loads(result.stdout)
        return {}

    def find_ready_work(self) -> Optional[dict]:
        """
        Find the highest priority ready work.
        
        Returns:
            Dictionary containing issue details, or None if no work available
        """
        ready = self.run_bd("ready", "--limit", "1")

        if isinstance(ready, list) and len(ready) > 0:
            return ready[0]
        return None

    def claim_task(self, issue_id: str) -> dict:
        """
        Claim a task by setting status to in_progress.
        
        Args:
            issue_id: The ID of the issue to claim
            
        Returns:
            Updated issue information
        """
        print(f"📋 Claiming task: {issue_id}")
        return self.run_bd("update", issue_id, "--status", "in_progress")

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        issue_type: str = "task"
    ) -> dict:
        """
        Create a new issue.
        
        Args:
            title: Issue title
            description: Issue description
            priority: Priority level (0-4, where 0 is highest)
            issue_type: Type of issue (bug, feature, task, epic, chore)
            
        Returns:
            Created issue information
        """
        print(f"✨ Creating issue: {title}")
        args = ["create", title, "-p", str(priority), "-t", issue_type]
        if description:
            args.extend(["-d", description])
        return self.run_bd(*args)

    def link_discovery(self, discovered_id: str, parent_id: str):
        """
        Link a discovered issue back to its parent.
        
        Args:
            discovered_id: ID of the newly discovered issue
            parent_id: ID of the parent issue where it was discovered
        """
        print(f"🔗 Linking {discovered_id} ← discovered-from ← {parent_id}")
        subprocess.run(
            ["bd", "dep", "add", discovered_id, parent_id, "--type", "discovered-from"],
            check=True
        )

    def complete_task(self, issue_id: str, reason: str = "Completed"):
        """
        Mark task as complete.
        
        Args:
            issue_id: ID of the issue to complete
            reason: Reason for completion
            
        Returns:
            Updated issue information
        """
        print(f"✅ Completing task: {issue_id} - {reason}")
        return self.run_bd("close", issue_id, "--reason", reason)

    def ask_claude(self, issue: dict) -> Dict[str, Any]:
        """
        Use Claude Code API to analyze and work on an issue.
        
        Args:
            issue: Issue dictionary containing task details
            
        Returns:
            Dictionary with 'solution', 'discovered_issues' keys
        """
        issue_id = issue["id"]
        title = issue["title"]
        description = issue.get("description", "")
        issue_type = issue["issue_type"]
        priority = issue["priority"]

        prompt = f"""You are an AI coding assistant helping to work on a task.

Task ID: {issue_id}
Title: {title}
Type: {issue_type}
Priority: {priority}
Description: {description}

Please analyze this task and provide:
1. A brief solution or approach to implement it
2. Any potential issues, bugs, or related tasks you discover while analyzing this

Format your response as JSON with keys:
- "solution": Your recommended approach/implementation
- "discovered_issues": List of dicts with "title", "description", and "priority" for any issues found
"""

        print(f"\n🤖 Asking Claude about: {title} ({issue_id})")
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            print(f"💡 Claude's response received")
            
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                result = {
                    "solution": response_text,
                    "discovered_issues": []
                }
            
            return result
            
        except Exception as e:
            print(f"⚠️  Error calling Claude API: {e}")
            return {
                "solution": f"Error: {str(e)}",
                "discovered_issues": []
            }

    def work_on_issue(self, issue: dict) -> bool:
        """
        Work on an issue using Claude Code API.
        
        Args:
            issue: Issue dictionary containing task details
            
        Returns:
            True if new issues were discovered, False otherwise
        """
        issue_id = issue["id"]
        
        result = self.ask_claude(issue)
        
        print(f"\n📝 Solution approach:")
        print(f"   {result['solution'][:200]}...")
        
        discovered_count = 0
        for discovered in result.get("discovered_issues", []):
            print(f"\n💡 Discovered: {discovered.get('title', 'Unnamed issue')}")
            new_issue = self.create_issue(
                title=discovered.get("title", "Discovered issue"),
                description=discovered.get("description", ""),
                priority=discovered.get("priority", 2),
                issue_type="task"
            )
            self.link_discovery(new_issue["id"], issue_id)
            discovered_count += 1
        
        return discovered_count > 0

    def run_once(self) -> bool:
        """
        Execute one work cycle.
        
        Returns:
            True if work was found, False otherwise
        """
        # Find ready work
        issue = self.find_ready_work()

        if not issue:
            print("📭 No ready work found.")
            return False

        # Claim the task
        self.claim_task(issue["id"])

        discovered_new_work = self.work_on_issue(issue)

        # Complete the task
        self.complete_task(issue["id"], "Analyzed and completed with Claude's assistance")

        if discovered_new_work:
            print("\n🔄 New work discovered and linked. Running another cycle...")

        return True

    def run(self, max_iterations: int = 10):
        """
        Run the agent for multiple iterations.
        
        Args:
            max_iterations: Maximum number of tasks to process
        """
        print("🚀 Claude Code Agent starting...\n")
        print(f"📡 Using model: {self.model}\n")

        for i in range(max_iterations):
            print(f"\n{'='*60}")
            print(f"Iteration {i+1}/{max_iterations}")
            print(f"{'='*60}")

            if not self.run_once():
                break

        print("\n✨ Agent finished!")


def main():
    """Main entry point."""
    try:
        agent = ClaudeCodeAgent()
        agent.run()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running bd: {e}", file=sys.stderr)
        print(f"Make sure bd is installed: go install github.com/steveyegge/beads/cmd/bd@latest")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Agent interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
