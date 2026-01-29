# services/history_service.py (rename from .txt)
from services.database_client import SupabaseClient
from datetime import datetime, timedelta, time
import uuid

class HistoryService:
    """Database operations for task history (Objective 3)"""
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    def record_task_completion(self, user_id, task_id, start_time, end_time, date_obj):
        """
        Insert task history record when task is completed.
        Objective 3a: Enables storing 50+ entries per user.
        """
        history_id = str(uuid.uuid4())
        
        try:
            response = self.client.table('taskHistory').insert({
                'historyId': history_id,
                'userId': user_id,
                'taskId': task_id,
                'startTime': start_time.isoformat(),
                'endTime': end_time.isoformat(),
                'date': date_obj.isoformat(),
                'completed_at': datetime.now().isoformat()
            }).execute()
            
            return response.data is not None
        
        except Exception as e:
            print(f"Error recording history: {e}")
            return False
    
    def get_task_history(self, user_id, task_name=None, since_date=None, limit=50):
        """
        Retrieve task history with optimized query.
        Objective 3a: Returns min 50 entries.
        Objective 3b: Default 90-day window.
        Objective 3c: Optimized for <2 second response.
        """
        try:
            # Build query with JOIN to get task names - CRITICAL for performance
            query = self.client.table('taskHistory').select(
                'historyId, userId, taskId, startTime, endTime, date, completed_at, tasks(name, effort, urgency, length)'
            ).eq('userId', user_id)
            
            # Apply date filter (Objective 3b - 90 days default)
            if since_date:
                query = query.gte('date', since_date.isoformat())
            else:
                # Default to 90 days
                ninety_days_ago = datetime.now() - timedelta(days=90)
                query = query.gte('date', ninety_days_ago.isoformat())
            
            # Apply task name filter if provided
            if task_name:
                query = query.eq('tasks.name', task_name)
            
            # Order by date descending (most recent first)
            query = query.order('date', desc=True).order('startTime', desc=True)
            
            # Limit results (Objective 3a)
            query = query.limit(limit)
            
            response = query.execute()
            
            # Format results
            history = []
            for record in response.data:
                history.append({
                    'history_id': record['historyId'],
                    'task_id': record['taskId'],
                    'task_name': record['tasks']['name'] if record.get('tasks') else 'Unknown',
                    'start_time': time.fromisoformat(record['startTime']),
                    'end_time': time.fromisoformat(record['endTime']),
                    'date': datetime.fromisoformat(record['date']).date(),
                    'completed_at': record['completed_at'],
                    'effort': record['tasks'].get('effort') if record.get('tasks') else None,
                    'urgency': record['tasks'].get('urgency') if record.get('tasks') else None
                })
            
            return history
        
        except Exception as e:
            print(f"Error retrieving history: {e}")
            return []
    
    def delete_old_history(self, user_id, days=90):
        """
        Cleanup old history records.
        Objective 3b: Maintain 90-day retention policy.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            response = self.client.table('taskHistory').delete()\
                .eq('userId', user_id)\
                .lt('date', cutoff_date.isoformat())\
                .execute()
            
            deleted_count = len(response.data) if response.data else 0
            print(f"Deleted {deleted_count} old history records")
            return True
        
        except Exception as e:
            print(f"Error deleting old history: {e}")
            return False
    
    def get_most_common_start_time(self, user_id, task_name):
        """
        Find most frequent start time for task.
        Objective 4: Time prediction algorithm support.
        Uses 30-day window as per your design document.
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        try:
            # Query with task name filter
            response = self.client.table('taskHistory').select(
                'startTime, tasks!inner(name)'
            ).eq('userId', user_id)\
             .eq('tasks.name', task_name)\
             .gte('date', thirty_days_ago.isoformat())\
             .execute()
            
            if not response.data:
                return None
            
            # Count frequency
            from collections import Counter
            start_times = [record['startTime'] for record in response.data]
            time_counter = Counter(start_times)
            
            if time_counter:
                most_common = time_counter.most_common(1)[0]
                return time.fromisoformat(most_common[0]).time()
            
            return None
        
        except Exception as e:
            print(f"Error getting common start time: {e}")
            return None
    
    def get_task_frequency(self, user_id):
        """
        Count how often each task appears in history.
        Objective 5: Supports recommended tasks feature.
        """
        try:
            # Get all history with task names
            response = self.client.table('taskHistory').select(
                'tasks(name)'
            ).eq('userId', user_id).execute()
            
            # Count task frequencies
            from collections import Counter
            task_names = [
                record['tasks']['name'] 
                for record in response.data 
                if record.get('tasks')
            ]
            task_counter = Counter(task_names)
            
            return dict(task_counter)
        
        except Exception as e:
            print(f"Error getting task frequency: {e}")
            return {}
    
    def get_history_count(self, user_id):
        """
        Count total history entries for user.
        Objective 3a: Verify 50+ entries stored.
        """
        try:
            response = self.client.table('taskHistory').select(
                'historyId', count='exact'
            ).eq('userId', user_id).execute()
            
            return response.count
        
        except Exception as e:
            print(f"Error counting history: {e}")
            return 0