from lib.states.congestion_avoidance import CongestionAvoidance
from lib.states.slow_start import SlowStart
from lib.states.state import MSS, State


class FastRecovery(State):
    def __init__(self, cwnd: int, lastACK: int):
        self._ssthresh = cwnd / 2
        self._cwnd = self._ssthresh + 3 * MSS
        self._dupACKcount = 0
        self._lastACKnumber = lastACK

    def timeout_event(self) -> State:
        return SlowStart(self._cwnd, self._lastACKnumber)
        # retransmit missing packet

    def ACK_event(self, ACKnumber: int):
        if ACKnumber == self._lastACKnumber:
            self._cwnd += 1
            # transmit new packet
        else:
            return CongestionAvoidance(self._ssthresh, self._ssthresh, ACKnumber)
