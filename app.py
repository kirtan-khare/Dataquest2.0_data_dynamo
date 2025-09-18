import zipfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import tempfile
import shutil
import os
from collections import defaultdict
import random
from auth import router as auth_router
from substitute_management import router as substitute_router
from user_management import router as user_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(substitute_router)
app.include_router(user_router)

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

POPULATION_SIZE = 100
GENERATIONS = 50
MUTATION_RATE = 0.15

def ga_scheduler_for_department(
    dept_code,
    courses_df,
    rooms_df,
    timeslots_df,
    professors_df,
    prof_avail_df,
    students_df,
    enrollments_df,
    course_pref_df,
):
    dept_courses = courses_df[courses_df['dept_code'] == dept_code].reset_index(drop=True)
    dept_professors = professors_df[professors_df['dept_code'] == dept_code].reset_index(drop=True)
    dept_students = students_df[students_df['dept_code'] == dept_code]['student_id'].tolist()
    dept_enrollments = enrollments_df[enrollments_df['student_id'].isin(dept_students)]

    course_dept = dept_courses.set_index('course_id')['dept_code'].to_dict()
    professors_by_dept = dept_professors['professor_id'].tolist()
    prof_avail_map = prof_avail_df[prof_avail_df['available'] == 1]
    prof_avail_map = prof_avail_map[prof_avail_map['professor_id'].isin(professors_by_dept)]
    prof_avail_map = prof_avail_map.groupby('professor_id')['timeslot_id'].apply(set).to_dict()

    course_profs = {cid: professors_by_dept for cid in dept_courses['course_id']}

    room_cap = rooms_df.set_index('room_id')['capacity'].to_dict()
    room_type = rooms_df.set_index('room_id')['room_type'].to_dict()
    course_roomreq = dept_courses.set_index('course_id')['required_room_type'].to_dict()

    course_students = dept_enrollments.groupby('course_id')['student_id'].apply(set).to_dict()
    student_course_map = dept_enrollments.groupby('student_id')['course_id'].apply(set).to_dict()
    course_pref_map = course_pref_df[course_pref_df['course_id'].isin(dept_courses['course_id'])]
    course_pref_map = course_pref_map.groupby('course_id')['timeslot_id'].apply(set).to_dict()

    def create_individual():
        individual = []
        for _, course in dept_courses.iterrows():
            cid = course['course_id']
            timeslot = random.choice(timeslots_df['timeslot_id'])
            possible_rooms = [
                r for r in rooms_df['room_id']
                if room_type[r] == course_roomreq.get(cid, 'Lecture') and room_cap[r] >= 30
            ]
            if not possible_rooms:
                possible_rooms = rooms_df['room_id'].tolist()
            room = random.choice(possible_rooms)
            prof_list = course_profs.get(cid, [])
            prof = random.choice(prof_list) if prof_list else None
            individual.append((cid, timeslot, room, prof))
        return individual

    def fitness(individual):
        score = 0
        used_room_time = set()
        prof_time = defaultdict(set)
        prof_load = defaultdict(int)
        student_time_courses = defaultdict(set)

        for gene in individual:
            cid, ts, room, prof = gene

            if room_cap[room] < 30 or room_type[room] != course_roomreq.get(cid, 'Lecture'):
                score -= 5
            else:
                score += 1

            if (room, ts) in used_room_time:
                score -= 10
            else:
                used_room_time.add((room, ts))
                score += 2

            if prof is not None:
                if ts not in prof_avail_map.get(prof, set()):
                    score -= 10
                if ts in prof_time[prof]:
                    score -= 15
                prof_time[prof].add(ts)
                prof_load[prof] += 1
                score += 2
            else:
                score -= 5

            students = course_students.get(cid, set())
            for stu in students:
                if ts in student_time_courses[stu]:
                    score -= 15
                else:
                    student_time_courses[stu].add(ts)

            if ts in course_pref_map.get(cid, set()):
                score += 3

        for prof, load in prof_load.items():
            max_load = dept_professors.loc[dept_professors['professor_id'] == prof, 'max_load_per_week'].values[0]
            if load > max_load:
                score -= (load - max_load) * 10
        return score

    def selection(population):
        population.sort(key=fitness, reverse=True)
        return population[:int(0.2 * len(population))]

    def crossover(p1, p2):
        point = random.randint(1, len(p1) - 1)
        return p1[:point] + p2[point:]

    def mutate(individual):
        for i in range(len(individual)):
            if random.random() < MUTATION_RATE:
                cid, _, _, _ = individual[i]
                timeslot = random.choice(timeslots_df['timeslot_id'])

                possible_rooms = [
                    r for r in rooms_df['room_id']
                    if room_type[r] == course_roomreq.get(cid, 'Lecture') and room_cap[r] >= 30
                ]
                if not possible_rooms:
                    possible_rooms = rooms_df['room_id'].tolist()
                room = random.choice(possible_rooms)

                prof_list = course_profs.get(cid, [])
                prof = random.choice(prof_list) if prof_list else None
                individual[i] = (cid, timeslot, room, prof)
        return individual

    def genetic_algorithm():
        population = [create_individual() for _ in range(POPULATION_SIZE)]
        best = None
        best_score = float('-inf')
        for gen in range(GENERATIONS):
            selected = selection(population)
            next_pop = selected[:]
            while len(next_pop) < POPULATION_SIZE:
                p1, p2 = random.sample(selected, 2)
                child = crossover(p1, p2)
                child = mutate(child)
                next_pop.append(child)
            population = next_pop
            current_best = max(population, key=fitness)
            current_score = fitness(current_best)
            print(f"[{dept_code}] Gen {gen + 1}, Best Score: {current_score}")
            if current_score > best_score:
                best = current_best
                best_score = current_score
        return best

    def prepare_output(schedule):
        timetable = []
        for gene in schedule:
            cid, ts, room, prof = gene
            course_name = dept_courses.loc[dept_courses['course_id'] == cid, 'course_name'].values[0]
            room_name = rooms_df.loc[rooms_df['room_id'] == room, 'room_name'].values[0]
            prof_name = (dept_professors.loc[dept_professors['professor_id'] == prof, 'name'].values[0]
                         if prof is not None else "NA")
            day = timeslots_df.loc[timeslots_df['timeslot_id'] == ts, 'day'].values[0]
            start_time = timeslots_df.loc[timeslots_df['timeslot_id'] == ts, 'start_time'].values[0]
            timetable.append({
                "day": day,
                "time": start_time,
                "id": cid,
                "name": course_name,
                "professor": prof_name,
                "room": room_name,
            })
        return timetable

    best_schedule = genetic_algorithm()
    return prepare_output(best_schedule)

