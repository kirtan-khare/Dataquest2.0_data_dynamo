import pandas as pd
import random
from collections import defaultdict

# Load all base datasets
courses_df = pd.read_csv('courses.csv')
rooms_df = pd.read_csv('rooms.csv')
timeslots_df = pd.read_csv('timeslots.csv')
professors_df = pd.read_csv('professors.csv')
prof_avail_df = pd.read_csv('prof_availability.csv')
students_df = pd.read_csv('students.csv')
enrollments_df = pd.read_csv('enrollments.csv')
course_pref_df = pd.read_csv('course_preferred_timeslots.csv')

POPULATION_SIZE = 100
GENERATIONS = 50
MUTATION_RATE = 0.15

def ga_scheduler_for_department(dept_code):
    # Filter data for the department
    dept_courses = courses_df[courses_df['dept_code'] == dept_code].reset_index(drop=True)
    dept_professors = professors_df[professors_df['dept_code'] == dept_code].reset_index(drop=True)
    dept_students = students_df[students_df['dept_code'] == dept_code]['student_id'].tolist()
    dept_enrollments = enrollments_df[enrollments_df['student_id'].isin(dept_students)]

    # Mappings
    course_dept = dept_courses.set_index('course_id')['dept_code'].to_dict()
    professors_by_dept = dept_professors['professor_id'].tolist()
    prof_avail_map = prof_avail_df[prof_avail_df['available'] == 1]
    prof_avail_map = prof_avail_map[prof_avail_map['professor_id'].isin(professors_by_dept)]
    prof_avail_map = prof_avail_map.groupby('professor_id')['timeslot_id'].apply(set).to_dict()

    # Map courses -> professors for this dept
    course_profs = {cid: professors_by_dept for cid in dept_courses['course_id']}

    room_cap = rooms_df.set_index('room_id')['capacity'].to_dict()
    room_type = rooms_df.set_index('room_id')['room_type'].to_dict()
    course_roomreq = dept_courses.set_index('course_id')['required_room_type'].to_dict()

    # Students enrolled in each course (dept-level filtered)
    course_students = dept_enrollments.groupby('course_id')['student_id'].apply(set).to_dict()

    student_course_map = dept_enrollments.groupby('student_id')['course_id'].apply(set).to_dict()

    # Preferred timeslots for dept courses
    course_pref_map = course_pref_df[course_pref_df['course_id'].isin(dept_courses['course_id'])]
    course_pref_map = course_pref_map.groupby('course_id')['timeslot_id'].apply(set).to_dict()

    def create_individual():
        individual = []
        for _, course in dept_courses.iterrows():
            cid = course['course_id']
            timeslot = random.choice(timeslots_df['timeslot_id'])
            possible_rooms = [r for r in rooms_df['room_id']
                              if room_type[r] == course_roomreq.get(cid, 'Lecture') and room_cap[r] >= 30]

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

                possible_rooms = [r for r in rooms_df['room_id']
                                  if room_type[r] == course_roomreq.get(cid, 'Lecture') and room_cap[r] >= 30]
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

    def print_and_save_timetable(best_schedule):
        timetable = {day: {period: [] for period in range(6)} for day in timeslots_df['day'].unique()}
        for gene in best_schedule:
            cid, ts, room, prof = gene
            course_name = dept_courses.loc[dept_courses['course_id'] == cid, 'course_name'].values[0]
            room_name = rooms_df.loc[rooms_df['room_id'] == room, 'room_name'].values[0]
            prof_name = (dept_professors.loc[dept_professors['professor_id'] == prof, 'name'].values[0]
                         if prof is not None else "NA")
            day = timeslots_df.loc[timeslots_df['timeslot_id'] == ts, 'day'].values[0]
            start_time = timeslots_df.loc[timeslots_df['timeslot_id'] == ts, 'start_time'].values[0]
            period = int(start_time.split(":")[0]) - 9

            timetable[day][period].append(f"{course_name} ({room_name}, {prof_name})")

        df_dict = {}
        for day, periods in timetable.items():
            df_dict[day] = [", ".join(periods[p]) if periods[p] else "" for p in range(6)]

        timetable_df = pd.DataFrame(df_dict, index=[f"Period {i+1}" for i in range(6)])
        print(f"\nTimetable for {dept_code}:")
        print(timetable_df)
        timetable_df.to_csv(f"optimized_timetable_{dept_code}.csv")
        print(f"Saved to optimized_timetable_{dept_code}.csv")

    best_schedule = genetic_algorithm()
    print_and_save_timetable(best_schedule)

def main():
    for dept in sorted(courses_df['dept_code'].unique()):
        ga_scheduler_for_department(dept)

if __name__ == "__main__":
    main()
