Project Overview
This project is a web-based Timetable Management System designed to automate the process of creating and managing university or school timetables. It uses a genetic algorithm to generate an optimized schedule and provides a user-friendly interface for managing and viewing the timetable, as well as handling substitute teachers. The system is built using Python for the backend logic and React with Material-UI for the frontend.

Core Components and Features
1. Genetic Algorithm for Timetable Generation
 - The timetable_generator.py script is the core of the system's scheduling logic. It uses a genetic algorithm to solve the complex problem of creating an optimal timetable. This approach is well-suited for this task because it can handle a large number of constraints simultaneously.

 - Individuals and Population: A single "individual" represents a complete timetable, which is a list of tuples (course_id, timeslot, room, professor). The "population" is a collection of these timetables.

 - Fitness Function: This function evaluates how "good" a timetable is. It assigns a score based on a set of rules and constraints:

 - Positive Score: Rewarded for assigning courses to their preferred timeslots, and for valid room and professor assignments.

 - Negative Score (Penalties): Deducted for conflicts and rule violations, such as:

 - A room being double-booked at the same time.

 - A professor being scheduled for two different courses at once.

 - A student having multiple classes at the same time.

 - A professor being scheduled when they are unavailable.

 - A professor's weekly course load exceeding their maximum limit.

 - Evolutionary Process: The script uses a standard genetic algorithm workflow:

**Initialization: Creates a random initial population of timetables.**

**Selection: Selects the best-performing timetables (the fittest) to be parents for the next generation.**

**Crossover: Combines parts of two parent timetables to create a new child timetable.**

**Mutation: Randomly makes small changes to a child timetable to introduce new variations and prevent the algorithm from getting stuck in a local optimum.**

 - This process repeats for a set number of generations, with the goal of producing an increasingly optimized timetable with each cycle.

2. Frontend Interface and Functionality
 - The React components handle the user-facing parts of the application.

 - TimetableUploader.js: This component allows an administrator to upload a ZIP file containing all the necessary dataset CSV files (courses.csv, rooms.csv, etc.). When the file is uploaded, the backend runs the genetic algorithm to generate the timetables for each department and returns the results.

 - TimetableGridDndKit.js: This component provides an interactive, visual representation of the generated timetable. It uses the dnd-kit library to enable drag-and-drop functionality, allowing users to manually adjust the schedule. It includes a conflict detection system that warns the user if a drag-and-drop action creates a room or professor conflict. Changes made on the frontend are sent to the backend to be saved.

 - SubstituteTeacherManagement.js: This component provides a dedicated interface for managing substitute teachers. It allows users to view, add, edit, and delete records for when a teacher needs to be replaced for a specific course and timeslot.

3. Data Management
 - The data.py script is used to generate mock data for testing purposes. It creates a series of interconnected CSV files that the genetic algorithm script uses as input. This simulates a real-world scenario where the system would pull data from a database.

 - CSV files: The mock data includes courses.csv, rooms.csv, professors.csv, students.csv, and more, all with realistic relationships between them (e.g., a student is enrolled in courses from their department).
