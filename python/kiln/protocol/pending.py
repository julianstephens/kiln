from dataclasses import dataclass
from typing import Generator

from pydantic import BaseModel

from .jsonrpc import JsonRpcErrorResponse, JsonRpcSuccessResponse
from .method import validate_error_data, validate_success_result


@dataclass(frozen=True)
class PendingRequest:
    """A pending JSON-RPC request."""

    id: str | int
    method: str


class PendingRequests:
    """A collection of pending JSON-RPC requests."""

    def __init__(self) -> None:
        self._by_id: dict[str | int, PendingRequest] = {}

    def add(self, request_id: str | int, method: str) -> None:
        """Add a pending request to the collection.

        Args:
            request_id: The ID of the pending request.
            method: The JSON-RPC method name of the pending request.
        """
        self._by_id[request_id] = PendingRequest(
            id=request_id,
            method=method,
        )

    def pop(self, request_id: str | int) -> PendingRequest:
        """Remove and return a pending request from the collection.

        Args:
            request_id: The ID of the pending request to remove.

        Returns:
            The removed PendingRequest instance.
        """
        return self._by_id.pop(request_id)

    def __contains__(self, request_id: str | int) -> bool:
        """Check if a pending request with the given ID exists in the collection.

        Args:
            request_id: The ID of the pending request to check.

        Returns:
            True if the pending request exists, False otherwise.
        """
        return request_id in self._by_id

    def __len__(self) -> int:
        """Return the number of pending requests in the collection.

        Returns:
            The number of pending requests.
        """
        return len(self._by_id)

    def __iter__(self) -> Generator[PendingRequest, None, None]:
        """Yield each pending request in the collection.

        Returns:
            Generator of PendingRequest instances.
        """
        for request in self._by_id.values():
            yield request


def validate_response_against_pending_method(
    *,
    pending: PendingRequest,
    response: JsonRpcSuccessResponse | JsonRpcErrorResponse,
) -> BaseModel | None:
    """Validate a JSON-RPC response against the corresponding pending request's method.

    Args:
        pending: The pending request to validate against.
        response: The JSON-RPC response to validate.

    Returns:
        BaseModel | None: The validated JSON-RPC model instance or None if no data is
            present.
    """
    if isinstance(response, JsonRpcSuccessResponse):
        return validate_success_result(
            method=pending.method,
            response=response,
        )

    return validate_error_data(
        method=pending.method,
        response=response,
    )
