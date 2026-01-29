from datetime import datetime, timedelta, time
from collections import Counter
from history import HistoryService

class TimePrediction:
    """Frequency-based time prediction for recurring tasks"""
    
    def __init__(self):
        self.history_service = HistoryService()
    
    def predict_start_time(self, task_name, user_id):
        """
        Predict most likely start time based on task history.
        Objective 4a: Uses frequency analysis from previous entries.
        """
        # Uses the optimized query from history service
        predicted_time = self.history_service.get_most_common_start_time(
            user_id, task_name
        )
        
        if predicted_time is None:
            return None  # No historical data available
        
        return predicted_time
    
    def get_average_duration(self, task_name, user_id):
        """Calculate average duration for a task from history"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        history = self.history_service.get_task_history(
            user_id=user_id,
            task_name=task_name,
            since_date=thirty_days_ago
        )
        
        if not history:
            return None
        
        # Calculate durations
        durations = []
        for entry in history:
            start = entry['start_time']
            end = entry['end_time']
            
            start_minutes = start.hour * 60 + start.minute
            end_minutes = end.hour * 60 + end.minute
            duration_hours = (end_minutes - start_minutes) / 60
            durations.append(duration_hours)
        
        return sum(durations) / len(durations) if durations else None
    
    def suggest_recommended_tasks(self, user_id, limit=5):
        """
        Get most frequently added tasks.
        Objective 5: List recommended tasks in sidebar.
        """
        task_frequency = self.history_service.get_task_frequency(user_id)
        
        # Sort by frequency
        sorted_tasks = sorted(
            task_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [task_name for task_name, _ in sorted_tasks[:limit]]