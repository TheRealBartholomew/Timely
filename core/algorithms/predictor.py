from collections import Counter
from datetime import datetime, timedelta, time

class TimePrediction:
    """Frequency-based time prediction for recurring tasks"""
    
    def __init__(self, history_service):
        self.history_service = history_service
    
    def predict_start_time(self, task_name, user_id):
        """
        Predict most likely start time based on task history
        
        Args:
            task_name (str): Name of the task
            user_id (str): User ID
        
        Returns:
            time object or None: Predicted start time
        """
        # Get task history from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        history = self.history_service.get_task_history(
            user_id=user_id,
            task_name=task_name,
            since_date=thirty_days_ago
        )
        
        if not history:
            return None
        
        # Extract start times
        start_times = [entry['start_time'] for entry in history]
        
        # Count frequency of each start time
        time_frequency = Counter(start_times)
        
        # Return most common start time
        if time_frequency:
            most_common = time_frequency.most_common(1)[0]
            return most_common[0]
        
        return None
    
    def get_average_duration(self, task_name, user_id):
        """Calculate average duration for a task"""
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
            
            if isinstance(start, time) and isinstance(end, time):
                start_minutes = start.hour * 60 + start.minute
                end_minutes = end.hour * 60 + end.minute
                duration_hours = (end_minutes - start_minutes) / 60
                durations.append(duration_hours)
        
        if durations:
            return sum(durations) / len(durations)
        
        return None
    
    def suggest_recommended_tasks(self, user_id, limit=5):
        """Get most frequently added tasks"""
        # This would query the database for task frequency
        task_frequency = self.history_service.get_task_frequency(user_id)
        
        # Sort by frequency
        sorted_tasks = sorted(
            task_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [task_name for task_name, _ in sorted_tasks[:limit]]