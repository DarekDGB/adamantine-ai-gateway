from abc import ABC, abstractmethod

from ai_gateway.types import Envelope, Output


class BaseAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_envelope(self, source_input: dict) -> Envelope:
        raise NotImplementedError

    @abstractmethod
    def build_output(self, envelope: Envelope) -> Output:
        raise NotImplementedError
