# Adapted from: https://github.com/app-sre/qontract-reconcile/blob/master/reconcile/utils/quay_api.py # pylint: disable=C0301 # noqa: E501
# qontract-reconcile takes a long time to install because it has so many
# dependencies. Pipelines will be faster if we simply redefine QuayApi here.
import os

import requests
from sretoolbox.utils import retry
from sretoolbox.utils.logger import get_text_logger


class QuayApiError(Exception):
    """Used when there are errors with the Quay API."""

    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


def retry_hook(exception):
    """Retries on 5xx QuayApiError and all other requests exceptions."""
    if (
        isinstance(exception, QuayApiError)
        and exception.response.status_code < 500
    ):
        raise exception
    # Ignore all other exceptions
    # https://docs.python-requests.org/en/latest/api/#exceptions


class QuayApi:
    """
    Abstraction around the Quay.io API.

    View swagger docs here: https://docs.quay.io/api/swagger/.
    """

    def __init__(self, organization, token=None, base_url="quay.io"):
        """
        Creates a Quay API abstraction.

        :param organization: Name of your quay organization.
        :type organization: str
        :param token: Quay OAuth Application token (do not use robot account)
        :type token: str, optional
        :param base_url: Quay base API server url
        :type base_url: str
        :return: instance
        :rtype: QuayApi
        """

        self.token = _get_token_or_fail(token)
        self.organization = organization
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        self.team_members = {}
        self.api_url = f"https://{base_url}/api/v1"
        self.log = get_text_logger("app")

    def repo_exists(self, repo_name):
        """
        Checks if a repo exists.

        :param repo_name: Name of the repository
        :type repo_name: str
        :return: response.status_code is 2XX
        :rtype: bool
        :raise QuayApiError: the operation failed
        """
        url = f"{self.api_url}/repository/{self.organization}/{repo_name}"
        params = {
            "includeTags": False,
            "includeStats": False,
        }
        response = self._api(
            method=requests.get, url=url, dont_raise_for=[404], params=params
        )
        return _is_200(response.status_code)

    def repo_create(self, repo_name):
        """
        Creates a public repository called repo_name.

        :param repo_name: Name of the repository
        :type repo_name: str
        :return: response.status_code is 2XX
        :rtype: bool
        :raise QuayApiError: the operation fails
        """
        url = f"{self.api_url}/repository"
        params = {
            "repo_kind": "image",
            "namespace": self.organization,
            "visibility": "public",
            "repository": repo_name,
            "description": "",
        }
        response = self._api(requests.post, url, json=params)
        return _is_200(response.status_code)

    @retry(hook=retry_hook)
    def _api(self, method, url, dont_raise_for=None, **kwargs):
        dont_raise_for = [] if dont_raise_for is None else dont_raise_for
        response = method(url, headers=self.headers, **kwargs)

        # Don't raise for certain HTTP response code, e.g.: 404 not found.
        if response.status_code not in dont_raise_for:
            _raise_for_status(response, method, url, **kwargs)
        self.log.info("JSON response: %s", response.json())
        self.log.info("status_code: %s", response.status_code)
        return response


def _is_200(status_code):
    return 200 <= status_code < 300


def _get_token_or_fail(token):
    res = token if token is not None else os.environ.get("QUAY_APIKEY")
    if token == "":
        raise ValueError("Invalid empty QUAY_APIKEY environment variable.")

    return res


def _raise_for_status(response, method, url, **kwargs):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        method = method.__name__.upper()
        error_message = f"Error {method} {url}\n{exception}\n"
        if kwargs.get("params"):
            error_message += f"params: {kwargs['params']}\n"
        if kwargs.get("json"):
            error_message += f"json: {kwargs['json']}\n"
        error_message += f"original error: {response.text}"
        raise QuayApiError(error_message, response)
