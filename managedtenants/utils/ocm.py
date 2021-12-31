import re
from datetime import datetime, timedelta

import requests
from sretoolbox.utils import retry

from managedtenants.utils.general_utils import parse_version_from_imageset_name


class OCMAPIError(Exception):
    """Used when there are errors with the OCM API"""

    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


def retry_hook(exception):
    if not isinstance(exception, OCMAPIError):
        return

    if exception.response.status_code < 500:
        raise exception


class OcmCli:
    API = "https://api.stage.openshift.com"
    TOKEN_EXPIRATION_MINUTES = 15

    ADDON_KEYS = {
        "id": "id",
        "name": "name",
        "description": "description",
        "link": "docs_link",
        "icon": "icon",
        "label": "label",
        "enabled": "enabled",
        "installMode": "install_mode",
        "targetNamespace": "target_namespace",
        "ocmQuotaName": "resource_name",
        "ocmQuotaCost": "resource_cost",
        "operatorName": "operator_name",
        "hasExternalResources": "has_external_resources",
        "addOnParameters": "parameters",
        "addOnRequirements": "requirements",
        "subOperators": "sub_operators",
    }

    IMAGESET_KEYS = {
        "indexImage": "source_image",
        "addOnParameters": "parameters",
        "addOnRequirements": "requirements",
        "subOperators": "sub_operators",
    }

    def __init__(self, offline_token, api=API, api_insecure=False):
        self.offline_token = offline_token
        self._token = None
        self._last_token_issue = None
        self.api_insecure = api_insecure

        if api is None:
            self.api = self.API
        else:
            self.api = api

    @property
    @retry(hook=retry_hook, max_attempts=10)
    def token(self):
        now = datetime.utcnow()
        if self._token:
            if now - self._last_token_issue < timedelta(
                minutes=self.TOKEN_EXPIRATION_MINUTES
            ):
                return self._token

        url = (
            "https://sso.redhat.com/auth/realms/"
            "redhat-external/protocol/openid-connect/token"
        )

        data = {
            "grant_type": "refresh_token",
            "client_id": "cloud-services",
            "refresh_token": self.offline_token,
        }

        method = requests.post
        response = method(url, data=data)
        self._raise_for_status(response, reqs_method=method, url=url)
        self._token = response.json()["access_token"]
        self._last_token_issue = now
        return self._token

    def list_addons(self):
        return self._pool_items("/api/clusters_mgmt/v1/addons")

    def list_sku_rules(self):
        return self._pool_items("/api/accounts_mgmt/v1/sku_rules")

    def add_addon(self, metadata):
        addon = self._addon_from_metadata(metadata)
        return self._post("/api/clusters_mgmt/v1/addons", json=addon)

    def add_addon_version(self, imageset, metadata):
        addon = self._addon_from_imageset(imageset, metadata)
        return self._post(
            f'/api/clusters_mgmt/v1/addons/{metadata.get("id")}/versions',
            json=addon,
        )

    def update_addon(self, metadata):
        addon = self._addon_from_metadata(metadata)
        addon_id = addon.pop("id")
        return self._patch(
            f"/api/clusters_mgmt/v1/addons/{addon_id}", json=addon
        )

    def update_addon_version(self, imageset, metadata):
        addon = self._addon_from_imageset(imageset, metadata)
        version_id = addon.pop("id")
        addon_name = metadata.get("id")
        return self._patch(
            f"/api/clusters_mgmt/v1/addons/{addon_name}/versions/{version_id}",
            json=addon,
        )

    def get_addon(self, addon_id):
        return self._get(f"/api/clusters_mgmt/v1/addons/{addon_id}")

    def delete_addon(self, addon_id):
        return self._delete(f"/api/clusters_mgmt/v1/addons/{addon_id}")

    def enable_addon(self, addon_id):
        return self._patch(
            f"/api/clusters_mgmt/v1/addons/{addon_id}", json={"enabled": True}
        )

    def disable_addon(self, addon_id):
        return self._patch(
            f"/api/clusters_mgmt/v1/addons/{addon_id}", json={"enabled": False}
        )

    def upsert_addon(self, metadata):
        try:
            addon = self.add_addon(metadata)
        except OCMAPIError as exception:
            if exception.response.status_code == 409:
                return self.update_addon(metadata)

            raise exception
        return addon

    # Post Addon version data to versions endpoint
    def upsert_addon_version(self, imageset, metadata):
        try:
            addon = self.add_addon_version(imageset, metadata)
        except OCMAPIError as exception:
            if exception.response.status_code == 409:
                return self.update_addon_version(imageset, metadata)
            raise exception
        return addon

    # Returns a versioned addon payload that corresponds
    # to an ImageSet
    def _addon_from_imageset(self, imageset, metadata):
        addon = {
            "id": str(parse_version_from_imageset_name(imageset.get("name"))),
            "enabled": metadata.get("enabled"),
            "channel": metadata.get("defaultChannel"),
        }

        for key, val in imageset.items():
            if key in self.IMAGESET_KEYS:
                if key == "addOnParameters":
                    # Enforce a sort order field on addon parameters
                    # so that they can be shown in the same order as
                    # the imageset file.
                    for index, param in enumerate(val):
                        param["order"] = index
                    val = {"items": val}
                addon[self.IMAGESET_KEYS[key]] = val
        return addon

    def _addon_from_metadata(self, metadata):
        addon = {}
        metadata["addOnParameters"] = metadata.get("addOnParameters", [])
        metadata["addOnRequirements"] = metadata.get("addOnRequirements", [])
        for key, val in metadata.items():
            if key in self.ADDON_KEYS:
                # Skip adding these parameters as they're present
                # in the ImageSet (versions endpoint)
                if metadata.get("addonImageSetVersion") and key in [
                    "addOnParameters",
                    "addOnRequirements",
                    "subOperators",
                ]:
                    continue
                if key == "installMode":
                    val = _camel_to_snake_case(val)
                if key == "addOnParameters":
                    # Enforce a sort order field on addon parameters
                    # so that they can be shown in the same order as
                    # the metadata file.
                    for index, param in enumerate(val):
                        param["order"] = index
                    val = {"items": val}
                addon[self.ADDON_KEYS[key]] = val
        return addon

    def _headers(self, extra_headers=None):
        headers = {"Authorization": f"Bearer {self.token}"}

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _url(self, path):
        return f"{self.api}{path}"

    @retry(hook=retry_hook)
    def _api(self, reqs_method, path, **kwargs):
        if self.api_insecure:
            kwargs["verify"] = False
        url = self._url(path)
        headers = self._headers(kwargs.pop("headers", None))
        response = reqs_method(url, headers=headers, **kwargs)
        self._raise_for_status(
            response, reqs_method=reqs_method, url=url, **kwargs
        )

        if response.headers.get("Content-Type") == "application/json":
            return response.json()

        return response

    def _post(self, path, **kwargs):
        return self._api(requests.post, path, **kwargs)

    def _get(self, path, **kwargs):
        return self._api(requests.get, path, **kwargs)

    def _delete(self, path, **kwargs):
        return self._api(requests.delete, path, **kwargs)

    def _patch(self, path, **kwargs):
        return self._api(requests.patch, path, **kwargs)

    def _pool_items(self, path):
        items = []
        page = 1
        while True:
            result = self._get(path, params={"page": str(page)})

            items.extend(result["items"])
            total = result["total"]
            page += 1

            if len(items) == total:
                break

        return items

    @staticmethod
    def _raise_for_status(response, reqs_method, url, **kwargs):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exception:
            method = reqs_method.__name__.upper()
            error_message = f"Error {method} {url}\n{exception}\n"
            if kwargs.get("params"):
                error_message += f"params: {kwargs['params']}\n"
            if kwargs.get("json"):
                error_message += f"json: {kwargs['json']}\n"
            error_message += f"original error: {response.text}"
            raise OCMAPIError(error_message, response)


def _camel_to_snake_case(val):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", val).lower()
