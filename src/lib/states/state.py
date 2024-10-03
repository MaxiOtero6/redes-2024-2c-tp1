from abc import abstractmethod

from lib.arguments.constants import MAX_PAYLOAD_SIZE

MSS = MAX_PAYLOAD_SIZE  # Packet payload bytes


class State:
    _dupACKcount: int
    _lastACKnumber: int
    _cwnd: int
    _ssthresh: int | None = None

    @abstractmethod
    def timeout_event(self):
        pass

    @abstractmethod
    def ACK_event(self, ACKnumber: int):
        pass
