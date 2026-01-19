from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class ServiceResult(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

    @staticmethod
    def ok(data: T) -> "ServiceResult[T]":
        return ServiceResult(success=True, data=data)

    @staticmethod
    def fail(error: str) -> "ServiceResult[T]":
        return ServiceResult(success=False, error=error)