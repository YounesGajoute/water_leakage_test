"""
Threading utilities for the Air Leakage Test Application
"""

import threading
import time
from typing import Optional, Callable, Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, Future


class ThreadSafeQueue:
    """Thread-safe queue implementation"""
    
    def __init__(self, maxsize: int = 0):
        self._queue = []
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._stats = {'puts': 0, 'gets': 0, 'timeouts': 0}
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Add item to queue"""
        with self._lock:
            if self._maxsize > 0:
                while len(self._queue) >= self._maxsize:
                    if not block:
                        raise Exception("Queue full")
                    if timeout is not None:
                        if not self._not_full.wait(timeout):
                            self._stats['timeouts'] += 1
                            raise Exception("Queue full, timeout")
                    else:
                        self._not_full.wait()
            
            self._queue.append(item)
            self._stats['puts'] += 1
            self._not_empty.notify()
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue"""
        with self._lock:
            while len(self._queue) == 0:
                if not block:
                    raise Exception("Queue empty")
                if timeout is not None:
                    if not self._not_empty.wait(timeout):
                        self._stats['timeouts'] += 1
                        raise Exception("Queue empty, timeout")
                else:
                    self._not_empty.wait()
            
            item = self._queue.pop(0)
            self._stats['gets'] += 1
            self._not_full.notify()
            return item
    
    def put_nowait(self, item: Any):
        """Add item to queue without blocking"""
        return self.put(item, block=False)
    
    def get_nowait(self) -> Any:
        """Get item from queue without blocking"""
        return self.get(block=False)
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        with self._lock:
            return len(self._queue) == 0
    
    def full(self) -> bool:
        """Check if queue is full"""
        with self._lock:
            return self._maxsize > 0 and len(self._queue) >= self._maxsize
    
    def qsize(self) -> int:
        """Get queue size"""
        with self._lock:
            return len(self._queue)
    
    def clear(self):
        """Clear the queue"""
        with self._lock:
            self._queue.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        with self._lock:
            return self._stats.copy()


class ThreadManager:
    """Thread manager for background tasks"""
    
    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._threads = {}
        self._futures = {}
        self._lock = threading.Lock()
    
    def submit_task(self, func: Callable, *args, name: Optional[str] = None, **kwargs) -> Future:
        """Submit a task for execution"""
        future = self._executor.submit(func, *args, **kwargs)
        
        if name:
            with self._lock:
                self._futures[name] = future
        
        return future
    
    def start_daemon_thread(self, target: Callable, name: str, *args, **kwargs) -> bool:
        """Start a daemon thread"""
        with self._lock:
            if name in self._threads:
                if self._threads[name].is_alive():
                    print(f"Thread '{name}' is already running")
                    return False
                else:
                    del self._threads[name]
        
        thread = threading.Thread(target=target, name=name, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        
        with self._lock:
            self._threads[name] = thread
        
        return True
    
    def stop_thread(self, name: str, timeout: float = 5.0) -> bool:
        """Stop a thread by name"""
        with self._lock:
            if name not in self._threads:
                return False
            
            thread = self._threads[name]
            if not thread.is_alive():
                del self._threads[name]
                return True
        
        # Note: We can't actually stop a thread in Python, but we can wait for it
        thread.join(timeout=timeout)
        
        with self._lock:
            if not thread.is_alive():
                del self._threads[name]
                return True
            else:
                print(f"Thread '{name}' did not stop within timeout")
                return False
    
    def is_thread_running(self, name: str) -> bool:
        """Check if a thread is running"""
        with self._lock:
            if name in self._threads:
                return self._threads[name].is_alive()
            return False
    
    def get_task_result(self, name: str, timeout: Optional[float] = None) -> Any:
        """Get result of a submitted task"""
        with self._lock:
            if name not in self._futures:
                return None
            
            future = self._futures[name]
        
        try:
            result = future.result(timeout=timeout)
            with self._lock:
                del self._futures[name]
            return result
        except Exception as e:
            with self._lock:
                del self._futures[name]
            raise e
    
    def wait_for_all_tasks(self, timeout: Optional[float] = None) -> bool:
        """Wait for all submitted tasks to complete"""
        with self._lock:
            futures = list(self._futures.values())
        
        if not futures:
            return True
        
        try:
            for future in futures:
                future.result(timeout=timeout)
            return True
        except Exception as e:
            print(f"Error waiting for tasks: {e}")
            return False
    
    def get_active_threads(self) -> List[str]:
        """Get list of active thread names"""
        with self._lock:
            return [name for name, thread in self._threads.items() if thread.is_alive()]
    
    def get_thread_count(self) -> int:
        """Get number of active threads"""
        return len(self.get_active_threads())
    
    def shutdown(self, wait: bool = True, timeout: float = 10.0):
        """Shutdown the thread manager"""
        with self._lock:
            threads = list(self._threads.values())
            futures = list(self._futures.values())
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=timeout)
        
        # Shutdown executor
        self._executor.shutdown(wait=wait)
        
        with self._lock:
            self._threads.clear()
            self._futures.clear()


class PeriodicTask:
    """Periodic task runner"""
    
    def __init__(self, interval: float, task: Callable, *args, **kwargs):
        self.interval = interval
        self.task = task
        self.args = args
        self.kwargs = kwargs
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
    
    def start(self) -> bool:
        """Start the periodic task"""
        if self._running:
            return False
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True
        return True
    
    def stop(self, timeout: float = 5.0) -> bool:
        """Stop the periodic task"""
        if not self._running:
            return True
        
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                print("Warning: Periodic task did not stop within timeout")
                return False
        
        self._running = False
        return True
    
    def _run(self):
        """Internal run method"""
        while not self._stop_event.is_set():
            try:
                start_time = time.time()
                self.task(*self.args, **self.kwargs)
                
                # Calculate sleep time accounting for execution time
                execution_time = time.time() - start_time
                sleep_time = max(0, self.interval - execution_time)
                
                if sleep_time > 0:
                    self._stop_event.wait(sleep_time)
                    
            except Exception as e:
                print(f"Error in periodic task: {e}")
                self._stop_event.wait(1)  # Wait 1 second before retry
    
    def is_running(self) -> bool:
        """Check if task is running"""
        return self._running


def run_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Optional[Any]:
    """
    Run a function with a timeout
    
    Args:
        func: Function to run
        timeout: Timeout in seconds
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or None if timeout
    """
    result: list[Optional[Any]] = [None]
    exception: list[Optional[Exception]] = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        return None
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


def debounce(wait_time: float):
    """
    Decorator to debounce function calls
    
    Args:
        wait_time: Time to wait before execution
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            def delayed_call():
                time.sleep(wait_time)
                return func(*args, **kwargs)
            
            thread = threading.Thread(target=delayed_call, daemon=True)
            thread.start()
            return thread
        
        return wrapper
    return decorator


def run_in_thread(func: Callable, *args, **kwargs) -> threading.Thread:
    """
    Run a function in a separate thread
    
    Args:
        func: Function to run
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Thread object
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread