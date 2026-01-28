from datetime import time

class RegularTask:
    def __init__(self, user_id, name, length, start_time, regular_task_id=None):
        self.regular_task_id = regular_task_id
        self.user_id = user_id
        self.name = name
        self.length = length
        self.start_time = start_time
    
    def to_dict(self):
        # Serialize RegularTask to dictionary
        data = {
            "userId": self.user_id,
            "name": self.name,
            "length": self.length,
            "start_time": self.start_time,
        }
        if self.regular_task_id:
            data["regularTaskId"] = self.regular_task_id
        return data