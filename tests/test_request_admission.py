"""CPU-only concurrent clients: fairness, overload, cancellation and safe release."""
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'network')]
from request_admission import RequestAdmission, QueueFull
from worker_manager import Workers, RouterError


class AdmissionTest(unittest.TestCase):
    def wait_for(self, check):
        deadline = time.monotonic() + 3
        while not check():
            if time.monotonic() > deadline:
                self.fail('Concurrent request did not reach expected state')
            threading.Event().wait(.005)

    def test_fifo_switch_cannot_be_overtaken_by_same_model(self):
        gate = RequestAdmission();gate.acquire()
        order = [];errors = []
        def request(name):
            try:
                if not gate.acquire(timeout=2):raise AssertionError('Admission timed out')
                order.append(name);gate.release()
            except BaseException as e:errors.append(e)
        threads = []
        for i, name in enumerate(['switch', 'same-model-1', 'same-model-2']):
            thread = threading.Thread(target=request,args=(name,));thread.start();threads.append(thread)
            self.wait_for(lambda: gate.snapshot()['queued'] == i + 1)
        self.assertFalse(gate.acquire(blocking=False))  # idle teardown cannot overtake clients
        gate.release()
        for thread in threads:thread.join(3)
        self.assertFalse(errors);self.assertFalse(any(t.is_alive() for t in threads))
        self.assertEqual(order,['switch','same-model-1','same-model-2'])

    def test_full_queue_timeout_and_next_request_recovery(self):
        gate=RequestAdmission(max_queued=1);gate.acquire();result=[]
        thread=threading.Thread(target=lambda:result.append(gate.acquire(timeout=.2)));thread.start()
        self.wait_for(lambda:gate.snapshot()['queued']==1)
        with self.assertRaises(QueueFull):gate.acquire(timeout=1)
        thread.join(3);self.assertEqual(result,[False]);self.assertEqual(gate.snapshot()['queued'],0)
        gate.release();self.assertTrue(gate.acquire(blocking=False));gate.release()

    def test_disconnected_waiter_is_removed_without_starting(self):
        gate=RequestAdmission();gate.acquire();cancel=threading.Event();errors=[]
        def progress():
            if cancel.is_set():raise BrokenPipeError('client gone')
        def request():
            try:gate.acquire(timeout=2,progress=progress)
            except BrokenPipeError:errors.append('cancelled')
        thread=threading.Thread(target=request);thread.start()
        self.wait_for(lambda:gate.snapshot()['queued']==1);cancel.set();thread.join(3)
        self.assertEqual(errors,['cancelled']);self.assertEqual(gate.snapshot()['queued'],0)
        gate.release();self.assertTrue(gate.acquire(blocking=False));gate.release()

    def test_same_model_burst_uses_one_qualified_slot(self):
        worker=Workers.__new__(Workers);worker.lock=RequestAdmission();worker.busy=False
        worker.touch_activity=lambda:None
        worker.start=lambda _name,_progress:None
        first=threading.Event();finish=threading.Event();errors=[];counts={'active':0,'peak':0}
        mutex=threading.Lock()
        def request():
            try:
                worker.acquire('qwen27b-sglang')
                with mutex:
                    counts['active']+=1;counts['peak']=max(counts['peak'],counts['active'])
                first.set();finish.wait(3)
                with mutex:counts['active']-=1
                worker.release()
            except BaseException as e:errors.append(e)
        threads=[threading.Thread(target=request) for _ in range(4)]
        for thread in threads:thread.start()
        self.assertTrue(first.wait(2));self.wait_for(lambda:worker.request_status()['queued']==3)
        self.assertEqual(worker.request_status()['inflight'],1)
        finish.set()
        for thread in threads:thread.join(3)
        self.assertFalse(errors);self.assertEqual(counts['peak'],1)
        self.assertEqual(worker.request_status()['inflight'],0)
        self.assertEqual(worker.request_status()['queued'],0)

    def test_failed_load_preserves_next_ticket_and_unload_ownership_checks(self):
        worker=Workers.__new__(Workers);worker.lock=RequestAdmission();worker.busy=False
        worker.touch_activity=lambda:None
        worker.start=lambda *_:(_ for _ in ()).throw(RouterError('guard stop'))
        with self.assertRaises(RouterError):worker.acquire('qwen27b-sglang')
        self.assertFalse(worker.lock.snapshot()['admission_active'])
        worker.stop_owned=lambda:(_ for _ in ()).throw(RouterError('protected GPU reservation'))
        with self.assertRaisesRegex(RouterError,'protected GPU'):worker.unload()
        self.assertFalse(worker.lock.snapshot()['admission_active'])
        worker.lock.acquire()  # hold gate while overload is tested below
        with patch.object(worker.lock,'acquire',side_effect=QueueFull):
            with self.assertRaises(RouterError) as error:worker.acquire('qwen27b-sglang')
        self.assertEqual(error.exception.status,429);worker.lock.release()


if __name__=='__main__':unittest.main()
