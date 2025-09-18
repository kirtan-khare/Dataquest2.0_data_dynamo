import React, { useContext } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from 'react-router-dom';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import Login from './components/Login';
import Register from './components/Register';
import Profile from './components/Profile';
import Layout from './components/Layout';
import TimetableUploader from './components/TimetableUploader';
import DepartmentTimetableViewer from './components/DepartmentTimetableViewer';
import SubstituteTeacherManagement from './components/SubstituteTeacherManagement';
import { Typography } from '@mui/material';

function useRouteTabs() {
  const navigate = useNavigate();
  const location = useLocation();

  const pathToTab = {
    '/upload': 'upload',
    '/timetables': 'timetables',
    '/substitutes': 'substitutes',
    '/profile': 'profile',
  };

  const tabToPath = Object.fromEntries(
    Object.entries(pathToTab).map(([path, tab]) => [tab, path])
  );

  const currentTab = pathToTab[location.pathname] || 'upload';

  const onTabChange = (event, newTab) => {
    navigate(tabToPath[newTab]);
  };

  return [currentTab, onTabChange];
}

function AppPages() {
  const [currentTab, onTabChange] = useRouteTabs();
  const [deptSchedules, setDeptSchedules] = React.useState(null);

  const handleSetDeptSchedules = (data) => setDeptSchedules(data);

  const renderContent = () => {
    switch (currentTab) {
      case 'upload':
        return <TimetableUploader setDeptSchedules={handleSetDeptSchedules} />;
      case 'timetables':
        if (!deptSchedules) {
          return (
            <Typography variant="body1" sx={{ mt: 3 }}>
              Please upload a dataset first.
            </Typography>
          );
        }
        return <DepartmentTimetableViewer deptSchedules={deptSchedules} />;
      case 'substitutes':
        return <SubstituteTeacherManagement />;
      case 'profile':
        return <Profile />;
      default:
        return null;
    }
  };

  return (
    <Layout currentTab={currentTab} onTabChange={onTabChange}>
      {renderContent()}
    </Layout>
  );
}

function AppRoutes() {
  const { token } = useContext(AuthContext);
  return (
    <Routes>
      <Route
        path="/login"
        element={!token ? <Login /> : <Navigate to="/upload" replace />}
      />
      <Route
        path="/register"
        element={!token ? <Register /> : <Navigate to="/upload" replace />}
      />
      <Route
        path="/upload"
        element={token ? <AppPages /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/timetables"
        element={token ? <AppPages /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/substitutes"
        element={token ? <AppPages /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/profile"
        element={token ? <AppPages /> : <Navigate to="/login" replace />}
      />
      <Route
        path="*"
        element={<Navigate to={token ? "/upload" : "/login"} replace />}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}
