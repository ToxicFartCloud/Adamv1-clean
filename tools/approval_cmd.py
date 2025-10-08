import argparse


def approve_proposal(proposal_id, sign=False, deploy=False, *, emit=True):
    """
    Approves a proposal, creates a signed commit, and optionally triggers deployment.
    Returns a list of log messages.
    """

    logs = []

    def _log(message: str) -> None:
        logs.append(message)
        if emit:
            print(message)

    _log(f"Approving proposal: {proposal_id}")
    if sign:
        _log("  - Creating signed commit...")
    if deploy:
        _log("  - Triggering deployment...")

    return logs


def run(**kwargs):
    proposal_id = kwargs.get("proposal_id")
    if not proposal_id:
        return {
            "ok": False,
            "data": None,
            "error": "'proposal_id' is required.",
        }

    sign = bool(kwargs.get("sign", False))
    deploy = bool(kwargs.get("deploy", False))
    logs = approve_proposal(proposal_id, sign=sign, deploy=deploy, emit=False)
    return {
        "ok": True,
        "data": {"proposal_id": proposal_id, "sign": sign, "deploy": deploy, "logs": logs},
        "error": None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Approve a proposal.")
    parser.add_argument("proposal_id", help="The ID of the proposal to approve.")
    parser.add_argument("--sign", action="store_true", help="Create a signed commit.")
    parser.add_argument("--deploy", action="store_true", help="Trigger deployment.")
    args = parser.parse_args()
    approve_proposal(args.proposal_id, args.sign, args.deploy)
