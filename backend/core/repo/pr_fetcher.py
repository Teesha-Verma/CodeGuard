import requests

class prFetcher:
    def fetch(self, repo_url:str , pr_number:int) ->dict:
        parts=repo_url.rstrip("/").split("/")
        owner, repo= parts[-2], parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        response=requests.get(api_url)
        response.raise_for_status()
        return response.json()