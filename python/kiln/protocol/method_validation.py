from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from kiln.schemas import (
    ModelError,
    ModelGeneratePayload,
    ModelGenerateResult,
    RepositoryError,
    RepositoryOpenSessionRequestPayload,
    RepositorySearchRequestPayload,
    RepositorySearchResult,
    RepositorySession,
    RepositorySourceRequestPayload,
    RepositorySourceResult,
)

from .errors import FramingError


@dataclass(frozen=True)
class KilnMethodSpec:
    method: str
    params_model: type[BaseModel] | None = None
    result_model: type[BaseModel] | None = None
    error_data_model: type[BaseModel] | None = None


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


def validate_kiln_schema(
    *,
    data_type: Literal["request", "response", "error"],
    schema: type[BaseModel],
    frame: dict,
) -> BaseModel:
    """Validate JSON-RPC frame against the given schema.

    Args:
        data_type: The type of the JSON-RPC frame, either "request", "response",
        or "error".
        schema: The Pydantic model class to validate against.
        frame: The JSON-RPC frame as a dictionary.

    Returns:
        The validated Pydantic model instance.

    Raises:
        FramingError: If the frame is invalid or does not conform to the schema.
    """
    data = None
    if data_type == "request":
        if "params" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'params' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["params"]
    if data_type == "response":
        if "result" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'result' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["result"]
    if data_type == "error":
        if "error" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'error' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["error"]

    if not isinstance(data, dict):
        raise FramingError(
            message=(
                f"invalid JSON-RPC frame: {data_type} must be a JSON object "
                f"for method '{frame.get('method')}'"
            )
        )
    try:
        validated_data = schema.model_validate(data)
    except Exception as e:
        raise FramingError(
            message=(
                "invalid JSON-RPC frame: payload validation failed "
                f"for schema '{schema.__name__}': {e}"
            )
        ) from e
    else:
        return validated_data
