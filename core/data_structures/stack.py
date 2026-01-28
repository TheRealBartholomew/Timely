class UndoStack:
    #Stack-based undo/redo system for schedule modifications
    
    def __init__(self, max_size=50):
        self._undo_stack = []
        self._redo_stack = []
        self._max_size = max_size

    def push_state(self, schedule_snapshot):
        #save state
        self._redo_stack.clear()
        self._undo_stack.append(schedule_snapshot.copy())

        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)

    def undo(self, current_state):
        # restore previous state
        if not self._undo_stack:
            return None
        
        self._redo_stack.append(current_state.copy())
        return self._undo_stack.pop()
    
    def redo(self):
        # restore next state
        if not self._redo_stack:
            return None
        
        return self._redo_stack.pop()
    
    def can_undo(self):
        return len(self._undo_stack) > 0
    
    def can_redo(self):
        return len(self._redo_stack) > 0
    
    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
