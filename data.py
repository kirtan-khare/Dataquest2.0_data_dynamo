import pandas as pd
import random

departments = ['CSE', 'ECE', 'ME', 'CE']
subjects = {
    'CSE': ['Algorithms', 'Data Structures', 'AI'],
    'ECE': ['Circuits', 'Signal Processing', 'Microprocessors'],
    'ME': ['Thermodynamics', 'Fluid Mechanics'],
    'CE': ['Geotechnical', 'Structural Analysis']
}

# Courses with dynamic departments
courses = []
course_id = 1
for dept, subs in subjects.items():
    for sub in subs:
        courses.append({
            'course_id': course_id,
            'course_name': sub,
            'dept_code': dept,
            'required_room_type': 'Lecture'
        })
        course_id += 1
courses_df = pd.DataFrame(courses)
courses_df.to_csv('courses.csv', index=False)

# Rooms (shared by all departments)
rooms = []
for i in range(1, 11):
    rooms.append({
        'room_id': i,
        'room_name': f'Room_{i}',
        'dept_code': random.choice(departments),
        'room_type': random.choice(['Lecture', 'Lab']),
        'capacity': random.choice([30, 40, 50])
    })
rooms_df = pd.DataFrame(rooms)
rooms_df.to_csv('rooms.csv', index=False)

# Timeslots (common)
timeslots = []
days = ['Mon','Tue','Wed','Thu','Fri']
for day_idx, day in enumerate(days):
    for period in range(6):
        timeslots.append({
            'timeslot_id': day_idx * 6 + period,
            'day': day,
            'start_time': f'{9+period}:00'
        })
timeslots_df = pd.DataFrame(timeslots)
timeslots_df.to_csv('timeslots.csv', index=False)

# Professors per department
professors = []
prof_id = 1
for dept in departments:
    for i in range(2):  # 2 professors per dept
        professors.append({
            'professor_id': prof_id,
            'name': f'Prof_{dept}_{i+1}',
            'dept_code': dept,
            'max_load_per_week': random.randint(4, 6)
        })
        prof_id += 1
professors_df = pd.DataFrame(professors)
professors_df.to_csv('professors.csv', index=False)

# Professor availability
prof_availability = []
for prof in professors:
    for ts in timeslots:
        available = 1 if random.random() < 0.7 else 0
        prof_availability.append({
            'professor_id': prof['professor_id'],
            'timeslot_id': ts['timeslot_id'],
            'available': available
        })
prof_avail_df = pd.DataFrame(prof_availability)
prof_avail_df.to_csv('prof_availability.csv', index=False)

# Students enrolled with departments and course enrollments
num_students = 60
students = []
enrollments = []
for sid in range(1, num_students + 1):
    dept = random.choice(departments)
    students.append({'student_id': sid, 'dept_code': dept})

    dept_courses = [c['course_id'] for c in courses if c['dept_code'] == dept]
    enrolled_courses = random.sample(dept_courses,
                                     min(len(dept_courses), random.randint(2, 3)))
    for cid in enrolled_courses:
        enrollments.append({'student_id': sid, 'course_id': cid})

students_df = pd.DataFrame(students)
students_df.to_csv('students.csv', index=False)
enrollments_df = pd.DataFrame(enrollments)
enrollments_df.to_csv('enrollments.csv', index=False)

# Preferred timeslots for courses
course_pref = []
num_timeslots = len(timeslots)
for c in courses:
    prefs = random.sample(range(num_timeslots), random.randint(1, 3))
    for ts in prefs:
        course_pref.append({'course_id': c['course_id'], 'timeslot_id': ts})
course_pref_df = pd.DataFrame(course_pref)
course_pref_df.to_csv('course_preferred_timeslots.csv', index=False)

print("Dynamic dataset generated in data/ folder.")
