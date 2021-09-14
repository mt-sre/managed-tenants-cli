import json

import gitlab


class GitLab:
    def __init__(self, url, token, project):
        self.gl = gitlab.Gitlab(url=url, private_token=token, ssl_verify=False)
        self.project = self.gl.projects.get(project)

    def create_branch(self, new_branch, source_branch):
        data = {"branch": new_branch, "ref": source_branch}
        self.project.branches.create(data)

    def delete_branch(self, branch):
        self.project.branches.delete(branch)

    def create_mr(self, source_branch, target_branch, title):
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": True,
            "labels": [],
        }
        self.project.mergerequests.create(data)

    def update_file(self, branch_name, file_path, commit_message, content):
        data = {
            "branch": branch_name,
            "commit_message": commit_message,
            "actions": [
                {"action": "update", "file_path": file_path,
                 "content": content}
            ],
        }
        self.project.commits.create(data)

    def create_file(self, branch_name, file_path, commit_message, content):
        data = {
            "branch": branch_name,
            "commit_message": commit_message,
            "actions": [
                {"action": "create", "file_path": file_path,
                 "content": content}
            ],
        }
        self.project.commits.create(data)

    def mr_exists(self, title):
        mrs = self.get_items(self.project.mergerequests.list, state="opened")
        for mr in mrs:
            if mr.attributes.get("title") != title:
                continue
            return True
        return False

    def get_file(self, path, ref="main"):
        try:
            path = path.lstrip("/")
            return self.project.files.get(file_path=path, ref=ref)
        except gitlab.exceptions.GitlabGetError as details:
            response = json.loads(details.response_body)
            if response.get("message") == "404 File Not Found":
                return None
            raise

    @staticmethod
    def get_items(method, **kwargs):
        all_items = []
        page = 1
        while True:
            items = method(page=page, per_page=100, **kwargs)
            all_items.extend(items)
            if len(items) < 100:
                break
            page += 1
        return all_items
