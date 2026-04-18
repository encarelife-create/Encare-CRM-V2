import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats');
export const getPatientsToCall = () => api.get('/dashboard/patients-to-call');

// Patients
export const getPatients = (params) => api.get('/patients', { params });
export const getPatient = (id) => api.get(`/patients/${id}`);
export const createPatient = (data) => api.post('/patients', data);
export const updatePatient = (id, data) => api.put(`/patients/${id}`, data);
export const deletePatient = (id) => api.delete(`/patients/${id}`);

// Vitals (unified endpoint)
export const addVital = (patientId, data) => api.post(`/patients/${patientId}/vitals`, data);
export const getVitals = (patientId, days = 30) => api.get(`/patients/${patientId}/vitals`, { params: { days } });

// Interactions
export const addInteraction = (patientId, data) => api.post(`/patients/${patientId}/interactions`, data);
export const getInteractions = (patientId) => api.get(`/patients/${patientId}/interactions`);

// Lab Tests
export const bookLabTest = (patientId, data) => api.post(`/patients/${patientId}/lab-tests/book`, data);
export const getLabTests = (patientId) => api.get(`/patients/${patientId}/lab-tests`);
export const updateLabTest = (patientId, testId, data) => api.put(`/patients/${patientId}/lab-tests/${testId}`, data);

// Medicines
export const addMedicine = (patientId, data) => api.post(`/patients/${patientId}/medicines`, data);
export const updateMedicine = (patientId, medicineId, data) => api.put(`/patients/${patientId}/medicines/${medicineId}`, data);
export const deleteMedicine = (patientId, medicineId) => api.delete(`/patients/${patientId}/medicines/${medicineId}`);
export const refillMedicine = (patientId, medicineIndex, quantity) =>
  api.put(`/patients/${patientId}/medicines/${medicineIndex}/refill?quantity=${quantity}`);

// Suggestions
export const getProductSuggestions = (patientId) => api.get(`/patients/${patientId}/suggestions/products`);
export const getLabTestSuggestions = (patientId) => api.get(`/patients/${patientId}/suggestions/lab-tests`);

// Opportunities
export const getOpportunities = (params) => api.get('/opportunities', { params });
export const generateOpportunities = () => api.post('/opportunities/generate');
export const updateOpportunity = (id, data) => api.put(`/opportunities/${id}`, data);

// Catalogs
export const getProductCatalog = () => api.get('/catalog/products');
export const getLabTestCatalog = () => api.get('/catalog/lab-tests');
export const addCustomLabTest = (data) => api.post('/catalog/lab-tests', data);
export const updateLabTestPrice = (testName, price) => api.put(`/catalog/lab-tests/${encodeURIComponent(testName)}/price`, { price });
export const updateCustomLabTest = (testId, data) => api.put(`/catalog/lab-tests/${testId}`, data);
export const deleteCustomLabTest = (testId) => api.delete(`/catalog/lab-tests/${testId}`);

// Laboratories
export const getLaboratories = () => api.get('/laboratories');
export const addLaboratory = (data) => api.post('/laboratories', data);
export const updateLaboratory = (labId, data) => api.put(`/laboratories/${labId}`, data);
export const deleteLaboratory = (labId) => api.delete(`/laboratories/${labId}`);

// Medicine Analysis
export const analyzeMedicine = (medicineName) => api.post(`/medicine/analyze?medicine_name=${encodeURIComponent(medicineName)}`);

// Doctor Appointments
export const createDoctorAppointment = (patientId, data) => api.post(`/patients/${patientId}/appointments`, data);
export const getDoctorAppointments = (patientId) => api.get(`/patients/${patientId}/appointments`);
export const updateAppointmentStatus = (patientId, appointmentId, status) =>
  api.put(`/patients/${patientId}/appointments/${appointmentId}/status`, { status });
export const deleteDoctorAppointment = (patientId, appointmentId) =>
  api.delete(`/patients/${patientId}/appointments/${appointmentId}`);

// Seed
export const seedDatabase = () => api.post('/seed');

// Sync (enCARE mock)
export const listEncarePatientsForSync = () => api.get('/sync/encare-patients');
export const syncPatient = (encareUserId) => api.post(`/sync/patient/${encareUserId}`);
export const syncMedications = (encareUserId) => api.post(`/sync/medications/${encareUserId}`);
export const syncVitals = (encareUserId) => api.post(`/sync/vitals/${encareUserId}`);
export const getSyncStatus = () => api.get('/sync/status');
export const getPatientSyncStatus = (patientId) => api.get(`/sync/status/${patientId}`);

// Onboarding Profile
export const getOnboardingProfile = (patientId) => api.get(`/patients/${patientId}/onboarding`);
export const updateOnboardingProfile = (patientId, data) => api.put(`/patients/${patientId}/onboarding`, data);

export default api;
