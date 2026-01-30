import os
import csv
from io import StringIO
from datetime import datetime, date, time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from dotenv import load_dotenv

# Import  modules
from services.database_client import SupabaseClient
from core.models.user import User
from core.models.task import Task
from core.models.schedule import Schedule
from core.models.regular_task import RegularTask
from core.algorithms.scheduler import GreedyScheduler
from core.algorithms.history import HistoryService

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Initialize scheduler
scheduler = GreedyScheduler()

# Supabase client
db = SupabaseClient()

# History service
history_service = HistoryService()


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = db.login(email, password)
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['chronotype'] = user['chronotype']
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        chronotype = request.form['chronotype']

        try:
            user = db.signup(email, password, chronotype)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get today's scheduled tasks
    try:
        schedules = db.get_client().table('schedules') \
            .select('*, tasks(name, priority), regularTasks(name, length)') \
            .eq('user_id', session['user_id']) \
            .eq('date', date.today().isoformat()) \
            .order('start_time') \
            .execute()
        
        tasks = db.get_client().table('tasks').select('*').eq('user_id', session['user_id']).execute()
        regular_tasks = db.get_client().table('regularTasks').select('*').eq('userId', session['user_id']).execute()

        return render_template('dashboard.html', 
                               schedules=schedules.data if schedules.data else [], 
                               tasks=tasks.data if tasks.data else [], 
                               regular_tasks=regular_tasks.data if regular_tasks.data else [],
                               today=date.today())
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', schedules=[], tasks=[], today=date.today())

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        is_regular = request.form.get('isRegular')

        if is_regular == 'true':
            try: 
                reg_task_data = {
                    'user_id': session['user_id'],
                    'name': request.form['name'],
                    'length': float(request.form['length']),
                    'start_time': request.form['start_time']
                }

                task = RegularTask(**reg_task_data)

                response = db.get_client().table('regularTasks').insert(task.to_dict()).execute()

                if response.data:
                    flash('Regular task created successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Failed to create task', 'error')
                
            except Exception as e:
                flash((f'Error creating task: {str(e)}', 'error'))
            
        else:
            try:
                task_data = {
                    'user_id': session['user_id'],
                    'name': request.form['name'],
                    'effort': int(request.form['effort']),
                    'urgency': int(request.form['urgency']),
                    'length': float(request.form['length'])
                }

                # Validate using our Task model
                task = Task(**task_data)

                # Insert into database
                response = db.get_client().table('tasks').insert(task.to_dict()).execute()

                if response.data:
                    flash('Task created successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Failed to create task', 'error')

            except Exception as e:
                flash(f'Error creating task: {str(e)}', 'error')

    return render_template('create_tasks.html')

