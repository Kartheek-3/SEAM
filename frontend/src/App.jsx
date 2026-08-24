import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { IDEProvider } from './context/IDEContext';
import IDELayout from './layouts/IDELayout';
import Workspace from './pages/Workspace';
import Projects from './pages/Projects';
import Experiments from './pages/Experiments';
import ExperimentDetail from './pages/ExperimentDetail';
import Tasks from './pages/Tasks';
import QA from './pages/QA';
import Delivery from './pages/Delivery';

function App() {
  return (
    <IDEProvider>
      <Router>
        <Routes>
          <Route path="/" element={<IDELayout />}>
            <Route index element={<Navigate to="/workspace" replace />} />
            
            {/* Main IDE Workspace */}
            <Route path="workspace" element={<Workspace />} />
            
            {/* Observability & Management */}
            <Route path="projects" element={<Projects />} />
            
            <Route path="experiments" element={<Experiments />} />
            <Route path="experiments/:id" element={<ExperimentDetail />} />
            
            <Route path="tasks" element={<Tasks />} />
            <Route path="qa" element={<QA />} />
            <Route path="delivery" element={<Delivery />} />
            
            {/* Placeholder for Dashboard redirect to workspace */}
            <Route path="dashboard" element={<Navigate to="/workspace" replace />} />
          </Route>
        </Routes>
      </Router>
    </IDEProvider>
  );
}

export default App;
