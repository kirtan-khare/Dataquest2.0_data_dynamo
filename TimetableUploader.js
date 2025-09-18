import React, { useState, useContext } from 'react';
import { Box, Button, CircularProgress, Typography, Paper } from '@mui/material';
import { AuthContext } from '../contexts/AuthContext';

export default function TimetableUploader({ setDeptSchedules }) {
  const { token } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a ZIP file to upload');
      return;
    }
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`, // Added authentication token
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || `Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setDeptSchedules(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ maxWidth: 600, margin: 'auto', padding: 3 }}>
      <Paper elevation={3} sx={{ padding: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom color="primary" align="center">
          Upload Dataset ZIP
        </Typography>

        <input
          type="file"
          accept=".zip"
          onChange={handleFileChange}
          style={{ marginBottom: 16, cursor: 'pointer' }}
        />

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={loading || !file}
          fullWidth
          sx={{ mb: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Upload & Generate Timetable'}
        </Button>

        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
            {error}
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
