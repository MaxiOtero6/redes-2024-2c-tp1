from lib.states.fast_recovery import FastRecovery
from lib.states.slow_start import SlowStart
from lib.states.state import MSS, State


class CongestionAvoidance(State):
    def __init__(self, cwnd: int, sstresh: int, lastACK: int):
        self._ssthresh = sstresh
        self._cwnd = cwnd
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self):
        return SlowStart(self._cwnd)
        # retransmit missing packet

    def ACK_event(self, ACKnumber: int):
        if ACKnumber == self._lastACKnumber:
            self._dupACKcount += 1

            if self._dupACKcount == 3:
                return FastRecovery(self._cwnd, self._lastACKnumber)
                # retransmit missing packet
            return

        self._cwnd += MSS * (MSS / self._cwnd)
        self._dupACKcount = 0
        self._lastACKnumber = ACKnumber
        # transmit new packet
