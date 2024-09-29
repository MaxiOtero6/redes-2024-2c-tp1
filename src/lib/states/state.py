from abc import abstractmethod

MSS = 1  # Packet


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
