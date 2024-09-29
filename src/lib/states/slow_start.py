from lib.states.congestion_avoidance import CongestionAvoidance
from lib.states.fast_recovery import FastRecovery
from lib.states.state import MSS, State


class SlowStart(State):
    def __init__(self, lastACK: int, cwnd: int | None = None):
        if cwnd:
            self._ssthresh = cwnd / 2

        self._cwnd = MSS
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self):
        self._ssthresh = self._cwnd / 2
        self._cwnd = MSS
        self._dupACKcount = 0
        # retransmit missing packet

    def ACK_event(self, ACKnumber: int) -> State | None:
        if ACKnumber == self._lastACKnumber:
            self._dupACKcount += 1

            if self._dupACKcount == 3:
                return FastRecovery(self._cwnd, self._lastACKnumber)
                # retransmit missing packet

            return

        if self._ssthresh and self._cwnd >= self._ssthresh:
            return CongestionAvoidance(self._cwnd, self._ssthresh, self._lastACKnumber)

        self._cwnd += MSS
        self._dupACKcount = 0
        self._lastACKnumber = ACKnumber
        # transmit new packet
