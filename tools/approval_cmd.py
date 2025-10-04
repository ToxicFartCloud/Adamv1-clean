import argparse


def approve_proposal(proposal_id, sign=False, deploy=False):
    """
    Approves a proposal, creates a signed commit, and optionally triggers deployment.
    """
    print(f"Approving proposal: {proposal_id}")
    if sign:
        print("  - Creating signed commit...")
        # Placeholder for git commit logic
    if deploy:
        print("  - Triggering deployment...")
        # Placeholder for deployment logic


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Approve a proposal.")
    parser.add_argument("proposal_id", help="The ID of the proposal to approve.")
    parser.add_argument("--sign", action="store_true", help="Create a signed commit.")
    parser.add_argument("--deploy", action="store_true", help="Trigger deployment.")
    args = parser.parse_args()
    approve_proposal(args.proposal_id, args.sign, args.deploy)
