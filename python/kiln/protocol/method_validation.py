from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from kiln.schemas.model import ModelError, ModelGeneratePayload, ModelGenerateResult
from kiln.schemas.repository import (
    RepositoryError,
    RepositoryOpenSessionRequestPayload,
    RepositorySearchRequestPayload,
    RepositorySearchResult,
    RepositorySession,
    RepositorySourceRequestPayload,
    RepositorySourceResult,
)

from .errors import KilnPayloadValidationError, UnsupportedMethodError
from .jsonrpc import JsonRpcErrorResponse, JsonRpcRequest, JsonRpcSuccessResponse


@dataclass(frozen=True)
class KilnMethodSpec:
    """Specification for a Kiln JSON-RPC method, including the expected parameter,
    result, and error data models."""

    method: str
    params_model: type[BaseModel] | None = None
    result_model: type[BaseModel] | None = None
    error_data_model: type[BaseModel] | None = None


# Kiln method specifications for supported JSON-RPC methods.
KILN_METHODS = {
    "repository.open_session": KilnMethodSpec(
        method="repository.open_session",
        params_model=RepositoryOpenSessionRequestPayload,
        result_model=RepositorySession,
        error_data_model=RepositoryError,
    ),
    "repository.search": KilnMethodSpec(
        method="repository.search",
        params_model=RepositorySearchRequestPayload,
        result_model=RepositorySearchResult,
        error_data_model=RepositoryError,
    ),
    "repository.get_source": KilnMethodSpec(
        method="repository.get_source",
        params_model=RepositorySourceRequestPayload,
        result_model=RepositorySourceResult,
        error_data_model=RepositoryError,
    ),
    "model.generate": KilnMethodSpec(
        method="model.generate",
        params_model=ModelGeneratePayload,
        result_model=ModelGenerateResult,
        error_data_model=ModelError,
    ),
}


def get_method_spec(method: str) -> KilnMethodSpec:
    """Get the KilnMethodSpec for the given method.

    Args:
        method: The JSON-RPC method name.

    Returns:
        The KilnMethodSpec for the given method.
    Raises:
        FramingError: If the method is not supported.
    """
    try:
        return KILN_METHODS[method]
    except KeyError as e:
        raise UnsupportedMethodError(method) from e


def validate_request_params(request: JsonRpcRequest) -> BaseModel | None:
    """Validate the request parameters for the given method.

    Args:
        request: The JSON-RPC request as a Pydantic model.

    Returns:
        The validated Pydantic model instance or None if no params model is defined.

    Raises:
        KilnPayloadValidationError: If the parameters are invalid.
    """
    spec = get_method_spec(request.method)
    if spec.params_model is None:
        return None
    params = request.params or {}
    try:
        return spec.params_model.model_validate(params)
    except ValidationError as e:
        raise KilnPayloadValidationError(
            method=request.method, part="params", details=str(e)
        ) from e


def validate_success_result(
    *, method: str, response: JsonRpcSuccessResponse
) -> BaseModel | None:
    """Validate the success result for the given method.

    Args:
        method: The JSON-RPC method name.
        response: The JSON-RPC success response as a Pydantic model.

    Returns:
        BaseModel | None: The validated Pydantic model instance or None if
            no result model is defined.

    Raises:
        KilnPayloadValidationError: If the result is invalid.
    """
    spec = get_method_spec(method)
    if spec.result_model is None:
        return None
    try:
        return spec.result_model.model_validate(response.result)
    except ValidationError as e:
        raise KilnPayloadValidationError(
            method=method, part="result", details=str(e)
        ) from e


def validate_error_data(
    *, method: str, response: JsonRpcErrorResponse
) -> BaseModel | None:
    """Validate the error data for the given method.

    Args:
        method: The JSON-RPC method name.
        response: The JSON-RPC error response as a Pydantic model.

    Returns:
        BaseModel | None: The validated Pydantic model instance or None if no error data
            model is defined.

    Raises:
        KilnPayloadValidationError: If the error data is invalid.
    """
    spec = get_method_spec(method)
    if spec.error_data_model is None:
        return None

    data = response.error.data
    if data is None:
        return None

    try:
        return spec.error_data_model.model_validate(data)
    except ValidationError as e:
        raise KilnPayloadValidationError(
            method=method, part="error.data", details=str(e)
        ) from e
