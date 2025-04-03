def main():
    """Main entry point for the PR Reviewer application"""
    print("Starting GitHub PR Reviewer Agent...")
    
    # Set up the agent
    agent = setup_pr_reviewer()
    
    # Determine mode of operation
    mode = os.getenv("OPERATION_MODE", "continuous").lower()
    
    if mode == "continuous":
        # Run in continuous mode
        interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
        print(f"Running in continuous mode, checking every {interval} minutes")
        agent.run_continuous_review(interval_minutes=interval)
    
    elif mode == "single":
        # Run for a single PR
        repo_name = os.getenv("REPO_NAME")
        pr_number = int(os.getenv("PR_NUMBER"))
        
        if not repo_name or not pr_number:
            print("Error: REPO_NAME and PR_NUMBER must be set for single mode")
            sys.exit(1)
            
        print(f"Reviewing single PR #{pr_number} in repository {repo_name}")
        result = agent.review_pull_request(repo_name, pr_number)
        print(f"Review completed with ID: {result.get('review_id', 'error')}")
    
    elif mode == "scan":
        # Just scan for PRs without reviewing
        print("Scanning for open PRs...")
        open_prs = agent.scan_for_new_prs()
        print(f"Found {len(open_prs)} open PRs:")
        for pr in open_prs:
            print(f"- {pr['repo']} #{pr['number']}: {pr['title']} by {pr['user']}")
    
    else:
        print(f"Unknown operation mode: {mode}")
        print("Valid modes are: continuous, single, scan")
        sys.exit(1)

# Standard Python idiom to call the main function
if __name__ == "__main__":
    import sys
    main()
