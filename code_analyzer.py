class CodeAnalyzer:
    def __init__(self, llm_api_url: str, api_key: str):
        self.llm_api_url = llm_api_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def analyze_code(self, code: str, file_path: str, coding_standards: Dict) -> Dict:
        """Analyze code using an LLM API"""
        language = self._detect_language(file_path)
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Analyze the following {language} code according to the provided coding standards.
        Identify issues, bugs, or improvements. Format your response as JSON with the following structure:
        {{
            "issues": [
                {{
                    "severity": "high/medium/low",
                    "description": "Description of the issue",
                    "line_number": line_number,
                    "suggestion": "Suggested fix if applicable"
                }}
            ],
            "code_quality_score": 0-10,
            "suggested_changes": [
                {{
                    "line_number": line_number,
                    "original_code": "original code snippet",
                    "suggested_code": "improved code snippet",
                    "explanation": "Why this change is suggested"
                }}
            ],
            "general_feedback": "Overall feedback about the code"
        }}
        
        Coding standards to follow:
        {json.dumps(coding_standards, indent=2)}
        
        Here's the code to analyze:
        ```{language}
        {code}
        ```
        """
        
        # Send the code to the LLM API for analysis
        response = requests.post(
            self.llm_api_url,
            headers=self.headers,
            json={"prompt": prompt, "max_tokens": 1500}
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract the JSON response from the LLM output
            # This depends on your specific LLM API's response format
            analysis = json.loads(result["choices"][0]["text"])
            return analysis
        else:
            return {
                "error": f"API request failed with status {response.status_code}",
                "message": response.text
            }
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".cs": "C#",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".rs": "Rust",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL"
        }
        return language_map.get(ext, "Unknown")
    
    def format_review_comments(self, analysis: Dict, file_path: str) -> List[Dict]:
        """Convert code analysis to GitHub review comments"""
        comments = []
        
        # Convert issues to comments
        for issue in analysis.get("issues", []):
            comment = {
                "path": file_path,
                "position": issue["line_number"],
                "body": f"**{issue['severity'].upper()} Issue**: {issue['description']}\n\n"
                        f"Suggestion: {issue['suggestion']}"
            }
            comments.append(comment)
        
        # Convert suggested changes to comments with GitHub suggestion format
        for change in analysis.get("suggested_changes", []):
            suggestion_body = f"""**Suggested Change**:

```suggestion
{change['suggested_code']}
```

{change['explanation']}"""
            
            comment = {
                "path": file_path,
                "position": change["line_number"],
                "body": suggestion_body
            }
            comments.append(comment)
        
        return comments
