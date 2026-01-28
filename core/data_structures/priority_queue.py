import heapq

class PriorityQueue:
    """
    Priority queue implementation using Python's heapq module.
    
    This implementation uses a min-heap but negates priorities to achieve
    max-heap behavior (higher priority values are extracted first).
    
    The counter ensures stable ordering when priorities are equal (FIFO).
    
    Attributes:
        _heap: List storing (negated_priority, counter, item) tuples
        _counter: Monotonically increasing counter for tie-breaking
    """
    
    def __init__(self):
        self._heap = []
        self._counter = 0

    def push(self, priority, item):
        """
        Add an item to the priority queue.
        
        Args:
            priority (float): Priority value (higher = more important)
            item: The item to store
            
        Note:
            Priority is negated internally to convert min-heap to max-heap behavior.
            Counter ensures FIFO ordering for equal priorities (Objective 11).
        """
        # CRITICAL FIX: Negate priority to convert min-heap to max-heap
        # Python's heapq is min-heap by default, so we negate to get highest priority first
        heapq.heappush(self._heap, (-priority, self._counter, item))
        self._counter += 1

    def pop(self):
        """
        Remove and return the highest priority item.
        
        Returns:
            tuple: (priority, item) - priority is the original (positive) value
            
        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("pop from an empty priority queue")
        
        negated_priority, counter, item = heapq.heappop(self._heap)
        
        # CRITICAL FIX: Return original (positive) priority
        original_priority = -negated_priority
        return original_priority, item
    
    def peek(self):
        """
        Return the highest priority item without removing it.
        
        Returns:
            tuple: (priority, item)
            
        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("peek from an empty priority queue")
        
        negated_priority, counter, item = self._heap[0]
        return -negated_priority, item
    
    def is_empty(self):
        """
        Check if the queue is empty.
        
        Returns:
            bool: True if queue is empty, False otherwise
        """
        return len(self._heap) == 0
    
    def length(self):
        """
        Get the number of items in the queue.
        
        Returns:
            int: Number of items currently in queue
        """
        return len(self._heap)
    
    def size(self):
        """
        Alias for length() for consistency with common data structure interfaces.
        
        Returns:
            int: Number of items currently in queue
        """
        return self.length()
    
    def clear(self):
        """
        Remove all items from the queue.
        """
        self._heap = []
        self._counter = 0