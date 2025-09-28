from abc import abstractmethod, ABC

from .entities import User


class AbstractUserRepository(ABC):

    @abstractmethod
    def get_by_id(self, user_id: int):
        raise NotImplementedError

    @abstractmethod
    def add(self, user: User):
        raise NotImplementedError

