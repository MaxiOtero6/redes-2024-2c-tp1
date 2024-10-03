from abc import abstractmethod

from lib.arguments.constants import MAX_PAYLOAD_SIZE

MSS = MAX_PAYLOAD_SIZE  # Packet payload bytes


class State:
    _dupACKcount: int
    _lastACKnumber: int
    _cwnd: int
    _ssthresh: int | None = None

    @abstractmethod
    def timeout_event(self, retransmit_function) -> "State":
        pass

    @abstractmethod
    def ACK_event(self, ACKnumber: int, retransmit_function) -> "State":
        pass

    def cwnd(self) -> int:
        return self._cwnd


class SlowStart(State):
    def __init__(self, lastACK: int, cwnd: int | None = None):
        if cwnd:
            self._ssthresh = cwnd / 2

        self._cwnd = MSS
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self, retransmit_function):
        self._ssthresh = self._cwnd / 2
        self._cwnd = MSS
        self._dupACKcount = 0
        # retransmit missing packet
        retransmit_function()

        return self

    def ACK_event(self, ACKnumber: int, retransmit_function) -> State:
        if ACKnumber == self._lastACKnumber:
            self._dupACKcount += 1

            if self._dupACKcount == 3:
                retransmit_function()
                return FastRecovery(self._cwnd, self._lastACKnumber)
                # retransmit missing packet

            return self

        if self._ssthresh and self._cwnd >= self._ssthresh:
            return CongestionAvoidance(
                self._cwnd, self._ssthresh, self._lastACKnumber
            )

        self._cwnd += MSS
        self._dupACKcount = 0
        self._lastACKnumber = ACKnumber
        # transmit new packet

        return self


class CongestionAvoidance(State):
    def __init__(self, cwnd: int, sstresh: int, lastACK: int):
        self._ssthresh = sstresh
        self._cwnd = cwnd
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self, retransmit_function):
        retransmit_function()
        return SlowStart(self._cwnd)
        # retransmit missing packet

    def ACK_event(self, ACKnumber: int, retransmit_function) -> State:
        if ACKnumber == self._lastACKnumber:
            self._dupACKcount += 1

            if self._dupACKcount == 3:
                retransmit_function()
                return FastRecovery(self._cwnd, self._lastACKnumber)
                # retransmit missing packet
            return self

        self._cwnd += MSS * (MSS / self._cwnd)
        self._dupACKcount = 0
        self._lastACKnumber = ACKnumber
        # transmit new packet

        return self


class FastRecovery(State):
    def __init__(self, cwnd: int, lastACK: int):
        self._ssthresh = cwnd / 2
        self._cwnd = self._ssthresh + 3 * MSS
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self, retransmit_function) -> State:
        retransmit_function()
        return SlowStart(self._cwnd, self._lastACKnumber)
        # retransmit missing packet

    def ACK_event(self, ACKnumber: int, retransmit_function) -> State:  # noqa
        if ACKnumber == self._lastACKnumber:
            self._cwnd += 1
            # transmit new packet
            return self
        else:
            return CongestionAvoidance(
                self._ssthresh, self._ssthresh, ACKnumber
            )
