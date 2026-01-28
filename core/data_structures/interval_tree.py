class IntervalTreeNode:
    """Node in the interval tree"""
    def __init__(self, start, end, task=None):
        self.start = start
        self.end = end
        self.task = task
        self.max = end  # Maximum end time in subtree
        self.left = None
        self.right = None

class IntervalTree:
    """Interval tree for detecting scheduling conflicts"""
    
    def __init__(self):
        self.root = None
    
    def insert(self, start, end, task=None):
        """
        Insert an interval into the tree
        
        Args:
            start: Start time in minutes
            end: End time in minutes
            task: Associated task object
        """
        self.root = self._insert_helper(self.root, start, end, task)
    
    def _insert_helper(self, node, start, end, task):
        """Recursive helper for insertion"""
        # Base case: create new node
        if node is None:
            return IntervalTreeNode(start, end, task)
        
        # Insert based on start time
        if start < node.start:
            node.left = self._insert_helper(node.left, start, end, task)
        else:
            node.right = self._insert_helper(node.right, start, end, task)
        
        # Update max value for this node
        node.max = max(node.end, 
                      node.left.max if node.left else float('-inf'),
                      node.right.max if node.right else float('-inf'))
        
        return node
    
    def query_overlaps(self, start, end):
        """
        Find all intervals that overlap with [start, end]
        
        Args:
            start: Query start time in minutes
            end: Query end time in minutes
            
        Returns:
            List of tuples: [(start, end), (start, end), ...]
        """
        overlaps = []
        self._query_helper(self.root, start, end, overlaps)
        return overlaps
    
    def _query_helper(self, node, start, end, overlaps):
        """Recursive helper for overlap query"""
        if node is None:
            return
        
        # Check if current node overlaps
        # Two intervals [a1, a2] and [b1, b2] overlap if:
        # a1 < b2 AND b1 < a2
        if node.start < end and start < node.end:
            # Return as tuple (start, end)
            overlaps.append((node.start, node.end))
        
        # Search left subtree if there might be overlaps
        if node.left and node.left.max > start:
            self._query_helper(node.left, start, end, overlaps)
        
        # Always search right subtree
        self._query_helper(node.right, start, end, overlaps)
    
    def clear(self):
        """Clear the entire tree"""
        self.root = None
    
    def is_empty(self):
        """Check if tree is empty"""
        return self.root is None
    
    def get_all_intervals(self):
        """Get all intervals in the tree (for debugging)"""
        intervals = []
        self._traverse(self.root, intervals)
        return intervals
    
    def _traverse(self, node, intervals):
        """In-order traversal to collect all intervals"""
        if node is None:
            return
        
        self._traverse(node.left, intervals)
        intervals.append((node.start, node.end, node.task))
        self._traverse(node.right, intervals)