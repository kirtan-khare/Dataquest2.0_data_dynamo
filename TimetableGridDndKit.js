import React, { useState, useEffect, useContext } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Box, Paper, Typography, Tooltip } from '@mui/material';
import { AuthContext } from '../contexts/AuthContext';

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const periods = ['9:00', '10:00', '11:00', '12:00', '1:00', '2:00'];

function DraggableCourse({ id, course }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    userSelect: 'none',
    padding: '8px',
    marginBottom: '8px',
    backgroundColor: '#4a90e2',
    color: 'white',
    borderRadius: 4,
    boxShadow: '0px 2px 5px rgba(0,0,0,0.2)',
    cursor: 'grab',
  };

  return (
    <Tooltip title={`Room: ${course.room}`}>
      <Paper ref={setNodeRef} style={style} {...attributes} {...listeners} elevation={3}>
        <Typography variant="subtitle1">{course.name}</Typography>
        <Typography variant="caption">{course.professor}</Typography>
      </Paper>
    </Tooltip>
  );
}

function transformScheduleToTimetable(schedule) {
  const timetable = {};

  days.forEach((day) => {
    periods.forEach((period) => {
      timetable[`${day}-${period}`] = [];
    });
  });

  schedule.forEach((course) => {
    const key = `${course.day}-${course.time}`;
    if (timetable[key]) timetable[key].push(course);
    else timetable[key] = [course];
  });

  return timetable;
}

export default function TimetableGridDndKit({ scheduleOutput = [] }) {
  const { token } = useContext(AuthContext);
  const [timetable, setTimetable] = useState(() => transformScheduleToTimetable(scheduleOutput));
  const [message, setMessage] = useState(null);

  useEffect(() => {
    setTimetable(transformScheduleToTimetable(scheduleOutput));
  }, [scheduleOutput]);

  const sensors = useSensors(useSensor(PointerSensor));
  const [activeSlot, setActiveSlot] = useState(null);

  const handleDragStart = (event) => {
    const [slotId] = event.active.id.split('__');
    setActiveSlot(slotId);
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setMessage(null);

    if (!over) {
      setActiveSlot(null);
      return;
    }

    const [activeSlotId, activeCourseId] = active.id.split('__');
    const [overSlotId] = over.id.split('__');

    if (activeSlotId === overSlotId) {
      setActiveSlot(null);
      return;
    }

    const activeSlotCourses = timetable[activeSlotId];
    const movedCourse = activeSlotCourses.find((c) => c.id === activeCourseId);

    const overSlotCourses = timetable[overSlotId] || [];
    const isRoomConflict = overSlotCourses.some(c => c.room === movedCourse.room);
    const isProfessorConflict = overSlotCourses.some(c => c.professor === movedCourse.professor);

    if (isRoomConflict) {
      setMessage({ text: `Conflict: Room ${movedCourse.room} is already booked.`, type: 'error' });
      setActiveSlot(null);
      return;
    }
    if (isProfessorConflict) {
      setMessage({ text: `Conflict: ${movedCourse.professor} is already scheduled at this time.`, type: 'error' });
      setActiveSlot(null);
      return;
    }

    setTimetable((prev) => {
      const updatedPrev = { ...prev };
      const newActiveCourses = updatedPrev[activeSlotId].filter(c => c.id !== activeCourseId);
      const newOverCourses = [...updatedPrev[overSlotId], { ...movedCourse, day: overSlotId.split('-')[0], time: overSlotId.split('-')[1] }];
      return {
        ...prev,
        [activeSlotId]: newActiveCourses,
        [overSlotId]: newOverCourses,
      };
    });

    const updatedTimetable = { ...movedCourse, day: overSlotId.split('-')[0], time: overSlotId.split('-')[1] };
    try {
      const response = await fetch('http://localhost:8000/update_timetable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updatedTimetable),
      });

      if (!response.ok) {
        throw new Error('Failed to save changes to the backend.');
      }
      setMessage({ text: 'Changes saved successfully!', type: 'success' });
    } catch (err) {
      setMessage({ text: err.message, type: 'error' });
    }

    setActiveSlot(null);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" gutterBottom>
        Drag courses between timetable slots
      </Typography>
      {message && (
        <Typography color={message.type === 'error' ? 'error' : 'primary'} sx={{ mt: 2, textAlign: 'center' }}>
          {message.text}
        </Typography>
      )}
      <Box
        component="table"
        sx={{
          borderCollapse: 'collapse',
          width: '100%',
          '& th, & td': {
            border: '1px solid #e0e0e0',
            padding: 1.5,
            textAlign: 'center',
          },
          '& th': {
            backgroundColor: 'primary.main',
            color: 'white',
            fontWeight: 'bold',
          },
        }}
        aria-label="Timetable"
      >
        <thead>
          <tr>
            <th>Time / Day</th>
            {days.map((day) => (
              <th key={day}>{day}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {periods.map((period) => (
            <tr key={period}>
              <td style={{ fontWeight: 'bold' }}>{period}</td>
              {days.map((day) => {
                const slotId = `${day}-${period}`;
                const courses = timetable[slotId] || [];
                return (
                  <td
                    key={slotId}
                    style={{
                      verticalAlign: 'top',
                      minHeight: 80,
                      backgroundColor: activeSlot === slotId ? 'rgba(74, 144, 226, 0.1)' : 'transparent',
                      transition: 'background-color 0.2s ease',
                    }}
                  >
                    <DndContext
                      sensors={sensors}
                      collisionDetection={closestCenter}
                      onDragStart={handleDragStart}
                      onDragEnd={handleDragEnd}
                    >
                      <SortableContext
                        id={slotId}
                        items={courses.map((c) => `${slotId}__${c.id}`)}
                        strategy={verticalListSortingStrategy}
                      >
                        {courses.length === 0 && (
                          <Typography variant="caption" color="textSecondary" sx={{ fontStyle: 'italic' }}>
                            (empty)
                          </Typography>
                        )}
                        {courses.map((course) => (
                          <DraggableCourse key={`${slotId}__${course.id}`} id={`${slotId}__${course.id}`} course={course} />
                        ))}
                      </SortableContext>
                    </DndContext>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </Box>
    </Box>
  );
}
