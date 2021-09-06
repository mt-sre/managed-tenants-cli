import subprocess


def get_short_hash(size=7):
    git_cmd = ["git", "rev-parse", f"--short={size}", "HEAD"]
    result = subprocess.run(
        git_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    short_hash = result.stdout.decode("utf-8").strip()
    return short_hash
