from git import Repo

class diffExtractor:
    def extract(self, repo_path:str, base_branch:str, pr_number:int):
        repo=repo(repo_path)

        repo.git.checkout(head_branch)
        diff=repo.git.diff(f"{base_branch}...{head_branch}", unified=0)

        return diff