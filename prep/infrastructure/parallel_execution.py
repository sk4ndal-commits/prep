"""Infrastructure implementation for parallel execution."""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Any, Callable, Optional
import threading
import multiprocessing

from ..domain.interfaces import ParallelExecutor


class ThreadBasedExecutor(ParallelExecutor):
    """Thread-based parallel executor implementation."""
    
    def execute_parallel(self, tasks: List[Callable], max_workers: Optional[int] = None) -> List[Any]:
        """Execute tasks in parallel using threads."""
        if not tasks:
            return []
        
        if max_workers is None:
            max_workers = min(len(tasks), threading.active_count() + 4)
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(task): task for task in tasks}
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    # Log the exception but continue with other tasks
                    # In a real implementation, you might want to use proper logging
                    print(f"Task generated an exception: {exc}")
                    results.append(None)
        
        return results


class ProcessBasedExecutor(ParallelExecutor):
    """Process-based parallel executor implementation."""
    
    def execute_parallel(self, tasks: List[Callable], max_workers: Optional[int] = None) -> List[Any]:
        """Execute tasks in parallel using processes."""
        if not tasks:
            return []
        
        if max_workers is None:
            max_workers = min(len(tasks), multiprocessing.cpu_count())
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(task): task for task in tasks}
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    # Log the exception but continue with other tasks
                    print(f"Task generated an exception: {exc}")
                    results.append(None)
        
        return results


class AdaptiveExecutor(ParallelExecutor):
    """Adaptive executor that chooses the best strategy based on task characteristics."""
    
    def __init__(self):
        self._thread_executor = ThreadBasedExecutor()
        self._process_executor = ProcessBasedExecutor()
    
    def execute_parallel(self, tasks: List[Callable], max_workers: Optional[int] = None) -> List[Any]:
        """Execute tasks using the most appropriate parallel strategy."""
        if not tasks:
            return []
        
        # Use threads for I/O-bound tasks (file reading) and processes for CPU-bound tasks
        # For grep operations, file I/O is typically the bottleneck, so use threads
        return self._thread_executor.execute_parallel(tasks, max_workers)


class SequentialExecutor(ParallelExecutor):
    """Sequential executor for debugging or single-threaded execution."""
    
    def execute_parallel(self, tasks: List[Callable], max_workers: Optional[int] = None) -> List[Any]:
        """Execute tasks sequentially."""
        results = []
        for task in tasks:
            try:
                result = task()
                results.append(result)
            except Exception as exc:
                print(f"Task generated an exception: {exc}")
                results.append(None)
        
        return results