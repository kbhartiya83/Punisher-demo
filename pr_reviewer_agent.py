class PRReviewerAgent:
    def __init__(self, org_name: str, llm_api_url: str, llm_api_key: str, auth_method="token"):
        self.org_name = org_name
        self.github = GitHubConnector(auth_method)
        self.memory = MemorySystem()
        self.analyzer = CodeAnalyzer(llm_api_url, llm_api_key)
        
        # Initialize with organization repositories
        self.update_org_repos()
        
        # Load default coding standards
        self.load_default_standards()
    
    def update_org_repos(self) -> None:
        """Update the list of repositories in the organization"""
        repos = self.github.get_organization_repos(self.org_name)
        self.memory.set_org_repos([repo["name"] for repo in repos])
    
    def load_default_standards(self) -> None:
        """Load default coding standards"""
        default_standards = {
            "Python": {
                "style_guide": "PEP 8",
                "max_line_length": 88,
                "docstring_style": "Google style",
                "prefer_type_hints": True
            },
            "JavaScript": {
                "style_guide": "Airbnb",
                "prefer_const": True,
                "avoid_var": True,
                "use_semicolons": True
            },
            "Java": {
                "style_guide": "Google Java Style Guide",
                "naming_conventions": {
                    "classes": "UpperCamelCase",
                    "methods": "lowerCamelCase",
                    "constants": "UPPER_SNAKE_CASE",
                    "variables": "lowerCamelCase",
                    "packages": "lowercase"
                },
                "formatting": {
                    "indent": 2,
                    "line_length": 100,
                    "braces": "same line",
                    "line_wrapping": "4-space continuation indent"
                },
                "practices": {
                    "prefer_interfaces": True,
                    "avoid_public_fields": True,
                    "immutability": "prefer immutable when possible",
                    "exception_handling": "use specific exceptions",
                    "avoid_null": "use Optional<T> instead of null",
                    "prefer_composition": "favor composition over inheritance"
                },
                "documentation": {
                    "javadoc_required": ["public", "protected"],
                    "javadoc_optional": ["private", "package-private"],
                    "method_comments": "describe parameters, return values, and exceptions"
                },
                "code_structure": {
                    "class_organization": [
                        "static fields",
                        "instance fields",
                        "constructors",
                        "public methods",
                        "protected methods",
                        "private methods"
                    ],
                    "method_length": "prefer < 40 lines",
                    "class_length": "prefer < 1000 lines"
                },
                "performance": {
                    "prefer_StringBuilder": "for string concatenation in loops",
                    "resource_management": "use try-with-resources",
                    "collection_sizing": "initialize with expected capacity"
                },
                "testing": {
                    "framework": "JUnit 5",
                    "naming": "test<MethodName>_<TestScenario>",
                    "coverage_target": "80% method coverage"
                },
                "design_patterns": {
                    "recommended": [
                        "Builder for complex objects",
                        "Factory Method for object creation",
                        "Strategy for algorithm selection"
                    ],
                    "avoid": [
                        "Singleton (use dependency injection)",
                        "Deep inheritance hierarchies"
                    ]
                }
            }
            # Add standards for other languages as needed
        }
        self.memory.update_coding_standards(default_standards)
    
    def load_custom_standards(self, standards_file: str) -> None:
        """Load custom coding standards from a file"""
        try:
            with open(standards_file, 'r') as f:
                standards = json.load(f)
                self.memory.update_coding_standards(standards)
        except Exception as e:
            print(f"Error loading custom standards: {e}")
    
    def scan_for_new_prs(self) -> List[Dict]:
        """Scan all repositories for new pull requests"""
        all_prs = []
        for repo_name in self.memory.org_repos:
            try:
                prs = self.github.get_open_pull_requests(repo_name, self.org_name)
                all_prs.extend([{"repo": repo_name, **pr} for pr in prs])
            except Exception as e:
                print(f"Error scanning PRs in {repo_name}: {e}")
        return all_prs
    
    def review_pull_request(self, repo_name: str, pr_number: int) -> Dict:
        """Review a specific pull request"""
        try:
            # Get PR files
            files = self.github.get_pull_request_files(repo_name, self.org_name, pr_number)
            
            all_comments = []
            overall_analysis = {
                "file_count": len(files),
                "total_changes": sum(f["changes"] for f in files),
                "file_analyses": []
            }
            
            # Review each file
            for file in files:
                # Skip certain files (binaries, large files, etc.)
                if not file["content"] or len(file["content"]) > 100000:
                    continue
                
                # Get coding standards for this file type
                language = self.analyzer._detect_language(file["filename"])
                standards = self.memory.coding_standards.get(language, {})
                
                # Analyze the code
                analysis = self.analyzer.analyze_code(file["content"], file["filename"], standards)
                
                # Format review comments
                file_comments = self.analyzer.format_review_comments(analysis, file["filename"])
                all_comments.extend(file_comments)
                
                # Add to overall analysis
                overall_analysis["file_analyses"].append({
                    "filename": file["filename"],
                    "code_quality_score": analysis.get("code_quality_score", 0),
                    "issue_count": len(analysis.get("issues", [])),
                    "suggestion_count": len(analysis.get("suggested_changes", []))
                })
            
            # Prepare summary
            quality_scores = [file["code_quality_score"] for file in overall_analysis["file_analyses"] 
                            if "code_quality_score" in file]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            summary = f"""# PR Review Summary

Overall code quality score: {avg_quality:.1f}/10

Reviewed {overall_analysis['file_count']} files with {overall_analysis['total_changes']} changes.
Found {sum(file['issue_count'] for file in overall_analysis['file_analyses'])} issues.
Provided {sum(file['suggestion_count'] for file in overall_analysis['file_analyses'])} suggestions.

## File-by-File Breakdown:
"""
            
            for file in overall_analysis["file_analyses"]:
                summary += f"- **{file['filename']}**: Score {file['code_quality_score']}/10, {file['issue_count']} issues, {file['suggestion_count']} suggestions\n"
            
            # Submit the review
            review_result = self.github.submit_review(
                repo_name=repo_name,
                org_name=self.org_name,
                pr_number=pr_number,
                comments=all_comments,
                review_body=summary,
                event="COMMENT"
            )
            
            # Store review in memory
            review_data = {
                "review_id": review_result["id"],
                "pr_number": pr_number,
                "repo_name": repo_name,
                "comment_count": len(all_comments),
                "summary": summary,
                "overall_analysis": overall_analysis
            }
            self.memory.store_review(f"{repo_name}_{pr_number}", review_data)
            
            return review_data
            
        except Exception as e:
            error_msg = f"Error reviewing PR #{pr_number} in {repo_name}: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
    
    def run_continuous_review(self, interval_minutes: int = 15) -> None:
        """Continuously scan for and review new PRs"""
        print(f"Starting continuous review. Checking for PRs every {interval_minutes} minutes.")
        try:
            while True:
                # Update repositories list
                self.update_org_repos()
                
                # Scan for open PRs
                open_prs = self.scan_for_new_prs()
                print(f"Found {len(open_prs)} open PRs")
                
                # Review PRs that haven't been reviewed yet
                for pr in open_prs:
                    pr_id = f"{pr['repo']}_{pr['number']}"
                    if pr_id not in self.memory.reviewed_prs:
                        print(f"Reviewing PR #{pr['number']} in {pr['repo']}")
                        self.review_pull_request(pr['repo'], pr['number'])
                
                # Wait for the next scan
                print(f"Waiting {interval_minutes} minutes until next scan...")
                time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            print("Stopping continuous review.")
        except Exception as e:
            print(f"Error in continuous review: {str(e)}")
