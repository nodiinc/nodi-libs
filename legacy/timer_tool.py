import threading 
import time
import asyncio

class WaitTimer:
    """Wait Timer"""

    def __init__(self, cycle):
        self.start_time = time.time()
        self.exmin_time = time.time() - self.start_time
        self._cycle_time = max(cycle, self.exmin_time)
        self.store_time = time.time()

    @property
    def cycle_time(self):
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, cycle):
        self._cycle_time = max(cycle, self.exmin_time)

    def wait_timer(self):
        """Execute timer to wait"""
        self.current_time = time.time()
        self.elapse_time = self.current_time - self.store_time
        if self._cycle_time >= self.elapse_time:
            self.store_time += self._cycle_time
        else:
            self.store_time = self._cycle_time - (self.elapse_time % self._cycle_time) + self.current_time
        self.await_time = max(self.store_time - time.time(), 0)
        time.sleep(self.await_time)

class AsyncWaitTimer:
    """Asynchronous Wait Timer"""

    def __init__(self, cycle: float):
        self.start_time = time.time()
        self.exmin_time = time.time() - self.start_time
        self._cycle_time = max(cycle, self.exmin_time)
        self.store_time = time.time()

    @property
    def cycle_time(self) -> float:
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, cycle: float):
        self._cycle_time = max(cycle, self.exmin_time)

    async def wait_timer(self):
        """Execute async timer to wait"""
        current_time = time.time()
        elapse_time = current_time - self.store_time
        if self._cycle_time >= elapse_time:
            self.store_time += self._cycle_time
        else:
            self.store_time = self._cycle_time - (elapse_time % self._cycle_time) + current_time
        await_time = max(self.store_time - time.time(), 0)
        await asyncio.sleep(await_time)

class CheckTimer:
    """Check Timer"""

    def __init__(self, cycle):
        self.start_time = time.time()
        self.exmin_time = time.time() - self.start_time
        self.cycle_time = max(cycle, self.exmin_time)
        self.store_time = time.time()
        
    def check_timer(self):
        """Execute timer to wait"""
        self.current_time = time.time()
        self.elapse_time = self.current_time - self.store_time
        if self.current_time >= self.store_time:
            if self.cycle_time >= self.elapse_time:
                self.store_time += self.cycle_time
            else:
                self.store_time = self.cycle_time - (self.elapse_time % self.cycle_time) + self.current_time
            return True
        else:
            return False

class ThreadTimer:
    """Repeated Thread Timer"""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.timer = None
        self.timer_running = False

        # Store base time
        self.store_time = time.time()

        # Start timer
        self.start_timer()

    def _execute_func(self):
        """Execute target function"""

        # Reset running flag
        self.timer_running = False

        # Execute function
        self.function(*self.args, **self.kwargs)
        
        # Restart timer
        self.start_timer()

    def start_timer(self):
        """Start timer"""
        
        # When not running
        if not self.timer_running:
            
            # Calculate next cycle
            self.current_time = time.time()
            self.store_time = self.store_time + self.interval \
                if (self.current_time - self.store_time) <= self.interval \
                else self.interval - ((self.current_time - self.store_time) % self.interval) + self.current_time
                
            # Input exact interval to timer
            self.interval_accurate = self.store_time - time.time()
            self.timer = threading.Timer(self.interval_accurate, self._execute_func)
            
            # Start timer
            self.timer.start()

            # Set running flag
            self.timer_running = True

    def stop_timer(self):
        """Stop timer"""
        
        # Stop timer
        self.timer.cancel()

        # Reset running flag
        self.timer_running = False


if __name__ == "__main__":
    # at = NodiWaitTimer(1)
    # while True:
    #     time.sleep(1.99) 
    #     at.wait_timer()
    #     print(time.time(), at.recd_tm)
        
    ct = CheckTimer(1)
    while True:
        time.sleep(1.1)
        if ct.check_timer():
            print(time.time(), ct.store_time)
    