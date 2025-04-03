class GitHubConnector:
    def __init__(self, auth_method="token"):
        load_dotenv()
        
        if auth_method == "token":
            self.token = os.getenv("GITHUB_TOKEN")
            self.github = Github(self.token)
        elif auth_method == "app":
            # For GitHub App installation
            app_id = os.getenv("GITHUB_APP_ID")
            private_key = os.getenv("GITHUB_PRIVATE_KEY")
            self.integration = GithubIntegration(app_id, private_key)
            self.installation_id = os.getenv("GITHUB_INSTALLATION_ID")
            self.github = self.get_github_connection()
        else:
            raise ValueError("Invalid auth method. Use 'token' or 'app'")
    
    def get_github_connection(self):
        """Get Github connection when using GitHub App authentication"""
        if hasattr(self, 'integration'):
            access_token = self.integration.get_access_token(self.installation_id)
            return Github(access_token.token)
        return self.github
    
    def get_organization_repos(self, org_name: str) -> List[Dict]:
        """Get all repositories in an organization"""
        org = self.github.get_organization(org_name)
        return [{"name": repo.name, "id": repo.id} for repo in org.get_repos()]
    
    def get_open_pull_requests(self, repo_name: str, org_name: str) -> List[Dict]:
        """Get all open pull requests for a repository"""
        repo = self.github.get_repo(f"{org_name}/{repo_name}")
        pulls = repo.get_pulls(state='open')
        return [{
            "id": pull.id,
            "number": pull.number,
            "title": pull.title,
            "user": pull.user.login,
            "created_at": pull.created_at.isoformat(),
            "updated_at": pull.updated_at.isoformat(),
            "url": pull.html_url
        } for pull in pulls]
    
    def get_pull_request_files(self, repo_name: str, org_name: str, pr_number: int) -> List[Dict]:
        """Get all files in a pull request"""
        repo = self.github.get_repo(f"{org_name}/{repo_name}")
        pull = repo.get_pull(pr_number)
        files = pull.get_files()
        
        return [{
            "filename": file.filename,
            "status": file.status,
            "additions": file.additions,
            "deletions": file.deletions,
            "changes": file.changes,
            "patch": file.patch,
            "content": self._get_file_content(repo, file.filename, pull.head.sha)
        } for file in files]
    
    def _get_file_content(self, repo, path, sha):
        """Get content of a file at a specific commit"""
        try:
            content = repo.get_contents(path, ref=sha)
            return base64.b64decode(content.content).decode('utf-8')
        except Exception as e:
            return f"Error retrieving content: {str(e)}"
    
    def add_review_comment(self, repo_name: str, org_name: str, pr_number: int, 
                           body: str, commit_id: str, path: str, position: int) -> Dict:
        """Add a review comment to a specific line in a PR"""
        repo = self.github.get_repo(f"{org_name}/{repo_name}")
        pull = repo.get_pull(pr_number)
        
        # Create a review comment
        comment = pull.create_review_comment(body=body, commit_id=commit_id,
                                           path=path, position=position)
        return {
            "id": comment.id,
            "body": comment.body,
            "path": comment.path,
            "position": comment.position
        }
    
    def submit_review(self, repo_name: str, org_name: str, pr_number: int, 
                     comments: List[Dict], review_body: str, event: str = "COMMENT") -> Dict:
        """Submit a full review with multiple comments"""
        repo = self.github.get_repo(f"{org_name}/{repo_name}")
        pull = repo.get_pull(pr_number)
        
        # Submit the review
        review = pull.create_review(commit=pull.head.sha, body=review_body, 
                                   event=event, comments=comments)
        return {
            "id": review.id,
            "body": review.body,
            "state": review.state
        }
    
    def suggest_changes(self, repo_name: str, org_name: str, pr_number: int, 
                       suggestions: List[Dict]) -> None:
        """Suggest code changes in a PR review"""
        # This is a simplified version - in practice, you'd create a review 
        # with comments that contain suggested changes in the GitHub suggestion format
        repo = self.github.get_repo(f"{org_name}/{repo_name}")
        pull = repo.get_pull(pr_number)
        
        comments = []
        for suggestion in suggestions:
            # Format according to GitHub suggestion syntax
            suggestion_body = f"""```suggestion
{suggestion['suggested_code']}
```

{suggestion['explanation']}"""
            
            comments.append({
                "body": suggestion_body,
                "path": suggestion["path"],
                "position": suggestion["position"],
                "line": suggestion.get("line", 1)
            })
        
        # Submit the review with suggestions
        self.submit_review(
            repo_name=repo_name,
            org_name=org_name,
            pr_number=pr_number,
            comments=comments,
            review_body="Here are some suggested improvements to the code.",
            event="COMMENT"
        )
