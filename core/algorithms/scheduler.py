from datetime import time, timedelta, datetime
from core.data_structures.priority_queue import PriorityQueue
from core.data_structures.interval_tree import IntervalTree

class GreedyScheduler:
    HIGH_PRIORITY_THRESHOLD = 7
    LOW_PRIORITY_THRESHOLD = 4

    def __init__(self):
        self.conflict_tree = IntervalTree()
        self.waitlist = PriorityQueue()

    def _get_peak_hours(self, user_chronotype):
        """
        Get peak productivity hours based on user chronotype

        Args:
            user_chronotype: 'Early', 'Middle', or 'Late'

        Returns:
            tuple: (start_hour, end_hour) in 24-hour format
        """
        chronotype_peak_hours = {
            'Early': (6, 12),      # 6 AM - 12 PM (Morning chronotype)
            'Middle': (10, 16),    # 10 AM - 4 PM (Intermediate chronotype)
            'Late': (14, 20),      # 2 PM - 8 PM (Evening chronotype)
        }

        return chronotype_peak_hours.get(user_chronotype, (6, 22))

    def _time_to_minutes(self, time_obj):
        """
        Convert time object to minutes since midnight

        Args:
            time_obj: datetime.time object

        Returns:
            int: Total minutes since midnight
        """
        if isinstance(time_obj, time):
            return time_obj.hour * 60 + time_obj.minute
        elif isinstance(time_obj, datetime):
            return time_obj.hour * 60 + time_obj.minute
        else:
            raise TypeError(f"Expected time or datetime object, got {type(time_obj)}")

    def _minutes_to_time(self, minutes):
        """
        Convert minutes since midnight to time object

        Args:
            minutes: Minutes since midnight

        Returns:
            datetime.time: Time object
        """
        hours = minutes // 60
        mins = minutes % 60
        return time(hours, mins)

    def _find_earliest_slot(self, task_length, search_window, date):
        """
        Find earliest available time slot for a task

        Args:
            task_length: Duration of task in hours
            search_window: Tuple of (start_hour, end_hour)
            date: Date to search on

        Returns:
            dict: {'start': time, 'end': time} or None if no slot found
        """
        start_hour, end_hour = search_window
        start_minutes = start_hour * 60
        end_minutes = end_hour * 60
        task_duration_minutes = int(task_length * 60)

        # ADDED: Validation
        if task_duration_minutes <= 0:
            print(f"WARNING: Invalid task length: {task_length} hours")
            return None

        if task_duration_minutes > (end_minutes - start_minutes):
            print(f"WARNING: Task too long ({task_length}hrs) for search window ({start_hour}-{end_hour})")
            return None

        current_time = start_minutes

        while current_time + task_duration_minutes <= end_minutes:
            slot_start = current_time
            slot_end = current_time + task_duration_minutes

            # Check if this slot conflicts with existing schedule
            conflicts = self.conflict_tree.query_overlaps(slot_start, slot_end)

            if not conflicts:  # No conflicts found
                return {
                    'start': self._minutes_to_time(slot_start),
                    'end': self._minutes_to_time(slot_end)
                }

            # Move to next potential slot (after the conflicting task ends)
            max_conflict_end = max(conflict[1] for conflict in conflicts)
            current_time = max_conflict_end

        # No available slot found in search window
        return None

    def add_regular_task(self, task, start_time, length, date):
        # Add a regular task to the conflict tree
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = start_minutes + int(length * 60)
        scheduled_results = []

        print(f"[SCHEDULER] Adding regular task '{task}' to schedule")
        schedule_entry = {
            'task': task,
            'start_time': start_time,
            'end_time': self._minutes_to_time(end_minutes),
            'date': date  # Date can be set as needed
        }
        scheduled_results.append(schedule_entry)

        self.conflict_tree.insert(
            start_minutes,
            end_minutes,
            schedule_entry
        )
        return scheduled_results


    def schedule_tasks(self, tasks, user_chronotype, date, existing_schedule=None):
        """
        Schedule tasks using greedy algorithm

        Args:
            tasks: List of Task objects
            user_chronotype: 'morning', 'evening', or 'intermediate'
            date: Date to schedule for
            existing_schedule: List of already scheduled tasks

        Returns:
            tuple: (scheduled_tasks, waitlist_tasks)
        """

        print(f"[SCHEDULER] Starting with {len(tasks)} tasks")
        print(f"[SCHEDULER] Chronotype: {user_chronotype}")

        # CRITICAL FIX: Reset data structures for new scheduling run
        self.conflict_tree = IntervalTree()
        self.waitlist = PriorityQueue()

        # Sort tasks by priority (descending)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        print("[SCHEDULER] Tasks sorted by priority:")
        for i, task in enumerate(sorted_tasks):
            print(f"  {i+1}. {task.name}: Priority={task.priority}, Length={task.length}hrs")

        # Get chronotype peak hours
        peak_hours = self._get_peak_hours(user_chronotype)
        print(f"[SCHEDULER] Peak hours for {user_chronotype}: {peak_hours[0]}:00 - {peak_hours[1]}:00")

        # Initialize conflict tree with existing schedule
        if existing_schedule:
            print(f"[SCHEDULER] Loading {len(existing_schedule)} existing schedules into conflict tree")
            for scheduled in existing_schedule:
                self.conflict_tree.insert(
                    self._time_to_minutes(scheduled.start_time),
                    self._time_to_minutes(scheduled.end_time),
                    (self._time_to_minutes(scheduled.start_time), self._time_to_minutes(scheduled.end_time))
                )
        else:
            print("[SCHEDULER] No existing schedule to load")

        scheduled_results = []

        for task in sorted_tasks:
            print(f"\n[SCHEDULER] Processing: {task.name} (Priority: {task.priority})")

            slot = None

            # CRITICAL FIX: Changed from > to >= for inclusive threshold
            if task.priority >= self.HIGH_PRIORITY_THRESHOLD:
                print(f"  → High priority task, first searching in peak hours: {peak_hours}")

                # First try peak hours (optimal placement)
                slot = self._find_earliest_slot(
                    task.length,
                    peak_hours,
                    date
                )

                # If no slot in peak hours, try any available slot in full day
                if not slot:
                    print(f"  → Peak hours full, searching entire day for high priority task")
                    slot = self._find_earliest_slot(
                        task.length,
                        (6, 22),  # Full day
                        date
                    )
            else:
                print(f"  → Normal priority task, searching full day: (6, 22)")
                search_window = (6, 22)  # 6am - 10pm (full day)
                slot = self._find_earliest_slot(
                    task.length,
                    search_window,
                    date
                )

            if slot:
                print(f"  ✓ Slot found: {slot['start']} - {slot['end']}")

                # Create schedule entry
                schedule_entry = {
                    'task': task,
                    'start_time': slot['start'],
                    'end_time': slot['end'],
                    'date': date
                }
                scheduled_results.append(schedule_entry)

                # Add to conflict tree
                self.conflict_tree.insert(
                    self._time_to_minutes(slot['start']),
                    self._time_to_minutes(slot['end']),
                    schedule_entry
                )
            else:
                print(f"  ✗ No slot available, adding to waitlist")
                # No slot found, add to waitlist
                self.waitlist.push(task.priority, task)

        # Process waitlist tasks
        waitlist_results = []
        while not self.waitlist.is_empty():
            _, task = self.waitlist.pop()
            waitlist_results.append(task)

        print(f"\n[SCHEDULER] Completed: {len(scheduled_results)} scheduled, {len(waitlist_results)} waitlisted")

        return scheduled_results, waitlist_results