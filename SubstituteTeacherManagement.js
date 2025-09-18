import React, { useState, useEffect, useContext } from 'react';
import {
  Typography, Box, Button, TextField, Select, MenuItem,
  FormControl, InputLabel, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Dialog,
  DialogTitle, DialogContent, DialogActions, CircularProgress
} from '@mui/material';
import { AuthContext } from '../contexts/AuthContext';

// Mock data - replace with API calls for dynamic lists
const mockTeachers = ['Alice', 'Bob', 'Charlie', 'Dave'];
const mockCourses = ['Math101', 'Physics202', 'Chemistry303'];
const mockTimeslots = ['09:00-10:00', '10:00-11:00', '11:00-12:00'];

export default function SubstituteTeacherManagement() {
  const { token, user } = useContext(AuthContext);
  const [substitutes, setSubstitutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [openDialog, setOpenDialog] = useState(false);
  const [editData, setEditData] = useState(null);

  const [date, setDate] = useState('');
  const [originalTeacher, setOriginalTeacher] = useState('');
  const [substituteTeacher, setSubstituteTeacher] = useState('');
  const [courseId, setCourseId] = useState('');
  const [timeslot, setTimeslot] = useState('');

  const fetchSubstitutes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/substitutes', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch substitutes');
      const data = await response.json();
      setSubstitutes(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (token) fetchSubstitutes();
  }, [token]);

  const openForm = (sub=null) => {
    if (sub) {
      setEditData(sub);
      setDate(sub.date);
      setOriginalTeacher(sub.original_teacher_id);
      setSubstituteTeacher(sub.substitute_teacher_id);
      setCourseId(sub.course_id);
      setTimeslot(sub.timeslot);
    } else {
      setEditData(null);
      setDate('');
      setOriginalTeacher('');
      setSubstituteTeacher('');
      setCourseId('');
      setTimeslot('');
    }
    setOpenDialog(true);
  };

  const closeForm = () => setOpenDialog(false);

  const handleDelete = async (id) => {
    if (!window.confirm('Confirm deletion?')) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/substitutes/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Delete failed');
      fetchSubstitutes();
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleSave = async () => {
    if (!date || !originalTeacher || !substituteTeacher || !courseId || !timeslot) {
      setError('All fields are required');
      return;
    }
    setLoading(true);
    setError(null);
    const payload = {
      date,
      original_teacher_id: originalTeacher,
      substitute_teacher_id: substituteTeacher,
      course_id: courseId,
      timeslot,
      id: editData?.id,
    };
    try {
      const response = await fetch(
        `http://localhost:8000/substitutes${editData ? `/${editData.id}` : ''}`,
        {
          method: editData ? 'PUT' : 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        }
      );
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Save failed');
      }
      fetchSubstitutes();
      closeForm();
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Substitute Teacher Management</Typography>
      {error && <Typography color="error">{error}</Typography>}
      <Button variant="contained" onClick={() => openForm()} sx={{ mb: 2 }}>
        Add Substitute
      </Button>
      {loading && <CircularProgress />}
      <TableContainer component={Paper}>
        <Table aria-label="substitutes">
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Original Teacher</TableCell>
              <TableCell>Substitute Teacher</TableCell>
              <TableCell>Course</TableCell>
              <TableCell>Timeslot</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {substitutes.map(sub => (
              <TableRow key={sub.id}>
                <TableCell>{sub.date}</TableCell>
                <TableCell>{sub.original_teacher_id}</TableCell>
                <TableCell>{sub.substitute_teacher_id}</TableCell>
                <TableCell>{sub.course_id}</TableCell>
                <TableCell>{sub.timeslot}</TableCell>
                <TableCell>
                  <Button onClick={() => openForm(sub)}>Edit</Button>
                  {user?.role === 'admin' && (
                    <Button color="error" onClick={() => handleDelete(sub.id)}>Delete</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={closeForm}>
        <DialogTitle>{editData ? 'Edit Substitute' : 'Add Substitute'}</DialogTitle>
        <DialogContent>
          <TextField
            label="Date"
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            fullWidth
            margin="dense"
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Original Teacher</InputLabel>
            <Select
              value={originalTeacher}
              onChange={e => setOriginalTeacher(e.target.value)}
              label="Original Teacher"
            >
              {mockTeachers.map(t => (
                <MenuItem key={t} value={t}>{t}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Substitute Teacher</InputLabel>
            <Select
              value={substituteTeacher}
              onChange={e => setSubstituteTeacher(e.target.value)}
              label="Substitute Teacher"
            >
              {mockTeachers.map(t => (
                <MenuItem key={t} value={t}>{t}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Course</InputLabel>
            <Select
              value={courseId}
              onChange={e => setCourseId(e.target.value)}
              label="Course"
            >
              {mockCourses.map(c => (
                <MenuItem key={c} value={c}>{c}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Timeslot</InputLabel>
            <Select
              value={timeslot}
              onChange={e => setTimeslot(e.target.value)}
              label="Timeslot"
            >
              {mockTimeslots.map(ts => (
                <MenuItem key={ts} value={ts}>{ts}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeForm}>Cancel</Button>
          <Button onClick={handleSave} disabled={loading}>{loading ? 'Saving...' : 'Save'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}