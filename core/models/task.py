from datetime import datetime

class Task:
    def __init__(self, user_id, name, effort, urgency, length, task_id=None, priority=None, created_at=None):
        self.task_id = task_id
        self.user_id = user_id
        
        # Manual Validation
        if not (1 <= len(name) <= 100):
            raise ValueError('Task name must be between 1 and 100 characters')
        self.name = name

        if not (1 <= effort <= 10) or not (1 <= urgency <= 10):
            raise ValueError('Effort and urgency must be between 1 and 10 NEWNEWNEWNEWNEWNEWNEW')
        self.effort = effort
        self.urgency = urgency

        if length <= 0:
            raise ValueError('Length must be a positive number')
        self.length = length

        self.created_at = created_at or datetime.now()
        
        # Calculate priority if not provided
        if priority is None:
            self.priority = round((self.effort * 0.3) + (self.urgency * 0.5) + (self.length * 0.2 * 10), 2)
        else:
            self.priority = priority

    def is_high_priority(self):
        return self.priority > 7
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "effort": self.effort,
            "urgency": self.urgency,
            "length": self.length,
            "created_at": self.created_at.isoformat()
        }

    def to_dict_with_priority(self):
        task_dict = self.to_dict()
        task_dict["priority"] = self.priority
        return task_dict