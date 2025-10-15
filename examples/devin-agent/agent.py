#!/usr/bin/env python3
"""
AI agent that uses Devin API to perform work on beads issues.

This demonstrates how an agent can:
1. Find ready work from beads
2. Claim and execute tasks using Devin API
3. Discover new issues during work
4. Link discoveries back to parent tasks
5. Complete work and move on

The agent uses Devin's API to execute complex coding tasks.
"""

import json
import os
import subprocess
import sys
import time
from typing import Optional, Dict, Any
from pathlib import Path
import requests

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class DevinAgent:
    """Agent that uses Devin API to work on beads issues."""

    def __init__(self):
        """Initialize the agent with Devin API client."""
        self.api_key = os.environ.get("DEVIN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEVIN_API_KEY environment variable is required. "
                "Set it with: export DEVIN_API_KEY='your-api-key'"
            )
        
        self.base_url = os.environ.get("DEVIN_API_URL", "https://api.devin.ai/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
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

    def create_devin_session(self, issue: dict) -> Dict[str, Any]:
        """
        Create a Devin session to work on an issue.
        
        Args:
            issue: Issue dictionary containing task details
            
        Returns:
            Dictionary with session information
        """
        issue_id = issue["id"]
        title = issue["title"]
        description = issue.get("description", "")
        issue_type = issue["issue_type"]
        priority = issue["priority"]

        prompt = f"""Work on this task:

Task ID: {issue_id}
Title: {title}
Type: {issue_type}
Priority: {priority}
Description: {description}

Please analyze this task, implement a solution, and report:
1. What you implemented
2. Any issues, bugs, or related tasks you discovered
3. Test results
"""

        print(f"\n🤖 Creating Devin session for: {title} ({issue_id})")
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "metadata": {
                        "beads_issue_id": issue_id,
                        "beads_issue_title": title
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            session_data = response.json()
            session_id = session_data.get("session_id")
            
            print(f"📡 Devin session created: {session_id}")
            return {
                "session_id": session_id,
                "status": "created",
                "url": session_data.get("session_url")
            }
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error creating Devin session: {e}")
            return {
                "session_id": None,
                "status": "error",
                "error": str(e)
            }

    def poll_session_status(self, session_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """
        Poll Devin session until completion.
        
        Args:
            session_id: ID of the Devin session
            max_wait: Maximum time to wait in seconds
            
        Returns:
            Dictionary with session results
        """
        print(f"⏳ Waiting for Devin to complete work...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/sessions/{session_id}",
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                
                session_data = response.json()
                status = session_data.get("status")
                
                if status in ["completed", "failed", "cancelled"]:
                    print(f"✓ Devin session {status}")
                    return {
                        "status": status,
                        "result": session_data.get("result", {}),
                        "session_data": session_data
                    }
                
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Error polling session: {e}")
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        print(f"⏱️  Session timed out after {max_wait} seconds")
        return {
            "status": "timeout",
            "error": f"Session did not complete within {max_wait} seconds"
        }

    def extract_discovered_issues(self, session_result: Dict[str, Any]) -> list:
        """
        Extract discovered issues from Devin's session results.
        
        Args:
            session_result: Results from Devin session
            
        Returns:
            List of discovered issue dictionaries
        """
        discovered = []
        
        result_data = session_result.get("result", {})
        output = result_data.get("output", "")
        
        keywords = ["bug", "issue", "todo", "fix", "problem"]
        
        for keyword in keywords:
            if keyword.lower() in output.lower():
                discovered.append({
                    "title": f"Follow-up: {keyword.title()} discovered during implementation",
                    "description": f"Devin found a {keyword} while working. Check session output for details.",
                    "priority": 2
                })
                break  # Only create one follow-up issue per session
        
        return discovered

    def work_on_issue(self, issue: dict) -> bool:
        """
        Work on an issue using Devin API.
        
        Args:
            issue: Issue dictionary containing task details
            
        Returns:
            True if new issues were discovered, False otherwise
        """
        issue_id = issue["id"]
        
        session = self.create_devin_session(issue)
        
        if not session.get("session_id"):
            print(f"⚠️  Failed to create Devin session")
            return False
        
        if session.get("url"):
            print(f"🔗 Session URL: {session['url']}")
        
        result = self.poll_session_status(session["session_id"])
        
        if result["status"] == "completed":
            print(f"✓ Devin completed the work successfully")
            
            discovered_issues = self.extract_discovered_issues(result)
            
            for discovered in discovered_issues:
                print(f"\n💡 Discovered: {discovered['title']}")
                new_issue = self.create_issue(
                    title=discovered["title"],
                    description=discovered["description"],
                    priority=discovered["priority"],
                    issue_type="task"
                )
                self.link_discovery(new_issue["id"], issue_id)
            
            return len(discovered_issues) > 0
        else:
            print(f"⚠️  Devin session did not complete successfully: {result['status']}")
            return False

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
        self.complete_task(issue["id"], "Completed with Devin's assistance")

        if discovered_new_work:
            print("\n🔄 New work discovered and linked. Running another cycle...")

        return True

    def run(self, max_iterations: int = 5):
        """
        Run the agent for multiple iterations.
        
        Note: Devin sessions can take several minutes, so default iterations is lower.
        
        Args:
            max_iterations: Maximum number of tasks to process
        """
        print("🚀 Devin Agent starting...\n")
        print(f"📡 Using Devin API at: {self.base_url}\n")

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
        agent = DevinAgent()
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