def run_ga_scheduling(
    courses_path,
    rooms_path,
    timeslots_path,
    professors_path,
    prof_avail_path,
    students_path,
    enrollments_path,
    course_pref_path,
):
    courses_df = pd.read_csv(courses_path)
    rooms_df = pd.read_csv(rooms_path)
    timeslots_df = pd.read_csv(timeslots_path)
    professors_df = pd.read_csv(professors_path)
    prof_avail_df = pd.read_csv(prof_avail_path)
    students_df = pd.read_csv(students_path)
    enrollments_df = pd.read_csv(enrollments_path)
    course_pref_df = pd.read_csv(course_pref_path)

    dept_timetables = {}

    for dept in sorted(courses_df['dept_code'].unique()):
        dept_timetables[dept] = ga_scheduler_for_department(
            dept,
            courses_df,
            rooms_df,
            timeslots_df,
            professors_df,
            prof_avail_df,
            students_df,
            enrollments_df,
            course_pref_df,
        )

    return dept_timetables

@app.post("/upload")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        return JSONResponse(content={"error": "Please upload a .zip file"}, status_code=400)

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, file.filename)
    try:
        with open(zip_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        required_files = ['courses.csv', 'rooms.csv', 'timeslots.csv', 'professors.csv',
                          'prof_availability.csv', 'students.csv', 'enrollments.csv', 'course_preferred_timeslots.csv']

        file_paths = {}
        for filename in required_files:
            path = os.path.join(temp_dir, filename)
            if not os.path.isfile(path):
                return JSONResponse(content={"error": f"Missing required file: {filename}"}, status_code=400)
            file_paths[filename] = path

        schedule = run_ga_scheduling(
            file_paths['courses.csv'], file_paths['rooms.csv'],
            file_paths['timeslots.csv'], file_paths['professors.csv'],
            file_paths['prof_availability.csv'], file_paths['students.csv'],
            file_paths['enrollments.csv'], file_paths['course_preferred_timeslots.csv']
        )
    finally:
        shutil.rmtree(temp_dir)

    return JSONResponse(content=schedule)

@app.get("/download")
def download_schedule():
    file_path = "optimized_timetable.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No timetable file available"}, status_code=404)
    return FileResponse(file_path, media_type="text/csv", filename="optimized_timetable.csv")
