from git import Repo  #This is what allows Python to run:git clone https://github.com/user/project
import os
import uuid    # help generating unique Ids


class RepoCloner:
    def __init__(self, base_dir: str = "repos"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir , exist_ok=True)

    def clone(self, repo_url: str) ->str:
        repo_id = str(uuid.uuid4())
        repo_path = os.path.join(self.base_dir , repo_id)


        Repo.clone_from(repo_url , repo_path)
        return repo_path