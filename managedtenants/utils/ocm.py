import abc
import copy
import dataclasses
import re
from datetime import datetime, timedelta

import requests
from sretoolbox.utils import retry

from managedtenants.utils.general_utils import (
    parse_version_from_imageset_name,
    try_with_timeout_until,
)


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
        "credentialsRequests": "credentials_requests",
        "addOnParameters": "parameters",
        "addOnRequirements": "requirements",
        "subOperators": "sub_operators",
        "managedService": "managed_service",
        "config": "config",
        "namespaces": "namespaces",
    }

    IMAGESET_KEYS = {
        "indexImage": "source_image",
        "addOnParameters": "parameters",
        "addOnRequirements": "requirements",
        "subOperators": "sub_operators",
        "pullSecretName": "pull_secret_name",
        "additionalCatalogSources": "additional_catalog_sources",
        "config": "config",
    }

    def __init__(
        self,
        client_id=None,
        client_secret=None,
        offline_token=None,
        api=API,
        api_insecure=False,
    ):  # pylint: disable=too-many-arguments
        """Accepts client_id and client_secret or offline token
        to authenticate against OCM. client_id and client_secret
        take precedence.
        """
        self._token_provider = _TokenProvider.from_options(
            options=_TokenProviderOptions(
                client_id=client_id,
                client_secret=client_secret,
                offline_token=offline_token,
            )
        )

        self.api_insecure = api_insecure

        if api is None:
            self.api = self.API
        else:
            self.api = api

    def list_addons(self):
        return self._pool_items("/api/clusters_mgmt/v1/addons")

    def list_sku_rules(self):
        return self._pool_items("/api/accounts_mgmt/v1/sku_rules")

    def add_addon(self, metadata):
        addon = self._addon_from_metadata(metadata)
        return self._post("/api/clusters_mgmt/v1/addons", json=addon)

    def _addon_exists(self, addon_id):
        try:
            self._get(f"/api/clusters_mgmt/v1/addons/{addon_id}")
            return True
        # `_get` raises OCMAPIError on 404's
        except OCMAPIError:
            return False

    def add_addon_version(self, imageset, metadata):
        if self._addon_exists(metadata.get("id")):
            return self._add_addon_version(imageset, metadata)
        # Create the addon first
        self.add_addon(metadata)
        return self._add_addon_version(imageset, metadata)

    def _add_addon_version(self, imageset, metadata):
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

    def shortcircuit_migrate(self, addon_id):
        def addon_migration_complete():
            migration = self.get_addon_migration(addon_id).json()
            return migration.get("state") == "completed"

        # Enable the migration
        resp = self.post_addon_migration_with_body(
            addon_id=addon_id,
            payload={
                "addon_id": addon_id,
                "enabled": True,
                "white_listed": False,
                "rollback_migration": False,
            },
        )

        if resp.status_code in [200, 201]:
            try:
                # Proceed to whitelist only if the migration object's
                # state is "completed"
                if try_with_timeout_until(
                    predicate_func=addon_migration_complete,
                    timeout_duration=40,
                ):
                    resp = self.complete_addon_migration(addon_id)
                    return resp.status_code == 200
            except TimeoutError:
                return False
        return False

    def get_addon_migrations(self):
        return self._get("/api/clusters_mgmt/v1/addon_migrations")

    def check_addon_migration_exists(self, addon_id):
        try:
            self._get(f"/api/clusters_mgmt/v1/addon_migrations/{addon_id}")
            return True
        # `_get` raises OCMAPIError on 404's
        except OCMAPIError:
            return False

    def get_addon_migration(self, addon_id):
        return self._get(f"/api/clusters_mgmt/v1/addon_migrations/{addon_id}")

    def post_addon_migration(self, addon_id):
        return self._post(
            "/api/clusters_mgmt/v1/addon_migrations",
            json={
                "addon_id": addon_id,
                "enabled": False,
                "white_listed": False,
                "rollback_migration": False,
            },
        )

    def post_addon_migration_with_body(self, addon_id, payload):
        try:
            output = self._post(
                "/api/clusters_mgmt/v1/addon_migrations", json=payload
            )
        except OCMAPIError as exception:
            if exception.response.status_code == 409:
                return self._patch(
                    f"/api/clusters_mgmt/v1/addon_migrations/{addon_id}",
                    json=payload,
                )
            raise exception
        return output

    def patch_addon_migration(self, addon_id, patch):
        return self._patch(
            f"/api/clusters_mgmt/v1/addon_migrations/{addon_id}", json=patch
        )

    def delete_addon_migration(self, addon_id):
        return self._delete(
            f"/api/clusters_mgmt/v1/addon_migrations/{addon_id}"
        )

    def disable_addon_installation(self, addon_id):
        try:
            output = self.post_addon_migration(addon_id)
        except OCMAPIError as exception:
            if exception.response.status_code == 409:
                return self.patch_addon_migration(
                    addon_id,
                    {
                        "enabled": False,
                        "white_listed": False,
                        "rollback_migration": False,
                    },
                )
            raise exception
        return output

    def enable_addon_migration(self, addon_id):
        return self.patch_addon_migration(
            addon_id,
            {
                "enabled": True,
            },
        )

    def complete_addon_migration(self, addon_id):
        return self.patch_addon_migration(
            addon_id,
            {
                "enabled": True,
                "white_listed": True,
            },
        )

    def rollback_addon_migration(self, addon_id):
        return self.patch_addon_migration(
            addon_id,
            {
                "enabled": True,
                "white_listed": False,
                "rollback_migration": True,
            },
        )

    def unrollback_addon_migration(self, addon_id):
        return self.patch_addon_migration(
            addon_id,
            {
                "rollback_migration": False,
            },
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

    def _set_default_values_for_addon_version(self, addon, metadata):
        # Set additionalCatalogSources
        mapped_key = self.IMAGESET_KEYS["additionalCatalogSources"]
        addon[mapped_key] = self.index_dicts(
            metadata.get("additionalCatalogSources", [])
        )

        # Set default values for attributes under config in metadata,
        # if not present.
        metadata["config"] = metadata.get("config", {})
        metadata["config"]["env"] = metadata["config"].get("env", [])
        metadata["config"]["secrets"] = metadata["config"].get("secrets", [])

        # Set config
        addon = self.set_addon_config(
            addon=addon,
            addon_id=metadata["id"],
            config_obj=metadata["config"],
            mapped_key=self.IMAGESET_KEYS["config"],
        )

        # Set addOnParameters
        mapped_key = self.IMAGESET_KEYS["addOnParameters"]
        addon[mapped_key] = self._parameters_from_list(
            metadata.get("addOnParameters", [])
        )

        # Set addOnRequirements
        mapped_key = self.IMAGESET_KEYS["addOnRequirements"]
        addon[mapped_key] = metadata.get("addOnRequirements", [])

        # Set subOperators
        mapped_key = self.IMAGESET_KEYS["subOperators"]
        addon[mapped_key] = metadata.get("subOperators", [])

        return addon

    # Returns a versioned addon payload that corresponds
    # to an ImageSet
    def _addon_from_imageset(self, imageset, metadata):
        addon = {
            "id": str(parse_version_from_imageset_name(imageset.get("name"))),
            "enabled": metadata.get("enabled"),
            "channel": metadata.get("defaultChannel"),
        }

        if metadata.get("pullSecretName"):
            mapped_key = self.IMAGESET_KEYS["pullSecretName"]
            addon[mapped_key] = metadata.get("pullSecretName")

        # Set attributes from metadata file if present, otherwise set them
        # to their default empty values.
        # These attributes will get overwritten with the values from
        # the imageset if they're present in the imageset as well.

        addon = self._set_default_values_for_addon_version(
            addon=addon, metadata=metadata
        )

        for key, val in imageset.items():
            if key in self.IMAGESET_KEYS:
                mapped_key = self.IMAGESET_KEYS[key]
                if key == "additionalCatalogSources":
                    catalog_src_list = self.index_dicts(val)
                    addon[mapped_key] = catalog_src_list
                    continue
                if key == "config":
                    addon = self.set_addon_config(
                        addon=addon,
                        addon_id=metadata["id"],
                        config_obj=val,
                        mapped_key=mapped_key,
                    )
                    continue
                if key == "addOnParameters":
                    val = self._parameters_from_list(val)
                addon[mapped_key] = val
        return addon

    def set_addon_config(self, addon, addon_id, config_obj, mapped_key):
        if config_obj is not None:
            if not addon.get(mapped_key):
                addon[mapped_key] = {}

            # Can be an empty list hence the not none check
            if config_obj.get("env") is not None:
                env_var_list = self.index_dicts(config_obj.get("env"))
                addon[mapped_key]["add_on_environment_variables"] = env_var_list

            # Can be an empty list hence the not none check
            if config_obj.get("secrets") is not None:
                secret_propagations_list = self.index_dicts(
                    self.map_secret_objs(addon_id, config_obj.get("secrets"))
                )
                addon[mapped_key][
                    "add_on_secret_propagations"
                ] = secret_propagations_list

        return addon

    def get_namespace_labels_list(self, namespaces, namespaceLabels):
        namespaceLabelsList = []
        for namespace in namespaces:
            namespaceLabelsList.append(
                {"name": namespace, "labels": namespaceLabels}
            )
        return namespaceLabelsList

    def _addon_from_metadata(self, metadata):
        addon = {}

        for key, val in self._complete_metadata(metadata).items():
            if key in self.ADDON_KEYS:
                mapped_key = self.ADDON_KEYS[key]
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
                    val = self._parameters_from_list(val)
                if key == "config":
                    addon = self.set_addon_config(
                        addon=addon,
                        addon_id=metadata["id"],
                        config_obj=val,
                        mapped_key=mapped_key,
                    )
                    continue
                addon[mapped_key] = val
        return addon

    @staticmethod
    def _complete_metadata(raw):
        list_fields = (
            "addOnParameters",
            "addOnRequirements",
            "subOperators",
            "additionalCatalogSources",
        )

        res = copy.deepcopy(raw)

        for field in list_fields:
            res[field] = res.get(field, [])

        res["config"] = res.get("config", {})
        res["config"]["env"] = res["config"].get("env", [])
        res["config"]["secrets"] = res["config"].get("secrets", [])

        res["namespaces"] = [
            {"name": ns, "labels": res.get("namespaceLabels")}
            for ns in res.get("namespaces", [])
        ]

        return res

    @staticmethod
    def _parameters_from_list(params):
        # Enforce a sort order field on addon parameters
        # so that they can be shown in the same order as
        # the metadata file.
        for index, param in enumerate(params):
            param["order"] = index + 1
        return {"items": params}

    # Maps a secret from the addon metadata json to the one ocm expects.
    @staticmethod
    def map_secret_objs(addon_id, secrets):
        return [
            {
                "source_secret": f"{addon_id}-{i['name']}",
                "destination_secret": i["name"],
            }
            for i in secrets
        ]

    @staticmethod
    def index_dicts(dicts):
        return [dict(d, id=str(id)) for id, d in enumerate(dicts)]

    def _headers(self, extra_headers=None):
        token = self._token_provider.retrieve_token()
        headers = {"Authorization": f"Bearer {token}"}

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
        _raise_for_status(response, reqs_method=reqs_method, url=url, **kwargs)
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
            result = self._get(path, params={"page": str(page)}).json()

            items.extend(result["items"])
            total = result["total"]
            page += 1

            if len(items) == total:
                break

        return items


def _camel_to_snake_case(val):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", val).lower()


_RHSSO_TOKEN_ENDPOINT = (
    "https://sso.redhat.com/"
    "auth/realms/redhat-external/protocol/openid-connect/token"
)


class _TokenProvider(abc.ABCMeta):
    def __init__(cls, options):
        cls._token_endpoint = options.token_endpoint
        cls._token_expiry_period = options.token_expiry_period
        cls._request_timeout = options.request_timeout

        cls._token = None
        cls._last_token_issue = None

    @staticmethod
    def from_options(options):
        # https://github.com/PyCQA/pylint/issues/3268
        # pylint: disable=no-value-for-parameter
        if options.client_secret:
            return _ClientCredentialTokenProvider(options)

        return _OfflineTokenProvider(options)

    @retry(hook=retry_hook, max_attempts=10)
    def retrieve_token(cls):
        now = datetime.utcnow()
        token_valid = now - cls._last_token_issue < cls._token_expiry_period

        if cls._token and token_valid:
            return cls._token

        method = requests.post
        response = method(
            cls._token_endpoint,
            data=cls._token_request_body(),
            timeout=cls._request_timeout,
        )
        _raise_for_status(response, reqs_method=method, url=cls._token_endpoint)

        cls._token = response.json()["access_token"]
        cls._last_token_issue = now

        return cls._token

    @classmethod
    @abc.abstractmethod
    def _token_request_body(cls):
        pass


_RHSSO_TOKEN_ENDPOINT = (
    "https://sso.redhat.com/"
    "auth/realms/redhat-external/protocol/openid-connect/token"
)


@dataclasses.dataclass(frozen=True)
class _TokenProviderOptions:
    client_id: str
    client_secret: str
    offline_token: str
    token_endpoint: str = _RHSSO_TOKEN_ENDPOINT
    token_expiry_period: timedelta = (timedelta(minutes=15),)
    request_timeout: int = None

    def __post_init__(self):
        if (self.client_id and self.client_secret) or self.offline_token:
            return

        raise ValueError(
            "`client_id` and `client_secret` or `offline_token` must be"
            " provided"
        )


class _ClientCredentialTokenProvider(_TokenProvider):
    def __init__(cls, options):
        super().__init__(cls, options)  # pylint: disable=too-many-function-args

        cls._client_id = options.client_id
        cls._client_secret = options.client_secret

    @classmethod
    def _token_request_body(cls):
        return {
            "grant_type": "client_credentials",
            "client_id": cls._client_id,
            "client_secret": cls._client_secret,
        }


class _OfflineTokenProvider(_TokenProvider):
    def __init__(cls, options):
        super().__init__(cls, options)  # pylint: disable=too-many-function-args

        cls._client_id = options.client_id or "cloud_services"
        cls._offline_token = options.offline_token

    @classmethod
    def _token_request_body(cls):
        return {
            "grant_type": "refresh_token",
            "client_id": cls._client_id,
            "refresh_token": cls._offline_token,
        }


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
