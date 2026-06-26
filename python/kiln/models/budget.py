from dataclasses import dataclass

from .errors import MustBePositiveError


@dataclass(frozen=True)
class Budget:
    max_input_tokens: int = 32_000
    max_output_tokens: int = 4_000
    max_model_calls: int = 8
    max_repository_queries: int = 24
    max_turns: int = 12
    max_wall_time_seconds: int = 300

    def __post_init__(self) -> None:
        values = {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_model_calls": self.max_model_calls,
            "max_repository_queries": self.max_repository_queries,
            "max_turns": self.max_turns,
            "max_wall_time_seconds": self.max_wall_time_seconds,
        }

        for _, value in values.items():
            if value <= 0:
                raise MustBePositiveError(value)
