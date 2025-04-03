class MemorySystem:
    def __init__(self):
        self.reviewed_prs = {}  # PR_id -> review summary
        self.org_repos = []     # List of repositories in the organization
        self.review_history = []  # Historical reviews for learning patterns
        self.coding_standards = {}  # Organization-specific coding standards

    def store_review(self, pr_id: str, review_data: Dict) -> None:
        """Store a review in memory"""
        self.reviewed_prs[pr_id] = review_data
        self.review_history.append({
            "pr_id": pr_id,
            "timestamp": time.time(),
            "review": review_data
        })
        
    def get_review(self, pr_id: str) -> Optional[Dict]:
        """Retrieve a previously conducted review"""
        return self.reviewed_prs.get(pr_id)
    
    def update_coding_standards(self, standards: Dict) -> None:
        """Update the coding standards for the organization"""
        self.coding_standards.update(standards)
    
    def set_org_repos(self, repos: List[str]) -> None:
        """Set the list of repositories in the organization"""
        self.org_repos = repos
