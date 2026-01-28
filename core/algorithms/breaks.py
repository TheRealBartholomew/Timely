from datetime import time, timedelta, datetime
import math

class BreakInsertion:
    """Pomodoro-based break insertion algorithm"""
    
    WORK_DURATION = 50  # minutes
    BREAK_DURATION = 10  # minutes
    
    def insert_breaks(self, scheduled_tasks):
        """
        Insert Pomodoro breaks into schedule
        
        Args:
            scheduled_tasks: List of scheduled task dictionaries
        
        Returns:
            List of tasks and breaks combined
        """
        modified_schedule = []
        
        for task_entry in scheduled_tasks:
            task = task_entry['task']
            start_time = task_entry['start_time']
            
            # Calculate task duration in minutes
            task_duration = task.length * 60
            
            # Calculate number of work segments
            num_segments = math.ceil(task_duration / self.WORK_DURATION)
            
            current_time = start_time
            remaining_duration = task_duration
            
            for i in range(num_segments):
                # Calculate work segment duration
                segment_duration = min(self.WORK_DURATION, remaining_duration)
                
                # Add work segment
                segment_end = self._add_minutes(current_time, segment_duration)
                
                work_segment = {
                    'type': 'WORK',
                    'task': task,
                    'start_time': current_time,
                    'end_time': segment_end,
                    'date': task_entry['date']
                }
                modified_schedule.append(work_segment)
                
                current_time = segment_end
                remaining_duration -= segment_duration
                
                # Add break after segment (unless last segment)
                if i < num_segments - 1 and remaining_duration > 0:
                    break_end = self._add_minutes(current_time, self.BREAK_DURATION)
                    
                    break_segment = {
                        'type': 'BREAK',
                        'task': None,
                        'start_time': current_time,
                        'end_time': break_end,
                        'date': task_entry['date']
                    }
                    modified_schedule.append(break_segment)
                    
                    current_time = break_end
        
        return modified_schedule
    
    def _add_minutes(self, time_obj, minutes):
        """Add minutes to a time object"""
        if isinstance(time_obj, time):
            # Convert to datetime for arithmetic
            dt = datetime.combine(datetime.today(), time_obj)
            dt += timedelta(minutes=minutes)
            return dt.time()
        return time_obj