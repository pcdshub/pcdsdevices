import time
import threading
import logging

from pcdsdevices.daq import Daq

logger = logging.getLogger(__name__)


class SimNoDaq(Daq):
    def connect(self):
        logger.debug('SimNoDaq.connect()')


class Control:
    _all_states = ['Disconnected', 'Connected', 'Configured', 'Open',
                   'Running']
    _state = _all_states[0]
    _transitions = dict(
        connect=dict(ignore=_all_states[1:],
                     begin=[_all_states[0]],
                     end=_all_states[1]),
        disconnect=dict(ignore=[],
                        begin=_all_states[0:3],
                        end=_all_states[0]),
        configure=dict(ignore=[],
                       begin=_all_states[1:3],
                       end=_all_states[2]),
        begin=dict(ignore=[],
                   begin=_all_states[2:4],
                   end=_all_states[4]),
        stop=dict(ignore=_all_states[0:4],
                  begin=[_all_states[4]],
                  end=_all_states[3]),
        endrun=dict(ignore=_all_states[0:3],
                    begin=_all_states[3:5],
                    end=_all_states[2])
    )

    def __init__(self, *args, **kwargs):
        self._duration = None
        self._time_remaining = 0
        self._done_flag = threading.Event()

    def _do_transition(self, transition):
        logger.debug('Doing transition %s from state %s',
                     transition, self._state)
        info = self._transitions[transition]
        if self._state in info['ignore']:
            ok = False
        elif self._state in info['begin']:
            self._state = info['end']
            ok = True
        else:
            err = 'Invalid SimControl transition {} from state {}'
            raise RuntimeError(err.format(transition, self._state))
        logger.debug('Ended in state %s, success: %s', self._state, ok)
        return ok

    def state(self):
        logger.debug('SimControl.state()')
        return self._all_states.index(self._state)

    def connect(self):
        logger.debug('SimControl.connect()')
        self._do_transition('connect')

    def disconnect(self):
        logger.debug('SimControl.disconnect()')
        self._do_transition('disconnect')

    def configure(self, *, record=False, key=0, events=None, l1t_events=None,
                  l3t_events=None, duration=None, controls=None, monitors=None,
                  partition=None):
        logger.debug(('SimControl.configure(record=%s, key=%s, events=%s, '
                      'l1t_events=%s, l3t_events=%s, duration=%s, '
                      'controls=%s, monitors=%s, partition=%s)'),
                     record, key, events, l1t_events, l3t_events, duration,
                     controls, monitors, partition)
        if self._do_transition('configure'):
            dur = self._pick_duration(events, l1t_events, l3t_events, duration)
            if dur is None:
                raise RuntimeError('configure requires events or duration')
            else:
                self._duration = dur

    def begin(self, *, events=None, l1t_events=None, l3t_events=None,
              duration=None, controls=None, monitors=None):
        logger.debug(('SimControl.begin(events=%s, l1t_events=%s, '
                      'l3t_events=%s, duration=%s, controls=%s, '
                      'monitors=%s)'),
                     events, l1t_events, l3t_events, duration, controls,
                     monitors)
        if self._do_transition('begin'):
            dur = self._pick_duration(events, l1t_events, l3t_events, duration)
            if dur is None:
                err = 'SimControl stops here because pydaq segfaults here'
                raise RuntimeError(err)
            self._done_flag.clear()
            thr = threading.Thread(target=self._begin_thread, args=(dur,))
            thr.start()

    def _pick_duration(self, events, l1t_events, l3t_events, duration):
        logger.debug('SimControl._pick_duration(%s, %s, %s, %s)', events,
                     l1t_events, l3t_events, duration)
        for ev in (events, l1t_events, l3t_events):
            if ev is not None:
                if ev < 0:
                    raise RuntimeError('This is bad in real daq')
                elif not isinstance(ev, int):
                    raise RuntimeError('This is bad in real daq')
                elif ev == 0:
                    return float('inf')
                else:
                    return ev / 120
        if duration is not None:
            if not isinstance(duration, list):
                raise RuntimeError('This freezes the real daq')
            elif not len(duration) == 2:
                raise RuntimeError('This freezes the real daq')
            secs = duration[0]
            nsec = duration[1]
            if not isinstance(secs, int):
                raise RuntimeError('This is bad in real daq')
            if not isinstance(nsec, int):
                raise RuntimeError('This is bad in real daq')
            total_time = secs + nsec * 1e-9
            if total_time <= 0:
                raise RuntimeError('This freezes the real daq')
            else:
                return total_time
        return None

    def stop(self):
        logger.debug('SimControl.stop()')
        self._do_transition('stop')
        self._time_remaining = 0
        self._done_flag.set()

    def endrun(self):
        logger.debug('SimControl.endrun()')
        self._do_transition('endrun')
        self._time_remaining = 0
        self._done_flag.set()

    def _begin_thread(self, duration):
        logger.debug('SimControl._begin_thread(%s)', duration)
        start = time.time()
        interrupted = False
        dt = 0.1
        while duration > 0:
            duration -= dt
            if self._done_flag.wait(dt):
                interrupted = True
                break
        if not interrupted:
            try:
                self.stop()
            except Exception:
                pass
        end = time.time()
        logger.debug('%ss elapased in SimControl._begin_thread(%s)',
                     end-start, duration)

    def end(self):
        logger.debug('SimControl.end()')
        if self._state != 'Running':
            raise RuntimeError('Not running!')
        self._done_flag.wait()
