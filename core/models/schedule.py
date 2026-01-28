from datetime import datetime, date, time
from pydantic import BaseModel
from typing import Optional

class Schedule(BaseModel):
    schedule_id: str
    user_id: str
    task_id: str
    task_name: str
    start_time: time
    end_time: time
    date: date
    is_regular_task: bool = False
    created_at: datetime = datetime.now()

    def to_dict(self):
        return {
            "schedule_id": self.schedule_id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "date": self.date.isoformat(),
            "is_regular_task": self.is_regular_task,
            "created_at": self.created_at.isoformat()
        }