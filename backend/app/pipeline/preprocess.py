from urllib.parse import urlparse

class Preprocessor:
    @staticmethod
    def validate_repo_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc, "github.com" in result.netloc])
        except ValueError:
            return False
            
    @staticmethod
    def sanitize_input(text: str) -> str:
        return text.strip()
