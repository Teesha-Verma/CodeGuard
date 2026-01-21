from git import Repo

class diffExtractor:
    def extract(self, repo_path: str, base_branch: str, pr_number: int):
        repo = Repo(repo_path)

        try:
            repo.git.fetch("origin", base_branch)
            base_ref = f"origin/{base_branch}"
        except:
            repo.git.fetch("origin", "main")
            base_ref = "origin/main"

        repo.git.fetch("origin", f"pull/{pr_number}/head:pr_branch")

        diff = repo.git.diff(f"{base_ref}...pr_branch")
        return diff