
from core.repo.clone import RepoCloner
from core.repo.pr_fetcher import prFetcher
from core.diff.extractor import diffExtractor
from core.diff.parser import diffParser

class pipelineRunner:
    def __init__(self, review_id: str, repo_url:str , pr_number:int ):
        self.review_id = review_id
        self.repo_url = repo_url
        self.pr_number = pr_number

    def run(self):

        print("[PIPELINE] Cloning repository...")
        repo_path = RepoCloner().clone(self.repo_url)

        print("[PIPELINE] Fetching PR Metadata....")
        pr_data = prFetcher().fetch(self.repo_url, self.pr_number)

        base_branch = pr_data["base"]["ref"]
        head_branch = pr_data["head"]["ref"]


        print("[DEBUG] Base branch:", base_branch)
        #print("[DEBUG] Head branch:", head_branch)

        print("[PIPELINE] Diff extracting...")
        diff = diffExtractor().extract(repo_path, base_branch, self.pr_number)

        # print("Diff extracted successfully! !")
        # return diff

        print("[PIPELINE] Parsing Diff....")
        parsing = diffParser().parse(diff)

        print("[PIPELINE] Parsed diff: ")
        for item in parsing:
            print(item)

        return parsing        