@app.route('/generate_schedule', methods=['POST'])
def generate_schedule():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        print("=== STEP 1: Fetching tasks ===")
        # Get user's tasks
        tasks_response = db.get_client().table('tasks').select('*').eq('user_id', session['user_id']).execute()
        regular_tasks_response = db.get_client().table('regularTasks').select('*').eq('userId', session['user_id']).execute()

        print(f"Tasks response: {tasks_response.data}")
        print(f"Regular tasks response: {regular_tasks_response.data}")

        if not tasks_response.data:
            return jsonify({'error': 'No tasks found. Please create tasks first.'}), 400

        print("=== STEP 2: Converting to Task objects + building regular entries ===")
        # Convert to Task objects
        tasks = []
        for task_data in tasks_response.data:
            print(f"Processing task: {task_data}")
            task = Task(
                task_id=task_data['task_id'],
                user_id=task_data['user_id'],
                name=task_data['name'],
                effort=task_data['effort'],
                urgency=task_data['urgency'],
                length=task_data['length'],
                priority=task_data.get('priority')
                
            )
            print(f"Created Task object: priority={task.priority}")
            tasks.append(task)

        # Build regular task schedule entries
        regular_tasks = []
        reg_schedule_entry = []

        for reg_task_data in regular_tasks_response.data:
            print(f"Processing regular task: {reg_task_data}")
            
            reg_task = RegularTask(
                regular_task_id=reg_task_data['regularTaskId'],
                user_id=reg_task_data['userId'],
                name=reg_task_data['name'],
                length=reg_task_data['length'],
                start_time=reg_task_data['start_time']
            )
            regular_tasks.append(reg_task)
            
            # Build schedule entry
            start_time_obj = datetime.strptime(reg_task.start_time, '%H:%M:%S').time()
            end_minutes = (start_time_obj.hour * 60 + start_time_obj.minute) + int(reg_task.length * 60)
            
            reg_schedule_entry.append({
                'user_id': session['user_id'],
                'task_id': None,
                'regular_task_id': reg_task.regular_task_id,
                'start_time': start_time_obj.isoformat(),
                'end_time': time(end_minutes // 60, end_minutes % 60).isoformat(),
                'date': date.today().isoformat(),
                'is_regular_task': True
            })

        print("=== STEP 3: Fetching existing schedules ===")
        # Get existing schedule for today
        existing_schedules = []
        schedule_response = db.get_client().table('schedules').select('*').eq('user_id', 
            session['user_id']).eq('date', date.today().isoformat()).execute()

        print(f"Existing schedules: {schedule_response.data}")

        if schedule_response.data:
            for sched_data in schedule_response.data:
                try:
                    existing_schedules.append(Schedule(
                        schedule_id=sched_data['schedule_id'],
                        user_id=sched_data['user_id'],
                        task_id=sched_data['task_id'],
                        #task_name=sched_data['task_name'],
                        start_time=datetime.fromisoformat(sched_data['start_time']).time(),
                        end_time=datetime.fromisoformat(sched_data['end_time']).time(),
                        date=datetime.fromisoformat(sched_data['date']).date()
                    ))
                except Exception as e:
                    print(f"Error parsing schedule: {e}, data: {sched_data}")
                    continue

        print("=== STEP 4: Scheduling regular tasks ===")
        # First schedule regular tasks at their preferred times
        for reg_task in regular_tasks:
            if reg_task.length is None or reg_task.start_time is None:
                print(f"Skipping regular task {reg_task.name}: missing length or start_time")
                continue
            try:
                scheduler.add_regular_task(
                    reg_task,
                    reg_task.start_time,
                    reg_task.length,
                    date.today()
                )
                # Fix: Align this print statement with the scheduler call above
                print(f"Scheduled regular task: {reg_task.name} at {reg_task.start_time}")
            except Exception as e:
                print(f"Error scheduling regular task {reg_task.name}: {str(e)}")
                

        print("=== STEP 5: Running scheduler ===")
        # Generate schedule using greedy algorithm
        scheduled, waitlist = scheduler.schedule_tasks(
            tasks,
            session.get('chronotype', 'Early'),
            date.today(),
            existing_schedules
        )

        print(f"Scheduled: {len(scheduled)} tasks")
        print(f"Waitlist: {len(waitlist)} tasks")
        print(f"Scheduled entries: {scheduled}")

        print("=== STEP 6: Building schedule entries ===")
        # Build schedule entries
        schedule_entries = []
        for entry in scheduled:
            print(f"Entry: {entry}")
            print(f"Task: {entry['task']}")
            print(f"Task ID: {entry['task'].task_id}")
            
            schedule_entry = {
                'user_id': session['user_id'],
                'task_id': entry['task'].task_id,
                #'task_name': entry['task'].name,
                'start_time': entry['start_time'].isoformat(),
                'end_time': entry['end_time'].isoformat(),
                'date': entry['date'].isoformat(),
                'is_regular_task': False
            }
            print(f"Built schedule entry: {schedule_entry}")
            schedule_entries.append(schedule_entry)

        print("=== STEP 7: Inserting into database ===")
        all_schedule_entries = schedule_entries + reg_schedule_entry
        if all_schedule_entries:

            clear_existing = db.get_client().table('schedules').delete().eq('user_id', 
                session['user_id']).eq('date', date.today().isoformat()).execute()
            print(f"Cleared existing schedules: {clear_existing}")

            print(f"Inserting {len(all_schedule_entries)} entries")
            print(f"Entry data: {all_schedule_entries}")
            
            # Insert new schedules
            insert_response = db.get_client().table('schedules').insert(all_schedule_entries).execute()
            
            print(f"Insert response: {insert_response}")
            print(f"Insert response data: {insert_response.data}")
            
            if not insert_response.data:
                raise Exception("Database insertion returned no data")
        else:
            print("No schedule entries to insert")

        print("=== SUCCESS ===")
        flash(f'Schedule generated! Successfully scheduled {len(scheduled)} tasks.', 'success')
        return redirect(url_for('dashboard'))
        

    except Exception as e:
        print(f"=== ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        # Get user's schedule for today
        response = db.get_client().table('schedules').select('*').eq('user_id', 
            session['user_id']).eq('date', date.today().isoformat()).execute()

        if not response.data:
            flash('No schedule to export', 'warning')
            return redirect(url_for('dashboard'))

        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Task Name', 'Start Time', 'End Time', 'Date', 'Priority'])

        for sched in response.data:
            # Get task details
            task_response = db.get_client().table('tasks').select('name', 
                'urgency').eq('task_id', sched['task_id']).execute()
            
            if task_response.data:
                task_name = task_response.data[0]['name']
                priority = task_response.data[0]['urgency']

                writer.writerow([
                    task_name,
                    sched['start_time'],
                    sched['end_time'],
                    sched['date'],
                    priority
                ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=schedule_{date.today()}.csv'}
        )

    except Exception as e:
        flash(f'Error exporting CSV: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        # Delete schedules pointing to standard tasks
        db.get_client().table('schedules').delete().eq('task_id', task_id).execute()
        # Delete schedules pointing to regular tasks
        db.get_client().table('schedules').delete().eq('regular_task_id', task_id).execute()
        # Delete the tasks 
        db.get_client().table('tasks').delete().eq('task_id', task_id).execute()
        db.get_client().table('regularTasks').delete().eq('regularTaskId', task_id).execute()

        flash('Task deleted successfully.')
        return redirect(url_for('dashboard'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/complete_task/<schedule_id>', methods=['POST'])
def complete_task(schedule_id):
    """Record task completion in history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Get schedule details
        sched_response = db.get_client().table('schedules').select(
            '*, tasks(name)'
        ).eq('schedule_id', schedule_id).execute()
        
        if not sched_response.data:
            return jsonify({'error': 'Schedule not found'}), 404
        
        schedule = sched_response.data[0]
        
        # Record to history
        success = history_service.record_task_completion(
            user_id=session['user_id'],
            task_id=schedule['task_id'],
            start_time=time.fromisoformat(schedule['start_time']),
            end_time=time.fromisoformat(schedule['end_time']),
            date_obj=datetime.fromisoformat(schedule['date']).date()
        )
        
        if success:
            completed = session.get('completed_tasks', [])
            completed.append(schedule_id)
            session['completed_tasks'] = completed
            session.modified = True
            flash('Task marked as complete!', 'success')
        else:
            flash('Failed to record completion', 'error')
        
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        print(f"Error in complete_task: {e}")
        return redirect(url_for('dashboard'))
    

@app.route('/history')
def view_history():
    """Display task history to user"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get history for last 90 days (Objective 3b)
        history = history_service.get_task_history(
            user_id=session['user_id'],
            limit=50  # Objective 3a
        )
        
        # Get total count for display
        total_count = history_service.get_history_count(session['user_id'])
        
        # Get most frequent tasks (Objective 5)
        task_freq = history_service.get_task_frequency(session['user_id'])
        recommended = []
        sorted_tasks = sorted(task_freq.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        for name, data in sorted_tasks:
            recommended.append((name, data['count'], data['task_id']))
        
        return render_template('history.html', 
                             history=history,
                             total_count=total_count,
                             recommended_tasks=recommended)
    
    except Exception as e:
        flash(f'Error loading history: {str(e)}', 'error')
        return render_template('history.html', history=[], total_count=0)

@app.route('/admin/cleanup_history', methods=['POST'])
def cleanup_old_history():
    """
    Maintenance endpoint for automated cleanup.
    Objective 3b: Remove records older than 90 days.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    success = history_service.delete_old_history(session['user_id'], days=90)
    
    return jsonify({'success': success})

@app.route('/add_again/<task_id>', methods=['POST'])
def add_again(task_id):
    """Add a recommended task again for the user"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Fetch task details
        task_response = db.get_client().table('tasks').select('*')\
            .eq('user_id', session['user_id'])\
            .eq('task_id', task_id).single().execute()
        
        if not task_response.data:
            flash('Task not found', 'error')
            return redirect(url_for('view_history'))
        
        task_data = task_response.data
        
        # Create new task entry
        new_task = {
            'user_id': session['user_id'],
            'name': task_data['name'],
            'effort': task_data['effort'],
            'urgency': task_data['urgency'],
            'length': task_data['length']
        }
        
        insert_response = db.get_client().table('tasks').insert(new_task).execute()
        
        if insert_response.data:
            flash(f'Task "{task_data["name"]}" added again!', 'success')
        else:
            flash('Failed to add task', 'error')
        
        return redirect(url_for('view_history'))
    
    except Exception as e:
        flash(f'Error adding task: {str(e)}', 'error')
        return redirect(url_for('view_history'))
    
@app.route('/adjust_task/<task_id>', methods = ['POST'])
def adjust_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        task = db.get_client().table('tasks').select('*')\
        .eq('user_id', session['user_id'])\
        .eq('task_id', task_id).execute()

        if not task.data:
            flash('Task not found', 'error')
            return '<script>window.opener.location.reload(); window.close();</script>'
        
        task_data = task.data[0]

        new_task = {
            'user_id': session['user_id'],
            'name': task_data['name'],
            'effort': int(request.form['effort']),
            'urgency': int(request.form['urgency']),
            'length': float(request.form['length'])
        }

        insert = db.get_client().table('tasks').insert(new_task).execute()
        delete = db.get_client().table('tasks').delete()\
        .eq('user_id', session['user_id'])\
        .eq('task_id', task_id).execute()

        if insert.data:
            flash(f'task {task_data["name"]} adjusted', 'sucess')
        else:
            flash('Failed to adjust task', 'error')

        return '<script>window.opener.location.reload(); window.close();</script>'
    
    except Exception as e:
        flash(f'Error adjusting task: {str(e)}', 'error')
        return '<script>window.opener.location.reload(); window.close();</script>'
    
@app.route('/adjust_task_popup/<task_id>')
def adjust_task_popup(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = db.get_client().table('tasks').select('*')\
        .eq('user_id', session['user_id'])\
        .eq('task_id', task_id).execute()
    
    if not task.data:
        flash('Task not found', 'error')
        return redirect(url_for('dashboard'))
    
    task_data = task.data[0]

    return render_template('popup.html', task=task_data)


        

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5051)

