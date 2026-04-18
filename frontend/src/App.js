import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Patients from "@/pages/Patients";
import PatientDetail from "@/pages/PatientDetail";
import PatientOnboarding from "@/pages/PatientOnboarding";
import Opportunities from "@/pages/Opportunities";
import LabTests from "@/pages/LabTests";
import SyncDashboard from "@/pages/SyncDashboard";

function App() {
  return (
    <div className="App min-h-screen bg-slate-50">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="patients" element={<Patients />} />
            <Route path="patients/:id" element={<PatientDetail />} />
            <Route path="patients/:id/onboarding" element={<PatientOnboarding />} />
            <Route path="opportunities" element={<Opportunities />} />
            <Route path="lab-tests" element={<LabTests />} />
            <Route path="sync" element={<SyncDashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
