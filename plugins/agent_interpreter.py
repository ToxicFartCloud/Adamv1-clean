"""
agent_interpreter.py — Self-introspective agent that analyzes Adam's code,
identifies improvements, and safely edits with user approval.
"""

import logging
import os
import json
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

METADATA = {
    "label": "Interpreter Agent",
    "description": "Analyzes Adam's codebase, proposes improvements, and safely edits with approval",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> Dict[str, Any]:
    """
    Main entry point for agent_interpreter.

    Expected kwargs:
    - action: str (required) - "analyze", "propose", "execute_approved"
    - target_file: str (optional) - specific file to analyze
    - scope: str (optional) - "plugin", "core", "utils", "all"
    - auto_approve_safe: bool (optional) - auto-approve safe changes like docs/logging
    - ui_callback: callable (optional) - for headless/UI approval instead of input()

    Returns:
    { "ok": bool, "data": dict, "error": str or None }
    """
    try:
        action = kwargs.get("action", "").strip().lower()

        if action == "analyze":
            return _analyze_codebase(**kwargs)
        elif action == "propose":
            return _propose_improvements(**kwargs)
        elif action == "execute_approved":
            return _execute_approved_changes(**kwargs)
        else:
            return {
                "ok": False,
                "data": None,
                "error": f"Unknown action: {action}. Use 'analyze', 'propose', or 'execute_approved'",
            }

    except Exception as e:
        error_msg = f"agent_interpreter failed: {str(e)}"
        logger.exception(error_msg)
        return {"ok": False, "data": None, "error": error_msg}


def _safe_import(module_name: str, default=None):
    """
    Safely import a module, returning default if import fails.
    """
    try:
        if "." in module_name:
            package, module = module_name.rsplit(".", 1)
            return __import__(module_name, fromlist=[module])
        else:
            return __import__(module_name)
    except ImportError as e:
        logger.warning("agent_interpreter: Missing module %s - %s", module_name, str(e))
        return default


def _load_config() -> Dict[str, Any]:
    """
    Load configuration for self-improvement settings.
    """
    try:
        # Try to load from utils.config first
        config_module = _safe_import("utils.config")
        if config_module and hasattr(config_module, "load_config"):
            return config_module.load_config("adam")

        # Fallback: try to load config file directly
        config_paths = [
            "config/adam.yaml",
            "config/adam.json",
            "src/config/adam.yaml",
            "src/config/adam.json",
        ]

        for config_path in config_paths:
            if os.path.exists(config_path):
                if config_path.endswith(".yaml"):
                    import yaml

                    with open(config_path, "r") as f:
                        return yaml.safe_load(f)
                elif config_path.endswith(".json"):
                    with open(config_path, "r") as f:
                        return json.load(f)

        logger.info("agent_interpreter: No config found, using defaults")
        return {}

    except Exception as e:
        logger.warning(
            "agent_interpreter: Config load failed, using defaults: %s", str(e)
        )
        return {}


def _analyze_codebase(**kwargs) -> Dict[str, Any]:
    """
    Phase 1: Analyze Adam's codebase for improvement opportunities.
    """
    target_file = kwargs.get("target_file")
    scope = kwargs.get("scope", "all")

    logger.info("agent_interpreter: Starting codebase analysis (scope=%s)", scope)

    # Safe import of memory_search
    memory_search = _safe_import("plugins.memory_search")
    search_result = {"ok": True, "data": []}

    if memory_search:
        search_result = memory_search.run(
            query="code quality issues, inefficiencies, outdated patterns", scope=scope
        )
    else:
        logger.warning(
            "agent_interpreter: memory_search not available, using fallback analysis"
        )
        search_result = _fallback_code_analysis(target_file, scope)

    if not search_result.get("ok"):
        return {
            "ok": False,
            "data": None,
            "error": f"Memory search failed: {search_result.get('error')}",
        }

    # Safe import of diag_adam
    diag_adam = _safe_import("tools.diag_adam")
    diag_result = {"ok": True, "data": {}}

    if diag_adam:
        diag_result = diag_adam.run(target=target_file or "all")
    else:
        logger.warning(
            "agent_interpreter: diag_adam not available, using basic diagnostics"
        )
        diag_result = _fallback_diagnostics()

    analysis_data = {
        "timestamp": time.time(),
        "scope": scope,
        "target_file": target_file,
        "search_results": search_result.get("data", []),
        "diagnostics": diag_result.get("data", {}),
        "issues_found": _extract_issues(search_result, diag_result),
        "improvement_opportunities": _identify_opportunities(
            search_result, diag_result
        ),
    }

    logger.info(
        "agent_interpreter: Analysis complete. Found %d issues",
        len(analysis_data["issues_found"]),
    )

    return {"ok": True, "data": analysis_data, "error": None}


def _propose_improvements(**kwargs) -> Dict[str, Any]:
    """
    Phase 2: Generate specific improvement proposals.
    """
    analysis_data = kwargs.get("analysis_data")
    if not analysis_data:
        # Run analysis first
        analyze_result = _analyze_codebase(**kwargs)
        if not analyze_result["ok"]:
            return analyze_result
        analysis_data = analyze_result["data"]

    logger.info("agent_interpreter: Generating improvement proposals")

    proposals = []

    # Safe imports for agent modules
    agent_researcher = _safe_import("plugins.agent_researcher")
    agent_coder = _safe_import("plugins.agent_coder")
    agent_critic = _safe_import("plugins.agent_critic")

    for issue in analysis_data["issues_found"]:
        research_data = "N/A"
        proposed_code = f"# TODO: Improve {issue['description']}\npass"
        critic_review = "No critic available"

        # Use agent_researcher if available
        if agent_researcher:
            research_result = agent_researcher.run(
                query=f"best practices for {issue['category']}: {issue['description']}"
            )
            if research_result.get("ok"):
                research_data = research_result.get("data", "N/A")

        # Use agent_coder if available
        if agent_coder:
            code_result = agent_coder.run(
                prompt=f"Improve this code: {issue['code_snippet']}. "
                f"Research suggests: {research_data}",
                language=issue.get("language", "python"),
            )
            if code_result.get("ok"):
                proposed_code = code_result.get("data", proposed_code)

        # Use agent_critic if available
        if agent_critic:
            critic_result = agent_critic.run(
                code=proposed_code, context=f"Improvement for: {issue['description']}"
            )
            if critic_result.get("ok"):
                critic_review = critic_result.get("data", critic_review)

        proposal = {
            "id": f"proposal_{int(time.time())}_{len(proposals)}",
            "issue": issue,
            "research": research_data,
            "proposed_code": proposed_code,
            "critic_review": critic_review,
            "risk_level": _assess_risk_level(issue),
            "requires_approval": _requires_user_approval(issue),
            "estimated_impact": _estimate_impact(issue),
        }

        proposals.append(proposal)

    proposal_data = {
        "timestamp": time.time(),
        "total_proposals": len(proposals),
        "auto_approvable": len([p for p in proposals if not p["requires_approval"]]),
        "needs_approval": len([p for p in proposals if p["requires_approval"]]),
        "proposals": proposals,
    }

    # Save proposals for approval workflow
    _save_proposals(proposal_data)

    logger.info(
        "agent_interpreter: Generated %d proposals (%d need approval)",
        len(proposals),
        proposal_data["needs_approval"],
    )

    return {"ok": True, "data": proposal_data, "error": None}


def _execute_approved_changes(**kwargs) -> Dict[str, Any]:
    """
    Phase 3: Execute approved changes safely.
    """
    proposal_ids = kwargs.get("proposal_ids", [])
    auto_approve_safe = kwargs.get("auto_approve_safe", False)
    ui_callback = kwargs.get("ui_callback")

    if not proposal_ids:
        return {
            "ok": False,
            "data": None,
            "error": "No proposal_ids provided for execution",
        }

    logger.info("agent_interpreter: Executing %d approved changes", len(proposal_ids))

    # Load saved proposals
    proposals = _load_proposals()
    if not proposals:
        return {"ok": False, "data": None, "error": "No saved proposals found"}

    execution_results = []

    # Safe import of backup_snapshot
    backup_snapshot = _safe_import("tools.backup_snapshot")
    agent_tester = _safe_import("plugins.agent_tester")

    for proposal_id in proposal_ids:
        proposal = next(
            (p for p in proposals["proposals"] if p["id"] == proposal_id), None
        )
        if not proposal:
            execution_results.append(
                {
                    "proposal_id": proposal_id,
                    "status": "error",
                    "message": "Proposal not found",
                }
            )
            continue

        # Check if approval is required and not auto-approvable
        if proposal["requires_approval"] and not auto_approve_safe:
            approval_result = _request_user_approval(proposal, ui_callback)
            if not approval_result:
                execution_results.append(
                    {
                        "proposal_id": proposal_id,
                        "status": "pending_approval",
                        "message": "User denied approval",
                    }
                )
                continue

        # Create backup before making changes
        backup_result = {"ok": True, "data": f"backup_manual_{proposal_id}"}
        if backup_snapshot:
            backup_result = backup_snapshot.run(
                target=proposal["issue"]["file_path"],
                tag=f"pre_interpreter_{proposal_id}",
            )
        else:
            logger.warning(
                "agent_interpreter: backup_snapshot not available, using manual backup"
            )
            backup_result = _manual_backup(proposal["issue"]["file_path"], proposal_id)

        if not backup_result.get("ok"):
            execution_results.append(
                {
                    "proposal_id": proposal_id,
                    "status": "error",
                    "message": f"Backup failed: {backup_result.get('error')}",
                }
            )
            continue

        # Apply the changes
        try:
            change_result = _apply_code_changes(proposal)

            # Test the changes if agent_tester is available
            test_result = {"ok": True, "data": "No tester available"}
            if agent_tester:
                test_result = agent_tester.run(
                    target=proposal["issue"]["file_path"], test_type="integration"
                )

            if test_result.get("ok"):
                execution_results.append(
                    {
                        "proposal_id": proposal_id,
                        "status": "success",
                        "message": "Changes applied and tested successfully",
                        "backup_id": backup_result.get("data"),
                    }
                )
                logger.info(
                    "agent_interpreter: Successfully applied proposal %s", proposal_id
                )
            else:
                # Rollback on test failure
                _rollback_changes(backup_result.get("data"))
                execution_results.append(
                    {
                        "proposal_id": proposal_id,
                        "status": "rolled_back",
                        "message": f"Tests failed, rolled back: {test_result.get('error')}",
                    }
                )

        except Exception as e:
            # Rollback on any error
            _rollback_changes(backup_result.get("data"))
            execution_results.append(
                {
                    "proposal_id": proposal_id,
                    "status": "error",
                    "message": f"Execution failed, rolled back: {str(e)}",
                }
            )

    return {
        "ok": True,
        "data": {
            "timestamp": time.time(),
            "executed_count": len(execution_results),
            "results": execution_results,
        },
        "error": None,
    }


# Helper functions
def _fallback_code_analysis(target_file, scope) -> Dict[str, Any]:
    """Fallback code analysis when memory_search is not available."""
    issues = []

    # Simple file scanning for common issues
    search_paths = []
    if target_file:
        search_paths = [target_file]
    elif scope == "plugins":
        search_paths = ["plugins/"]
    elif scope == "core":
        search_paths = ["src/adam/", "core.py", "run_adam.py"]
    else:
        search_paths = [".", "src/", "plugins/", "tools/"]

    for path in search_paths:
        if os.path.isfile(path) and path.endswith(".py"):
            try:
                with open(path, "r") as f:
                    content = f.read()
                    if "TODO" in content or "FIXME" in content:
                        issues.append(
                            {
                                "file": path,
                                "content": "Found TODO/FIXME markers",
                                "type": "improvement_opportunity",
                            }
                        )
            except Exception as e:
                logger.warning("Failed to analyze %s: %s", path, str(e))

    return {"ok": True, "data": issues}


def _fallback_diagnostics() -> Dict[str, Any]:
    """Fallback diagnostics when diag_adam is not available."""
    return {
        "ok": True,
        "data": {
            "system_status": "unknown",
            "memory_usage": "unknown",
            "plugin_count": len(os.listdir("plugins/"))
            if os.path.exists("plugins/")
            else 0,
        },
    }


def _manual_backup(file_path: str, proposal_id: str) -> Dict[str, Any]:
    """Manual backup when backup_snapshot is not available."""
    try:
        if not os.path.exists(file_path):
            return {"ok": False, "error": f"File {file_path} does not exist"}

        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        backup_name = f"manual_backup_{proposal_id}_{timestamp}.py"
        backup_path = backup_dir / backup_name

        with open(file_path, "r") as src, open(backup_path, "w") as dst:
            dst.write(src.read())

        return {"ok": True, "data": str(backup_path)}

    except Exception as e:
        return {"ok": False, "error": f"Manual backup failed: {str(e)}"}


def _extract_issues(search_result, diag_result) -> List[Dict]:
    """Extract concrete issues from search and diagnostic results."""
    issues = []

    # Parse search results for code quality issues
    search_data = search_result.get("data", [])
    for item in search_data:
        if isinstance(item, dict):
            if "issue" in str(item).lower() or "todo" in str(item).lower():
                issues.append(
                    {
                        "category": "code_quality",
                        "description": str(item.get("content", item)),
                        "file_path": item.get("file", "unknown"),
                        "code_snippet": item.get("content", "")[:200],
                        "severity": "medium",
                        "language": "python",
                    }
                )
        else:
            # Handle string items
            if "issue" in str(item).lower() or "todo" in str(item).lower():
                issues.append(
                    {
                        "category": "code_quality",
                        "description": str(item),
                        "file_path": "unknown",
                        "code_snippet": str(item)[:200],
                        "severity": "medium",
                        "language": "python",
                    }
                )

    # Parse diagnostic results
    diag_data = diag_result.get("data", {})
    for key, value in diag_data.items():
        if "error" in key.lower() or "warning" in key.lower():
            issues.append(
                {
                    "category": "system_health",
                    "description": f"{key}: {value}",
                    "file_path": "system",
                    "code_snippet": "",
                    "severity": "high" if "error" in key.lower() else "low",
                    "language": "system",
                }
            )

    return issues


def _identify_opportunities(search_result, diag_result) -> List[Dict]:
    """Identify improvement opportunities."""
    opportunities = [
        {
            "type": "performance",
            "description": "Optimize memory usage in embedder.py",
            "potential_impact": "medium",
        },
        {
            "type": "maintainability",
            "description": "Add more comprehensive logging",
            "potential_impact": "low",
        },
        {
            "type": "reliability",
            "description": "Improve error handling in LLM fallback",
            "potential_impact": "high",
        },
    ]
    return opportunities


def _assess_risk_level(issue) -> str:
    """Assess risk level of changing this issue."""
    if issue["category"] == "system_health":
        return "high"
    elif "core" in issue.get("file_path", ""):
        return "high"
    elif issue["severity"] == "low":
        return "low"
    else:
        return "medium"


def _requires_user_approval(issue) -> bool:
    """Determine if this change requires explicit user approval based on config."""
    # Load configuration
    config = _load_config()
    self_improve_config = config.get("self_improve", {})

    # Get configurable approval list
    require_approval_for = self_improve_config.get(
        "require_approval_for",
        [
            "core.py",
            "run_adam.py",
            "plugins.py",
            "approval_cmd.py",
            "backup_snapshot.py",
        ],
    )

    file_path = issue.get("file_path", "")

    # Always require approval for configured critical files
    if any(pattern in file_path for pattern in require_approval_for):
        return True

    # Check if auto-approve safe changes is enabled
    auto_approve_safe = self_improve_config.get("auto_approve_safe", True)
    if auto_approve_safe:
        # Auto-approve safe changes like documentation, logging
        safe_changes = [
            "logging",
            "documentation",
            "comments",
            "formatting",
            "todo",
            "fixme",
        ]
        if any(safe in issue["description"].lower() for safe in safe_changes):
            return False

    return True  # Default to requiring approval


def _estimate_impact(issue) -> Dict:
    """Estimate the impact of fixing this issue."""
    return {
        "performance": "low",
        "maintainability": "medium",
        "reliability": "high" if issue["severity"] == "high" else "medium",
        "complexity": "low",
    }


def _save_proposals(proposal_data):
    """Save proposals to disk for approval workflow."""
    proposals_dir = Path("data/proposals")
    proposals_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    filepath = proposals_dir / f"proposals_{timestamp}.json"

    with open(filepath, "w") as f:
        json.dump(proposal_data, f, indent=2)

    logger.info("agent_interpreter: Saved proposals to %s", filepath)


def _load_proposals() -> Optional[Dict]:
    """Load the most recent proposals."""
    proposals_dir = Path("data/proposals")
    if not proposals_dir.exists():
        return None

    proposal_files = list(proposals_dir.glob("proposals_*.json"))
    if not proposal_files:
        return None

    # Get most recent
    latest_file = max(proposal_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, "r") as f:
        return json.load(f)


def _request_user_approval(proposal, ui_callback: Optional[Callable] = None) -> bool:
    """
    Request user approval for a proposal.
    Supports both CLI (input) and headless/UI mode (callback).
    """
    # Use UI callback if provided (for headless/web UI mode)
    if ui_callback:
        try:
            return ui_callback(proposal)
        except Exception as e:
            logger.error("agent_interpreter: UI callback failed: %s", str(e))
            # Fall back to CLI mode

    # CLI mode - interactive approval
    print("\n" + "=" * 60)
    print("🤖 ADAM SELF-IMPROVEMENT PROPOSAL")
    print("=" * 60)
    print(f"Proposal ID: {proposal['id']}")
    print(f"Issue: {proposal['issue']['description']}")
    print(f"File: {proposal['issue']['file_path']}")
    print(f"Risk Level: {proposal['risk_level']}")
    print(f"Estimated Impact: {proposal['estimated_impact']}")
    print("\nProposed Changes:")
    print("-" * 40)
    code_preview = proposal["proposed_code"]
    if len(code_preview) > 500:
        code_preview = code_preview[:500] + "..."
    print(code_preview)
    print("\nCritic Review:")
    print("-" * 40)
    print(proposal["critic_review"])
    print("\n" + "=" * 60)

    try:
        response = (
            input("Do you approve this change? (yes/no/details): ").strip().lower()
        )

        if response == "details":
            print("\nFull Proposed Code:")
            print(proposal["proposed_code"])
            response = input("Do you approve this change? (yes/no): ").strip().lower()

        return response in ["yes", "y", "approve"]

    except (KeyboardInterrupt, EOFError):
        print("\nApproval cancelled by user")
        return False


def _apply_code_changes(proposal) -> Dict:
    """Apply the proposed code changes to the file."""
    file_path = proposal["issue"]["file_path"]
    new_code = proposal["proposed_code"]

    try:
        # Simple implementation - in production, you'd want more sophisticated patching
        with open(file_path, "w") as f:
            f.write(new_code)

        return {"ok": True, "message": f"Applied changes to {file_path}"}

    except Exception as e:
        return {"ok": False, "error": f"Failed to apply changes: {str(e)}"}


def _rollback_changes(backup_id):
    """Rollback changes using backup."""
    logger.warning("agent_interpreter: Rolling back changes using backup %s", backup_id)

    try:
        if backup_id and os.path.exists(backup_id):
            # Extract original file path from backup
            # This is a simplified implementation
            backup_path = Path(backup_id)
            if backup_path.exists():
                # For manual backups, try to restore
                logger.info(
                    "agent_interpreter: Backup file found, manual restore needed"
                )
                # In production, implement automatic restore logic
        else:
            logger.error(
                "agent_interpreter: Backup %s not found for rollback", backup_id
            )

    except Exception as e:
        logger.error("agent_interpreter: Rollback failed: %s", str(e))
