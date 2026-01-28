"""CSV export utility (Objective 17)"""
import csv
from datetime import datetime

class CSVExporter:
    """Export user data to CSV format"""
    
    @staticmethod
    def export_schedule(schedules, tasks, filename=None):
        """Export schedule data to CSV"""
        if filename is None:
            filename = f"timely_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create task lookup dictionary
        task_dict = {task.task_id: task for task in tasks}
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Start Time', 'End Time', 'Task Name', 'Priority', 'Duration (hours)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for schedule in schedules:
                task = task_dict.get(schedule.task_id)
                
                writer.writerow({
                    'Date': schedule.date.isoformat(),
                    'Start Time': schedule.start_time.isoformat(),
                    'End Time': schedule.end_time.isoformat(),
                    'Task Name': task.name if task else 'Unknown',
                    'Priority': task.priority if task else 'N/A',
                    'Duration (hours)': schedule.get_duration_hours()
                })
        
        return filename
    
    @staticmethod
    def export_task_history(history, filename=None):
        """Export task history to CSV"""
        if filename is None:
            filename = f"timely_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Task Name', 'Start Time', 'End Time', 'Duration (hours)', 'Completed At']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for record in history:
                # Calculate duration
                start_minutes = record['start_time'].hour * 60 + record['start_time'].minute
                end_minutes = record['end_time'].hour * 60 + record['end_time'].minute
                duration = (end_minutes - start_minutes) / 60
                
                writer.writerow({
                    'Date': record['date'].isoformat(),
                    'Task Name': record['task_name'],
                    'Start Time': record['start_time'].isoformat(),
                    'End Time': record['end_time'].isoformat(),
                    'Duration (hours)': round(duration, 2),
                    'Completed At': record['completed_at']
                })
        
        return filename