from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="enCARE Healthcare CRM - Allied Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================== MODELS (Aligned with enCARE) ========================

class Caregiver(BaseModel):
    """Emergency contact / Caregiver - aligned with enCARE's relative fields"""
    name: str
    phone: str
    email: Optional[str] = None
    relationship: str = "Family"

class DosageTiming(BaseModel):
    """Individual dosage timing - matches enCARE's DosageTiming"""
    time: str  # e.g., "08:00"
    amount: str  # e.g., "10" (tablets) or "15" (IU for injection)

class MedicationSchedule(BaseModel):
    """Medicine schedule - aligned with enCARE's MedicationSchedule"""
    frequency: str = "daily"  # daily, weekly, as-needed
    times: List[str] = []  # Legacy: ['09:00', '21:00']
    dosage_timings: List[DosageTiming] = []  # New: [{time, amount}]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    weekly_days: List[str] = []  # ['monday', 'wednesday'] for weekly

class RefillReminder(BaseModel):
    """Refill settings - aligned with enCARE"""
    enabled: bool = True
    pills_remaining: int = 0
    threshold: int = 7

class Medicine(BaseModel):
    """Medicine model - fully aligned with enCARE's Medication model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    dosage: str = ""  # Legacy field
    form: str = "Tablet"  # Tablet, Capsule, Injection, Syrup, etc.
    color: str = "#FF6B6B"
    instructions: Optional[str] = None
    schedule: MedicationSchedule = MedicationSchedule()
    refill_reminder: RefillReminder = RefillReminder()
    
    # Tablet/Capsule stock tracking
    tablet_stock_count: Optional[int] = None
    tablets_per_strip: Optional[int] = None
    
    # Injection stock tracking (IU-based)
    injection_iu_remaining: Optional[float] = None
    injection_iu_per_ml: Optional[float] = None
    injection_iu_per_package: Optional[float] = None
    injection_ml_volume: Optional[float] = None
    injection_stock_count: Optional[int] = None
    
    # Pricing for invoice calculation
    cost_per_unit: Optional[float] = None
    include_in_invoice: bool = True
    
    # Order/Invoice links
    medicine_order_link: Optional[str] = None
    medicine_invoice_link: Optional[str] = None
    medicine_invoice_amount: Optional[float] = None
    injection_order_link: Optional[str] = None
    injection_invoice_link: Optional[str] = None
    injection_invoice_amount: Optional[float] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Patient(BaseModel):
    """Patient model - aligned with enCARE's User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic profile (enCARE alignment)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    picture: Optional[str] = None
    
    # Demographics
    age: Optional[int] = None
    sex: Optional[str] = None  # enCARE uses 'sex', not 'gender'
    
    # Address fields (enCARE alignment)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    
    # Medical info
    diabetes_type: Optional[str] = "Type 2"
    diseases: List[str] = []
    
    # Emergency contact (enCARE alignment)
    relative_name: Optional[str] = None
    relative_email: Optional[str] = None
    relative_whatsapp: Optional[str] = None
    caregivers: List[Caregiver] = []
    
    # Medications (populated from enCARE)
    medicines: List[Medicine] = []
    
    # Invoice links (user-level from enCARE)
    medicine_order_link: Optional[str] = None
    medicine_invoice_link: Optional[str] = None
    medicine_invoice_amount: Optional[float] = None
    injection_order_link: Optional[str] = None
    injection_invoice_link: Optional[str] = None
    injection_invoice_amount: Optional[float] = None
    
    # CRM-specific fields
    adherence_rate: float = 85.0
    priority: str = "normal"  # high, normal, low
    last_contact: Optional[str] = None
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PatientCreate(BaseModel):
    """Create patient - aligned with enCARE User fields"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    diabetes_type: Optional[str] = "Type 2"
    relative_name: Optional[str] = None
    relative_email: Optional[str] = None
    relative_whatsapp: Optional[str] = None

class BloodGlucose(BaseModel):
    """Blood glucose reading - aligned with enCARE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    value: int
    unit: str = "mg/dL"
    time: str
    meal_context: str  # Fasting, Before Breakfast, After Lunch, etc.
    date: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BloodPressure(BaseModel):
    """Blood pressure reading - aligned with enCARE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    time: str
    date: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BodyMetrics(BaseModel):
    """Body metrics - aligned with enCARE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    weight: float
    height: float  # in cm
    bmi: float
    date: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Appointment(BaseModel):
    """Appointment model - aligned with enCARE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # doctor, lab
    title: str
    doctor: Optional[str] = None
    hospital: Optional[str] = None
    date: str
    time: str
    location: Optional[str] = None
    notes: Optional[str] = None
    status: str = "upcoming"  # upcoming, done, postponed, abandoned
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AppointmentCreate(BaseModel):
    type: str = "doctor"
    title: str = "Doctor Consultation"
    doctor: Optional[str] = None
    hospital: Optional[str] = None
    date: str
    time: str
    location: Optional[str] = None
    notes: Optional[str] = None

class AdherenceLog(BaseModel):
    """Adherence log - aligned with enCARE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    medication_id: str
    scheduled_time: str
    taken_time: Optional[str] = None
    status: str  # pending, taken, skipped
    date: str
    dosage_amount: Optional[str] = None  # Amount taken at this time
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Interaction(BaseModel):
    """CRM interaction log"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # call, message, visit
    purpose: str = ""  # reason for interaction (comma-separated if multiple)
    notes: str
    outcome: str  # positive, neutral, negative, no_answer
    follow_up_date: str
    follow_up_time: str = "09:00"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "Healthcare Assistant"


class Opportunity(BaseModel):
    """CRM opportunity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    type: str  # refill, lab_test, product, vitals_alert, adherence, invoice
    description: str
    priority: str  # high, medium, low
    expected_revenue: float = 0.0
    status: str = "pending"  # pending, contacted, converted, dismissed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ======================== PRODUCT CATALOG ========================

PRODUCT_CATALOG = {
    "Diabetes": [
        {"name": "Glucometer", "category": "equipment", "purpose": "Monitor blood sugar levels at home", "price": 1200},
        {"name": "Blood Glucose Test Strips (50)", "category": "equipment", "purpose": "For glucometer testing", "price": 650},
        {"name": "Lancets Pack (100)", "category": "equipment", "purpose": "For blood sampling", "price": 250},
        {"name": "Diabetic Foot Cream", "category": "personal_care", "purpose": "Prevent foot complications", "price": 350},
        {"name": "Sugar-Free Supplements", "category": "personal_care", "purpose": "Nutritional support", "price": 480},
    ],
    "Hypertension": [
        {"name": "Digital BP Monitor", "category": "equipment", "purpose": "Track blood pressure daily", "price": 1800},
        {"name": "Automatic Wrist BP Monitor", "category": "equipment", "purpose": "Portable BP monitoring", "price": 1500},
        {"name": "Salt Substitute", "category": "personal_care", "purpose": "Low sodium alternative", "price": 180},
    ],
    "Heart Disease": [
        {"name": "Pulse Oximeter", "category": "equipment", "purpose": "Monitor oxygen levels", "price": 800},
        {"name": "ECG Monitor (Portable)", "category": "equipment", "purpose": "Heart rhythm monitoring", "price": 3500},
        {"name": "Omega-3 Supplements", "category": "personal_care", "purpose": "Heart health support", "price": 650},
    ],
    "Thyroid": [
        {"name": "Thyroid Function Test Kit", "category": "equipment", "purpose": "Home monitoring", "price": 1200},
        {"name": "Weight Scale (Digital)", "category": "equipment", "purpose": "Track weight changes", "price": 1200},
    ],
    "Arthritis": [
        {"name": "Heating Pad", "category": "equipment", "purpose": "Pain relief for joints", "price": 900},
        {"name": "Knee Brace", "category": "equipment", "purpose": "Joint support", "price": 650},
        {"name": "Pain Relief Gel", "category": "personal_care", "purpose": "Topical pain relief", "price": 280},
    ],
    "Elderly Care": [
        {"name": "Walking Stick (Adjustable)", "category": "equipment", "purpose": "Mobility support", "price": 450},
        {"name": "Adult Diapers (Pack of 10)", "category": "personal_care", "purpose": "Incontinence care", "price": 350},
        {"name": "Pill Organizer (Weekly)", "category": "equipment", "purpose": "Medicine management", "price": 180},
    ],
    "Respiratory": [
        {"name": "Nebulizer Machine", "category": "equipment", "purpose": "Medication delivery", "price": 2500},
        {"name": "Peak Flow Meter", "category": "equipment", "purpose": "Monitor lung function", "price": 650},
    ],
}

LAB_TEST_CATALOG = [
    {"name": "HbA1c", "diseases": ["Diabetes"], "frequency_months": 3, "price": 450},
    {"name": "Fasting Blood Sugar", "diseases": ["Diabetes"], "frequency_months": 1, "price": 150},
    {"name": "Lipid Profile", "diseases": ["Diabetes", "Hypertension", "Heart Disease"], "frequency_months": 6, "price": 600},
    {"name": "Kidney Function Test", "diseases": ["Diabetes", "Hypertension"], "frequency_months": 6, "price": 800},
    {"name": "Liver Function Test", "diseases": ["Diabetes", "Heart Disease"], "frequency_months": 6, "price": 700},
    {"name": "Thyroid Profile (T3, T4, TSH)", "diseases": ["Thyroid"], "frequency_months": 3, "price": 550},
    {"name": "Complete Blood Count", "diseases": ["Elderly Care", "Arthritis"], "frequency_months": 6, "price": 350},
    {"name": "ECG", "diseases": ["Heart Disease", "Hypertension"], "frequency_months": 6, "price": 400},
    {"name": "Uric Acid", "diseases": ["Arthritis"], "frequency_months": 3, "price": 200},
    {"name": "Vitamin D", "diseases": ["Elderly Care", "Arthritis"], "frequency_months": 6, "price": 750},
    {"name": "Chest X-Ray", "diseases": ["Respiratory"], "frequency_months": 12, "price": 500},
]

# Medicine-Disease mapping for auto-detection
MEDICINE_DISEASE_MAP = {
    # Diabetes medicines
    "metformin": ["Diabetes"], "glimepiride": ["Diabetes"], "gliclazide": ["Diabetes"],
    "sitagliptin": ["Diabetes"], "empagliflozin": ["Diabetes"], "insulin": ["Diabetes"],
    "pioglitazone": ["Diabetes"], "vildagliptin": ["Diabetes"], "dapagliflozin": ["Diabetes"],
    "januvia": ["Diabetes"], "jardiance": ["Diabetes"], "glucophage": ["Diabetes"],
    # BP medicines
    "amlodipine": ["Hypertension"], "telmisartan": ["Hypertension"], "losartan": ["Hypertension"],
    "atenolol": ["Hypertension"], "metoprolol": ["Hypertension", "Heart Disease"],
    "ramipril": ["Hypertension", "Heart Disease"], "lisinopril": ["Hypertension", "Heart Disease"],
    "chlorthalidone": ["Hypertension"], "hydrochlorothiazide": ["Hypertension"],
    # Heart medicines
    "aspirin": ["Heart Disease"], "clopidogrel": ["Heart Disease"], "atorvastatin": ["Heart Disease"],
    "rosuvastatin": ["Heart Disease"], "ecosprin": ["Heart Disease"],
    # Thyroid medicines
    "thyroxine": ["Thyroid"], "levothyroxine": ["Thyroid"], "eltroxin": ["Thyroid"],
    # Arthritis medicines
    "diclofenac": ["Arthritis"], "ibuprofen": ["Arthritis"], "naproxen": ["Arthritis"],
    "celecoxib": ["Arthritis"], "etoricoxib": ["Arthritis"], "methotrexate": ["Arthritis"],
    # Respiratory medicines
    "salbutamol": ["Respiratory"], "budesonide": ["Respiratory"], "montelukast": ["Respiratory"],
}

# ======================== HELPER FUNCTIONS ========================

def detect_diseases_from_medicines(medicines: List[Dict]) -> List[str]:
    """Detect diseases based on medicines - works with enCARE medicine format."""
    diseases = set()
    for med in medicines:
        med_name = med.get("name", "").lower()
        for key, disease_list in MEDICINE_DISEASE_MAP.items():
            if key in med_name:
                diseases.update(disease_list)
    return list(diseases)

def calculate_stock_status(medicine: Dict) -> Dict:
    """Calculate stock status based on medicine form - aligned with enCARE."""
    form = medicine.get("form", "").lower()
    
    if form in ["tablet", "capsule"]:
        stock = medicine.get("tablet_stock_count", 0) or 0
        # Calculate days based on dosage_timings
        schedule = medicine.get("schedule", {})
        dosage_timings = schedule.get("dosage_timings", [])
        daily_consumption = len(dosage_timings) if dosage_timings else 1
        
        # Sum up actual amounts if available
        if dosage_timings:
            try:
                daily_consumption = sum(int(dt.get("amount", 1)) for dt in dosage_timings)
            except:
                daily_consumption = len(dosage_timings)
        
        days_left = int(stock / daily_consumption) if daily_consumption > 0 else 999
        return {
            "stock": stock,
            "unit": "tablets" if form == "tablet" else "capsules",
            "days_left": days_left,
            "is_low": days_left <= 10
        }
    
    elif form == "injection":
        iu_remaining = medicine.get("injection_iu_remaining", 0) or 0
        stock_count = medicine.get("injection_stock_count", 0) or 0
        
        # Calculate days based on daily IU consumption
        schedule = medicine.get("schedule", {})
        dosage_timings = schedule.get("dosage_timings", [])
        daily_iu = 0
        if dosage_timings:
            try:
                daily_iu = sum(float(dt.get("amount", 0)) for dt in dosage_timings)
            except:
                daily_iu = 0
        
        days_left = int(iu_remaining / daily_iu) if daily_iu > 0 else 999
        return {
            "stock": stock_count,
            "iu_remaining": iu_remaining,
            "unit": "vials/pens",
            "days_left": days_left,
            "is_low": days_left <= 7 or stock_count <= 1
        }
    
    return {"stock": 0, "unit": "units", "days_left": 999, "is_low": False}

def get_product_suggestions(diseases: List[str]) -> List[Dict]:
    """Get product suggestions based on diseases."""
    suggestions = []
    for disease in diseases:
        if disease in PRODUCT_CATALOG:
            for product in PRODUCT_CATALOG[disease]:
                suggestions.append({**product, "disease": disease})
    return suggestions

def get_lab_test_suggestions(diseases: List[str]) -> List[Dict]:
    """Get lab test suggestions based on diseases (built-in catalog only, sync)."""
    suggestions = []
    for test in LAB_TEST_CATALOG:
        if any(d in test["diseases"] for d in diseases):
            suggestions.append(test)
    return suggestions

async def get_lab_test_suggestions_with_custom(diseases: List[str]) -> List[Dict]:
    """Get lab test suggestions including custom tests from DB."""
    if not diseases:
        return []

    # Built-in catalog with price overrides
    overrides = await db.lab_test_overrides.find({}, {"_id": 0}).to_list(500)
    override_map = {o["test_name"]: o for o in overrides}

    suggestions = []
    seen_names = set()
    for test in LAB_TEST_CATALOG:
        if any(d in test["diseases"] for d in diseases):
            t = {**test, "source": "auto"}
            if test["name"] in override_map:
                t["price"] = override_map[test["name"]]["price"]
            suggestions.append(t)
            seen_names.add(test["name"])

    # Custom tests from MongoDB
    custom_tests = await db.custom_lab_tests.find({}, {"_id": 0}).to_list(500)
    for ct in custom_tests:
        if ct["name"] not in seen_names and any(d in ct.get("diseases", []) for d in diseases):
            ct["source"] = "custom"
            suggestions.append(ct)

    return suggestions

# ======================== API ROUTES ========================

@api_router.get("/")
async def root():
    return {"message": "enCARE Healthcare CRM - Allied Platform API", "version": "2.0.0"}

# ======================== PATIENT ROUTES ========================

async def compute_priority_reason(patient: Dict) -> str:
    """Compute a human-readable reason for the patient's current priority."""
    reasons = []
    priority = patient.get("priority", "normal")
    pid = patient.get("id")

    # Check medicine stock
    for med in patient.get("medicines", []):
        stock = calculate_stock_status(med)
        if stock.get("is_low") and stock.get("days_left", 999) <= 3:
            reasons.append(f"{med.get('name', 'Medicine')} critically low ({stock['days_left']} days left)")
        elif stock.get("is_low"):
            reasons.append(f"{med.get('name', 'Medicine')} running low ({stock['days_left']} days left)")

    # Check adherence
    adherence = patient.get("adherence_rate", 100)
    if adherence < 70:
        reasons.append(f"Low adherence ({adherence}%)")

    # Check doctor visit overdue (3+ months)
    if pid:
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        last_done = await db.appointments.find_one(
            {"user_id": pid, "status": "done"}, {"_id": 0, "date": 1}, sort=[("date", -1)]
        )
        if last_done and last_done["date"] < three_months_ago:
            reasons.append(f"Doctor visit overdue (last: {last_done['date']})")
        elif not last_done:
            any_appt = await db.appointments.find_one({"user_id": pid}, {"_id": 0})
            if any_appt:
                reasons.append("Doctor visit overdue (no completed visits)")

    # Check number of diseases
    diseases = patient.get("diseases", [])
    if len(diseases) >= 3:
        reasons.append(f"Multiple conditions ({', '.join(diseases[:3])})")

    if not reasons:
        if priority == "high":
            reasons.append("Marked as high priority")
        elif priority == "normal":
            reasons.append("Standard care plan")
        else:
            reasons.append("Stable condition")

    return "; ".join(reasons)


@api_router.get("/patients", response_model=List[Dict])
async def get_patients(
    search: Optional[str] = None,
    disease: Optional[str] = None,
    priority: Optional[str] = None
):
    """Get all patients with optional filters."""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if disease:
        query["diseases"] = disease
    if priority:
        query["priority"] = priority
    
    patients = await db.patients.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with stock status and priority reason
    for patient in patients:
        for med in patient.get("medicines", []):
            med["stock_status"] = calculate_stock_status(med)
        patient["priority_reason"] = await compute_priority_reason(patient)
    
    return patients

@api_router.get("/patients/{patient_id}", response_model=Dict)
async def get_patient(patient_id: str):
    """Get a single patient by ID with vitals and lab tests."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Enrich with stock status
    for med in patient.get("medicines", []):
        med["stock_status"] = calculate_stock_status(med)
    
    # Enrich with priority reason
    patient["priority_reason"] = await compute_priority_reason(patient)
    
    # Include latest vitals
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    patient["blood_glucose"] = await db.blood_glucose.find(
        {"user_id": patient_id, "date": {"$gte": cutoff}}, {"_id": 0}
    ).sort("date", -1).to_list(50)
    patient["blood_pressure"] = await db.blood_pressure.find(
        {"user_id": patient_id, "date": {"$gte": cutoff}}, {"_id": 0}
    ).sort("date", -1).to_list(50)
    patient["body_metrics"] = await db.body_metrics.find(
        {"user_id": patient_id, "date": {"$gte": cutoff}}, {"_id": 0}
    ).sort("date", -1).to_list(50)
    
    # Include lab test bookings
    patient["lab_tests"] = await db.lab_bookings.find(
        {"patient_id": patient_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    # Calculate next due dates from onboarding visit dates (3-month interval)
    if patient.get("last_doctor_visit_date"):
        try:
            last_doc = datetime.strptime(patient["last_doctor_visit_date"], "%Y-%m-%d")
            patient["next_doctor_visit_due"] = (last_doc + timedelta(days=90)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            patient["next_doctor_visit_due"] = None
    else:
        patient["next_doctor_visit_due"] = None

    if patient.get("last_lab_visit_date"):
        try:
            last_lab = datetime.strptime(patient["last_lab_visit_date"], "%Y-%m-%d")
            patient["next_lab_visit_due"] = (last_lab + timedelta(days=90)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            patient["next_lab_visit_due"] = None
    else:
        patient["next_lab_visit_due"] = None

    return patient

@api_router.post("/patients", response_model=Dict)
async def create_patient(patient_data: PatientCreate):
    """Create a new patient."""
    patient_dict = patient_data.model_dump()
    
    # Detect diseases from medicines (if any)
    diseases = []
    if patient_dict.get("age", 0) and patient_dict["age"] >= 65:
        diseases.append("Elderly Care")
    
    # Build caregiver from relative fields
    caregivers = []
    if patient_dict.get("relative_name"):
        caregivers.append({
            "name": patient_dict["relative_name"],
            "phone": patient_dict.get("relative_whatsapp", ""),
            "email": patient_dict.get("relative_email", ""),
            "relationship": "Family"
        })
    
    new_patient = Patient(
        **patient_dict,
        diseases=diseases,
        caregivers=caregivers,
        medicines=[],
        priority="normal"
    )
    
    doc = new_patient.model_dump()
    await db.patients.insert_one(doc)
    
    return await db.patients.find_one({"id": new_patient.id}, {"_id": 0})

@api_router.put("/patients/{patient_id}", response_model=Dict)
async def update_patient(patient_id: str, updates: Dict):
    """Update patient details."""
    # Re-detect diseases if medicines updated
    if "medicines" in updates:
        diseases = detect_diseases_from_medicines(updates["medicines"])
        existing = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if existing and existing.get("age", 0) >= 65:
            diseases.append("Elderly Care")
        updates["diseases"] = list(set(diseases))
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.patients.update_one(
        {"id": patient_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return await db.patients.find_one({"id": patient_id}, {"_id": 0})

@api_router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient and all related data."""
    result = await db.patients.delete_one({"id": patient_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    await db.blood_glucose.delete_many({"user_id": patient_id})
    await db.blood_pressure.delete_many({"user_id": patient_id})
    await db.body_metrics.delete_many({"user_id": patient_id})
    await db.appointments.delete_many({"user_id": patient_id})
    await db.lab_bookings.delete_many({"patient_id": patient_id})
    await db.opportunities.delete_many({"patient_id": patient_id})
    return {"message": "Patient deleted"}

@api_router.put("/patients/{patient_id}/medicines/{medicine_index}/refill")
async def refill_medicine(patient_id: str, medicine_index: int, quantity: int = Query(30)):
    """Refill a medicine by index - handles tablets and injections."""
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    medicines = patient.get("medicines", [])
    if medicine_index < 0 or medicine_index >= len(medicines):
        raise HTTPException(status_code=400, detail="Invalid medicine index")
    med = medicines[medicine_index]
    form = (med.get("form") or "Tablet").lower()
    if form in ["tablet", "capsule"]:
        med["tablet_stock_count"] = (med.get("tablet_stock_count") or 0) + quantity
        if med.get("refill_reminder"):
            med["refill_reminder"]["pills_remaining"] = med["tablet_stock_count"]
    elif form == "injection":
        iu_per_pkg = med.get("injection_iu_per_package") or 300
        med["injection_stock_count"] = (med.get("injection_stock_count") or 0) + 1
        med["injection_iu_remaining"] = (med.get("injection_iu_remaining") or 0) + iu_per_pkg
    else:
        med["tablet_stock_count"] = (med.get("tablet_stock_count") or 0) + quantity
    medicines[medicine_index] = med
    await db.patients.update_one(
        {"id": patient_id},
        {"$set": {"medicines": medicines, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Medicine refilled", "medicine": {k: v for k, v in med.items() if k != "_id"}}

@api_router.post("/patients/{patient_id}/medicines", response_model=Dict)
async def add_medicine(patient_id: str, data: Dict):
    """Add a medicine to a patient."""
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    new_med = {
        "id": str(uuid.uuid4()),
        "user_id": patient_id,
        "name": data["name"],
        "dosage": data.get("dosage", ""),
        "form": data.get("form", "Tablet"),
        "color": data.get("color", "#FF6B6B"),
        "instructions": data.get("instructions"),
        "schedule": data.get("schedule", {"frequency": "daily", "times": [], "dosage_timings": [], "start_date": None, "end_date": None, "weekly_days": []}),
        "refill_reminder": data.get("refill_reminder", {"enabled": True, "pills_remaining": 0, "threshold": 7}),
        "tablet_stock_count": data.get("tablet_stock_count"),
        "tablets_per_strip": data.get("tablets_per_strip"),
        "injection_iu_remaining": data.get("injection_iu_remaining"),
        "injection_iu_per_ml": data.get("injection_iu_per_ml"),
        "injection_iu_per_package": data.get("injection_iu_per_package"),
        "injection_ml_volume": data.get("injection_ml_volume"),
        "injection_stock_count": data.get("injection_stock_count"),
        "cost_per_unit": data.get("cost_per_unit"),
        "include_in_invoice": data.get("include_in_invoice", True),
        "medicine_order_link": data.get("medicine_order_link"),
        "medicine_invoice_link": data.get("medicine_invoice_link"),
        "medicine_invoice_amount": data.get("medicine_invoice_amount"),
        "injection_order_link": data.get("injection_order_link"),
        "injection_invoice_link": data.get("injection_invoice_link"),
        "injection_invoice_amount": data.get("injection_invoice_amount"),
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    
    # Re-detect diseases
    medicines = patient.get("medicines", []) + [new_med]
    diseases = detect_diseases_from_medicines(medicines)
    if patient.get("age", 0) >= 65:
        diseases.append("Elderly Care")
    diseases = list(set(diseases + patient.get("diseases", [])))
    
    await db.patients.update_one(
        {"id": patient_id},
        {"$push": {"medicines": new_med}, "$set": {"diseases": diseases, "updated_at": now_iso}}
    )
    return {k: v for k, v in new_med.items() if k != "_id"}

@api_router.put("/patients/{patient_id}/medicines/{medicine_id}", response_model=Dict)
async def update_medicine(patient_id: str, medicine_id: str, data: Dict):
    """Update a specific medicine by its ID."""
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    medicines = patient.get("medicines", [])
    found_idx = None
    for idx, med in enumerate(medicines):
        if med.get("id") == medicine_id:
            found_idx = idx
            break
    if found_idx is None:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Update fields
    existing = medicines[found_idx]
    for key in ["name", "dosage", "form", "color", "instructions", "schedule",
                "refill_reminder", "tablet_stock_count", "tablets_per_strip",
                "injection_iu_remaining", "injection_iu_per_ml", "injection_iu_per_package",
                "injection_ml_volume", "injection_stock_count", "cost_per_unit",
                "include_in_invoice", "medicine_order_link", "medicine_invoice_link",
                "medicine_invoice_amount", "injection_order_link", "injection_invoice_link",
                "injection_invoice_amount"]:
        if key in data:
            existing[key] = data[key]
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    medicines[found_idx] = existing
    
    # Re-detect diseases
    diseases = detect_diseases_from_medicines(medicines)
    if patient.get("age", 0) >= 65:
        diseases.append("Elderly Care")
    diseases = list(set(diseases))
    
    await db.patients.update_one(
        {"id": patient_id},
        {"$set": {"medicines": medicines, "diseases": diseases, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {k: v for k, v in existing.items() if k != "_id"}

@api_router.delete("/patients/{patient_id}/medicines/{medicine_id}")
async def delete_medicine(patient_id: str, medicine_id: str):
    """Delete a medicine from a patient."""
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    medicines = [m for m in patient.get("medicines", []) if m.get("id") != medicine_id]
    if len(medicines) == len(patient.get("medicines", [])):
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    diseases = detect_diseases_from_medicines(medicines)
    if patient.get("age", 0) >= 65:
        diseases.append("Elderly Care")
    diseases = list(set(diseases))
    
    await db.patients.update_one(
        {"id": patient_id},
        {"$set": {"medicines": medicines, "diseases": diseases, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Medicine deleted"}

# ======================== VITALS ROUTES (Aligned with enCARE) ========================

@api_router.post("/patients/{patient_id}/vitals", response_model=Dict)
async def add_vital_unified(patient_id: str, data: Dict):
    """Unified vital recording endpoint - dispatches based on type."""
    vital_type = data.get("type", "bp")
    now = datetime.now(timezone.utc)
    date_str = data.get("date", now.strftime("%Y-%m-%d"))
    time_str = data.get("time", now.strftime("%H:%M"))
    
    if vital_type == "bp":
        bp = BloodPressure(
            user_id=patient_id,
            systolic=int(data.get("systolic", 120)),
            diastolic=int(data.get("diastolic", 80)),
            pulse=data.get("pulse"),
            time=time_str,
            date=date_str,
            notes=data.get("notes")
        )
        await db.blood_pressure.insert_one(bp.model_dump())
        return bp.model_dump()
    elif vital_type in ("sugar", "glucose"):
        glucose = BloodGlucose(
            user_id=patient_id,
            value=int(data.get("value", 100)),
            time=time_str,
            meal_context=data.get("meal_context", "Random"),
            date=date_str,
            notes=data.get("notes")
        )
        await db.blood_glucose.insert_one(glucose.model_dump())
        return glucose.model_dump()
    elif vital_type in ("weight", "metrics"):
        height = float(data.get("height", 170))
        weight = float(data.get("value", data.get("weight", 70)))
        bmi = round(weight / ((height / 100) ** 2), 1)
        metrics = BodyMetrics(
            user_id=patient_id,
            weight=weight,
            height=height,
            bmi=bmi,
            date=date_str,
            notes=data.get("notes")
        )
        await db.body_metrics.insert_one(metrics.model_dump())
        return metrics.model_dump()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown vital type: {vital_type}")

@api_router.post("/patients/{patient_id}/vitals/glucose", response_model=Dict)
async def add_glucose_reading(patient_id: str, reading: Dict):
    """Add blood glucose reading - aligned with enCARE."""
    glucose = BloodGlucose(
        user_id=patient_id,
        value=reading["value"],
        time=reading.get("time", datetime.now(timezone.utc).strftime("%H:%M")),
        meal_context=reading.get("meal_context", "Random"),
        date=reading.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        notes=reading.get("notes")
    )
    
    await db.blood_glucose.insert_one(glucose.model_dump())
    return glucose.model_dump()

@api_router.post("/patients/{patient_id}/vitals/bp", response_model=Dict)
async def add_bp_reading(patient_id: str, reading: Dict):
    """Add blood pressure reading - aligned with enCARE."""
    bp = BloodPressure(
        user_id=patient_id,
        systolic=reading["systolic"],
        diastolic=reading["diastolic"],
        pulse=reading.get("pulse"),
        time=reading.get("time", datetime.now(timezone.utc).strftime("%H:%M")),
        date=reading.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        notes=reading.get("notes")
    )
    
    await db.blood_pressure.insert_one(bp.model_dump())
    return bp.model_dump()

@api_router.post("/patients/{patient_id}/vitals/metrics", response_model=Dict)
async def add_body_metrics(patient_id: str, reading: Dict):
    """Add body metrics - aligned with enCARE."""
    height = reading.get("height", 170)
    weight = reading["weight"]
    bmi = round(weight / ((height / 100) ** 2), 1)
    
    metrics = BodyMetrics(
        user_id=patient_id,
        weight=weight,
        height=height,
        bmi=bmi,
        date=reading.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        notes=reading.get("notes")
    )
    
    await db.body_metrics.insert_one(metrics.model_dump())
    return metrics.model_dump()

@api_router.get("/patients/{patient_id}/vitals", response_model=Dict)
async def get_patient_vitals(patient_id: str, days: int = 30):
    """Get all vitals for a patient."""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    glucose = await db.blood_glucose.find(
        {"user_id": patient_id, "date": {"$gte": cutoff_date}},
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    bp = await db.blood_pressure.find(
        {"user_id": patient_id, "date": {"$gte": cutoff_date}},
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    metrics = await db.body_metrics.find(
        {"user_id": patient_id, "date": {"$gte": cutoff_date}},
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    return {
        "blood_glucose": glucose,
        "blood_pressure": bp,
        "body_metrics": metrics
    }

# ======================== APPOINTMENT ROUTES (Aligned with enCARE) ========================

@api_router.get("/patients/{patient_id}/appointments", response_model=List[Dict])
async def get_patient_appointments(patient_id: str):
    """Get appointments for a patient, sorted by date desc."""
    appointments = await db.appointments.find(
        {"user_id": patient_id},
        {"_id": 0}
    ).sort([("date", -1), ("time", -1)]).to_list(200)
    return appointments

@api_router.post("/patients/{patient_id}/appointments", response_model=Dict)
async def create_appointment(patient_id: str, appointment: AppointmentCreate):
    """Create appointment - aligned with enCARE."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0, "name": 1})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_apt = Appointment(
        user_id=patient_id,
        **appointment.model_dump()
    )
    
    await db.appointments.insert_one(new_apt.model_dump())
    return {k: v for k, v in new_apt.model_dump().items() if k != "_id"}

@api_router.put("/patients/{patient_id}/appointments/{apt_id}/status")
async def update_apt_status(patient_id: str, apt_id: str, data: dict):
    """Update appointment status - aligned with enCARE statuses."""
    new_status = data.get("status")
    valid_statuses = ["upcoming", "done", "postponed", "abandoned"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db.appointments.update_one(
        {"id": apt_id, "user_id": patient_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Auto-flag patient as high priority if last done visit was 3+ months ago
    if new_status == "done":
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        last_done = await db.appointments.find_one(
            {"user_id": patient_id, "status": "done"},
            {"_id": 0, "date": 1}, sort=[("date", -1)]
        )
        if not last_done or last_done["date"] < three_months_ago:
            await db.patients.update_one({"id": patient_id}, {"$set": {"priority": "high"}})

    updated = await db.appointments.find_one({"id": apt_id}, {"_id": 0})
    return updated

# ======================== INTERACTION ROUTES ========================

@api_router.post("/patients/{patient_id}/interactions", response_model=Dict)
async def add_interaction(patient_id: str, interaction: Dict):
    """Log an interaction with a patient."""
    follow_up_date = interaction.get("follow_up_date", "")
    follow_up_time = interaction.get("follow_up_time", "09:00")
    if not follow_up_date:
        raise HTTPException(status_code=400, detail="Follow-up date is required")

    # Validate follow-up is in the future
    try:
        follow_up_dt = datetime.fromisoformat(f"{follow_up_date}T{follow_up_time}")
        if follow_up_dt <= datetime.now():
            raise HTTPException(status_code=400, detail="Follow-up date and time must be in the future")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid follow-up date or time format")

    interaction_obj = Interaction(
        type=interaction["type"],
        purpose=interaction.get("purpose", ""),
        notes=interaction["notes"],
        outcome=interaction["outcome"],
        follow_up_date=follow_up_date,
        follow_up_time=follow_up_time
    )
    
    # Add to patient's interactions array
    result = await db.patients.update_one(
        {"id": patient_id},
        {
            "$push": {"interactions": interaction_obj.model_dump()},
            "$set": {"last_contact": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return interaction_obj.model_dump()

@api_router.get("/patients/{patient_id}/interactions", response_model=List[Dict])
async def get_interactions(patient_id: str):
    """Get interactions for a patient."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0, "interactions": 1})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.get("interactions", [])



# ======================== LAB TEST BOOKING ROUTES ========================

@api_router.post("/patients/{patient_id}/lab-tests/book", response_model=Dict)
async def book_lab_test(patient_id: str, data: Dict):
    """Book a lab test for a patient."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    booking = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "test_name": data["test_name"],
        "booked_date": data.get("booked_date"),
        "status": "booked",
        "price": data.get("price", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.lab_bookings.insert_one(booking)
    return {k: v for k, v in booking.items() if k != "_id"}

@api_router.get("/patients/{patient_id}/lab-tests", response_model=List[Dict])
async def get_lab_tests(patient_id: str):
    """Get lab test bookings for a patient."""
    bookings = await db.lab_bookings.find(
        {"patient_id": patient_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return bookings

@api_router.put("/patients/{patient_id}/lab-tests/{test_id}", response_model=Dict)
async def update_lab_test(patient_id: str, test_id: str, data: Dict):
    """Update a lab test booking status."""
    result = await db.lab_bookings.update_one(
        {"id": test_id, "patient_id": patient_id},
        {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lab test booking not found")
    return {"message": "Lab test updated"}

# ======================== SUGGESTIONS ROUTES ========================

@api_router.get("/patients/{patient_id}/suggestions/products", response_model=List[Dict])
async def get_product_suggestions_for_patient(patient_id: str):
    """Get product suggestions based on patient's diseases."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    diseases = patient.get("diseases", [])
    return get_product_suggestions(diseases)

@api_router.get("/patients/{patient_id}/suggestions/lab-tests", response_model=List[Dict])
async def get_lab_test_suggestions_for_patient(patient_id: str):
    """Get lab test suggestions based on patient's diseases."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    diseases = patient.get("diseases", [])
    return await get_lab_test_suggestions_with_custom(diseases)

# ======================== OPPORTUNITIES ROUTES ========================

@api_router.get("/opportunities", response_model=List[Dict])
async def get_opportunities(
    opportunity_type: Optional[str] = None,
    status: Optional[str] = "pending"
):
    """Get all opportunities."""
    query = {}
    if opportunity_type:
        query["type"] = opportunity_type
    if status:
        query["status"] = status
    
    opportunities = await db.opportunities.find(query, {"_id": 0}).to_list(500)
    return opportunities

@api_router.post("/opportunities/generate")
async def generate_opportunities():
    """Generate opportunities from all patients."""
    patients = await db.patients.find({}, {"_id": 0}).to_list(1000)
    opportunities = []
    
    for patient in patients:
        patient_id = patient["id"]
        patient_name = patient["name"]
        
        # Check refill opportunities from medicines
        for med in patient.get("medicines", []):
            stock_status = calculate_stock_status(med)
            if stock_status["is_low"]:
                opp = Opportunity(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    type="refill",
                    description=f"{med['name']} running low ({stock_status['days_left']} days left)",
                    priority="high" if stock_status["days_left"] <= 3 else "medium",
                    expected_revenue=med.get("medicine_invoice_amount", 500.0) or 500.0
                )
                opportunities.append(opp.model_dump())
        
        # Check invoice opportunities
        total_invoice = 0
        if patient.get("medicine_invoice_amount"):
            total_invoice += patient["medicine_invoice_amount"]
        if patient.get("injection_invoice_amount"):
            total_invoice += patient["injection_invoice_amount"]
        
        if total_invoice > 0:
            opp = Opportunity(
                patient_id=patient_id,
                patient_name=patient_name,
                type="invoice",
                description=f"Monthly invoice: ₹{total_invoice:,.0f}",
                priority="medium",
                expected_revenue=total_invoice
            )
            opportunities.append(opp.model_dump())
        
        # Check lab test opportunities
        diseases = patient.get("diseases", [])
        for test in LAB_TEST_CATALOG:
            if any(d in test["diseases"] for d in diseases):
                # Check if test is due (simplified - just suggest if disease matches)
                opp = Opportunity(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    type="lab_test",
                    description=f"{test['name']} recommended",
                    priority="medium",
                    expected_revenue=float(test["price"])
                )
                opportunities.append(opp.model_dump())
                break  # One lab test opp per patient
        
        # Check product opportunities
        product_suggestions = get_product_suggestions(diseases)
        if product_suggestions[:1]:  # Top 1 product
            prod = product_suggestions[0]
            opp = Opportunity(
                patient_id=patient_id,
                patient_name=patient_name,
                type="product",
                description=f"Suggest {prod['name']} for {prod['disease']}",
                priority="low",
                expected_revenue=float(prod["price"])
            )
            opportunities.append(opp.model_dump())
        
        # Check adherence
        if patient.get("adherence_rate", 100) < 70:
            opp = Opportunity(
                patient_id=patient_id,
                patient_name=patient_name,
                type="adherence",
                description=f"Low adherence ({patient['adherence_rate']}%) - needs follow-up",
                priority="high",
                expected_revenue=0.0
            )
            opportunities.append(opp.model_dump())
    
    # Clear old pending opportunities and insert new ones
    await db.opportunities.delete_many({"status": "pending"})
    if opportunities:
        await db.opportunities.insert_many(opportunities)
    
    return {"generated": len(opportunities)}

@api_router.put("/opportunities/{opportunity_id}", response_model=Dict)
async def update_opportunity(opportunity_id: str, updates: Dict):
    """Update opportunity status."""
    result = await db.opportunities.update_one(
        {"id": opportunity_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"message": "Opportunity updated"}

# ======================== DASHBOARD ROUTES ========================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    total_patients = await db.patients.count_documents({})
    high_priority = await db.patients.count_documents({"priority": "high"})
    
    # Get opportunities stats
    refill_opps = await db.opportunities.count_documents({"type": "refill", "status": "pending"})
    lab_opps = await db.opportunities.count_documents({"type": "lab_test", "status": "pending"})
    product_opps = await db.opportunities.count_documents({"type": "product", "status": "pending"})
    invoice_opps = await db.opportunities.count_documents({"type": "invoice", "status": "pending"})
    adherence_opps = await db.opportunities.count_documents({"type": "adherence", "status": "pending"})
    
    # Calculate expected revenue
    pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$expected_revenue"}}}
    ]
    revenue_result = await db.opportunities.aggregate(pipeline).to_list(1)
    expected_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Calculate total invoice amounts from patients
    patients = await db.patients.find({}, {"_id": 0, "medicine_invoice_amount": 1, "injection_invoice_amount": 1}).to_list(1000)
    total_monthly_invoice = sum(
        (p.get("medicine_invoice_amount", 0) or 0) + (p.get("injection_invoice_amount", 0) or 0)
        for p in patients
    )
    
    # Get today's tasks
    today_tasks = await db.opportunities.find(
        {"status": "pending", "priority": {"$in": ["high", "medium"]}},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    # Disease distribution
    disease_pipeline = [
        {"$unwind": "$diseases"},
        {"$group": {"_id": "$diseases", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    disease_dist = await db.patients.aggregate(disease_pipeline).to_list(10)
    
    return {
        "total_patients": total_patients,
        "high_priority_patients": high_priority,
        "opportunities": {
            "refills": refill_opps,
            "lab_tests": lab_opps,
            "products": product_opps,
            "invoices": invoice_opps,
            "adherence": adherence_opps
        },
        "expected_revenue": expected_revenue,
        "total_monthly_invoice": total_monthly_invoice,
        "today_tasks": today_tasks,
        "disease_distribution": [{"disease": d["_id"], "count": d["count"]} for d in disease_dist]
    }

@api_router.get("/dashboard/patients-to-call")
async def get_patients_to_call():
    """Daily task list for callers — individual entries with statuses.
    Sources: 1) Follow-ups scheduled today, 2) Pending opportunities, 3) No contact 30+ days.
    Statuses: pending, completed, upcoming, overdue.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_time_str = now.strftime("%H:%M")
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    entries = []

    all_patients = await db.patients.find(
        {}, {"_id": 0, "id": 1, "name": 1, "interactions": 1, "priority": 1}
    ).to_list(500)

    patient_map = {p["id"]: p for p in all_patients}

    # Helper: check if patient has any interaction logged today AFTER a given timestamp
    def has_later_interaction_today(interactions, after_created_at):
        for inter in interactions:
            created = inter.get("created_at", "")
            if created > after_created_at and created[:10] == today_str[:10]:
                return True
        return False

    def has_any_interaction_today(interactions):
        for inter in interactions:
            created = inter.get("created_at", "")
            if created[:10] == today_str[:10]:
                return True
        return False

    # --- Source 1: Follow-up entries (each follow-up = separate entry) ---
    for p in all_patients:
        interactions = p.get("interactions", [])
        for inter in interactions:
            if inter.get("follow_up_date") == today_str:
                fu_time = inter.get("follow_up_time", "09:00")
                created_at = inter.get("created_at", "")

                if has_later_interaction_today(interactions, created_at):
                    status = "completed"
                elif fu_time > now_time_str:
                    status = "upcoming"
                else:
                    status = "overdue"

                entries.append({
                    "id": inter.get("id", created_at),
                    "patient_id": p["id"],
                    "patient_name": p["name"],
                    "status": status,
                    "task_type": "follow_up",
                    "description": f"Scheduled follow-up at {fu_time}",
                    "follow_up_time": fu_time,
                    "revenue": 0,
                    "priority": p.get("priority", "medium"),
                })

    # --- Source 2: Opportunity entries ---
    opportunities = await db.opportunities.find(
        {"status": "pending"}, {"_id": 0}
    ).to_list(200)

    for opp in opportunities:
        pid = opp["patient_id"]
        p = patient_map.get(pid)
        interactions = p.get("interactions", []) if p else []
        contacted_today = has_any_interaction_today(interactions)

        entries.append({
            "id": opp.get("id", ""),
            "patient_id": pid,
            "patient_name": opp["patient_name"],
            "status": "completed" if contacted_today else "pending",
            "task_type": "opportunity",
            "description": opp["description"],
            "follow_up_time": None,
            "revenue": opp.get("expected_revenue", 0),
            "priority": opp.get("priority", "medium"),
        })

    # --- Source 3: No contact in 30+ days ---
    patients_with_entries = set(e["patient_id"] for e in entries)
    for p in all_patients:
        pid = p["id"]
        if pid in patients_with_entries:
            continue
        interactions = p.get("interactions", [])
        if not interactions:
            entries.append({
                "id": f"nc-{pid}",
                "patient_id": pid,
                "patient_name": p["name"],
                "status": "pending",
                "task_type": "no_contact",
                "description": "No interactions recorded",
                "follow_up_time": None,
                "revenue": 0,
                "priority": p.get("priority", "low"),
            })
        else:
            last_date = max(i.get("created_at", "") for i in interactions)
            if last_date and last_date < thirty_days_ago:
                contacted_today = has_any_interaction_today(interactions)
                entries.append({
                    "id": f"nc-{pid}",
                    "patient_id": pid,
                    "patient_name": p["name"],
                    "status": "completed" if contacted_today else "pending",
                    "task_type": "no_contact",
                    "description": f"Last contacted {last_date[:10]}",
                    "follow_up_time": None,
                    "revenue": 0,
                    "priority": p.get("priority", "low"),
                })

    # --- Source 4: Doctor appointments today + 3-month overdue ---
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    today_appointments = await db.appointments.find(
        {"date": today_str, "status": "upcoming"}, {"_id": 0}
    ).to_list(100)

    for apt in today_appointments:
        pid = apt.get("user_id") or apt.get("patient_id")
        p = patient_map.get(pid)
        pname = p["name"] if p else apt.get("patient_name", "Unknown")
        entries.append({
            "id": apt["id"],
            "patient_id": pid,
            "patient_name": pname,
            "status": "upcoming",
            "task_type": "doctor_appointment",
            "description": f"Dr. {apt.get('doctor', 'N/A')} at {apt.get('hospital', apt.get('location', 'N/A'))} — {apt.get('time', '')}",
            "follow_up_time": apt.get("time"),
            "revenue": 0,
            "priority": p.get("priority", "medium") if p else "medium",
        })

    # 3-month overdue doctor visits — flag as high priority + add to list
    for p in all_patients:
        pid = p["id"]
        last_done = await db.appointments.find_one(
            {"user_id": pid, "status": "done"}, {"_id": 0, "date": 1},
            sort=[("date", -1)]
        )
        is_overdue = False
        if last_done and last_done["date"] < three_months_ago:
            is_overdue = True
        elif not last_done:
            # Check if patient has ANY appointments at all
            any_appt = await db.appointments.find_one({"user_id": pid}, {"_id": 0, "id": 1})
            if any_appt:
                is_overdue = True

        if is_overdue:
            # Auto-flag as high priority
            await db.patients.update_one({"id": pid}, {"$set": {"priority": "high"}})
            # Add entry if not already in list from other sources
            already_has_appt_entry = any(e["patient_id"] == pid and e["task_type"] == "doctor_appointment" for e in entries)
            if not already_has_appt_entry:
                entries.append({
                    "id": f"doc-overdue-{pid}",
                    "patient_id": pid,
                    "patient_name": p["name"],
                    "status": "overdue",
                    "task_type": "doctor_visit_overdue",
                    "description": f"Last doctor visit: {last_done['date'] if last_done else 'Never'} (3+ months ago)",
                    "follow_up_time": None,
                    "revenue": 0,
                    "priority": "high",
                })

    # --- Source 5: Post-visit feedback calls ---
    # All past appointments (any status) and lab bookings where date < today.
    # Persist until HA logs an interaction AFTER the appointment date.
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Build interaction lookup: for each patient, list of interaction dates
    patient_interaction_dates = {}
    for p in all_patients:
        pid = p["id"]
        interactions = p.get("interactions", [])
        dates = [i.get("created_at", "")[:10] for i in interactions if i.get("created_at")]
        patient_interaction_dates[pid] = dates

    # Doctor appointments where date has passed (date < today)
    past_appts = await db.appointments.find(
        {"date": {"$lt": today_str}}, {"_id": 0}
    ).to_list(500)

    feedback_patient_ids = set()
    for apt in past_appts:
        pid = apt.get("user_id")
        p = patient_map.get(pid)
        if not p:
            continue
        appt_date = apt["date"]
        # Day after appointment is when feedback is expected
        feedback_due_date = (datetime.strptime(appt_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        # Check if HA logged an interaction on or after the feedback due date
        interaction_dates = patient_interaction_dates.get(pid, [])
        has_followup = any(d >= feedback_due_date for d in interaction_dates)

        days_since = (datetime.now() - datetime.strptime(appt_date, "%Y-%m-%d")).days
        day_label = "yesterday" if days_since == 1 else f"{days_since} days ago"

        entries.append({
            "id": f"feedback-appt-{apt['id']}",
            "patient_id": pid,
            "patient_name": p["name"],
            "status": "completed" if has_followup else "pending",
            "task_type": "feedback_call",
            "description": f"Feedback: {apt.get('title','Doctor visit')} with {apt.get('doctor','Dr.')} ({day_label})",
            "follow_up_time": None,
            "revenue": 0,
            "priority": p.get("priority", "medium"),
        })
        feedback_patient_ids.add(pid)

    # Lab test bookings where date has passed (booked_date < today)
    past_lab_tests = await db.lab_bookings.find(
        {"booked_date": {"$lt": today_str}}, {"_id": 0}
    ).to_list(500)

    for lt in past_lab_tests:
        pid = lt.get("patient_id")
        p = patient_map.get(pid)
        if not p:
            continue
        booked_date = lt.get("booked_date", "")
        if not booked_date:
            continue
        feedback_due_date = (datetime.strptime(booked_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        interaction_dates = patient_interaction_dates.get(pid, [])
        has_followup = any(d >= feedback_due_date for d in interaction_dates)

        days_since = (datetime.now() - datetime.strptime(booked_date, "%Y-%m-%d")).days
        day_label = "yesterday" if days_since == 1 else f"{days_since} days ago"

        entries.append({
            "id": f"feedback-lab-{lt.get('id', pid)}",
            "patient_id": pid,
            "patient_name": p["name"],
            "status": "completed" if has_followup else "pending",
            "task_type": "feedback_call",
            "description": f"Feedback: {lt.get('test_name','Lab test')} ({day_label})",
            "follow_up_time": None,
            "revenue": 0,
            "priority": p.get("priority", "medium"),
        })

    # Sort: overdue first, then upcoming, pending, completed last
    status_order = {"overdue": 0, "upcoming": 1, "pending": 2, "completed": 3}
    priority_order = {"high": 0, "medium": 1, "low": 2}
    entries.sort(key=lambda x: (
        status_order.get(x["status"], 4),
        priority_order.get(x["priority"], 3),
        x.get("follow_up_time") or "99:99",
        -x["revenue"]
    ))

    return entries

# ======================== CATALOG ROUTES ========================

@api_router.get("/catalog/products")
async def get_product_catalog():
    """Get the full product catalog."""
    return PRODUCT_CATALOG

@api_router.get("/catalog/lab-tests")
async def get_lab_test_catalog():
    """Get the full lab test catalog — merges built-in + custom tests from DB."""
    custom_tests = await db.custom_lab_tests.find({}, {"_id": 0}).to_list(500)
    
    # Start with built-in catalog, apply any price overrides from DB
    overrides = await db.lab_test_overrides.find({}, {"_id": 0}).to_list(500)
    override_map = {o["test_name"]: o for o in overrides}
    
    merged = []
    for test in LAB_TEST_CATALOG:
        t = {**test, "source": "auto"}
        if test["name"] in override_map:
            t["price"] = override_map[test["name"]]["price"]
        merged.append(t)
    
    for ct in custom_tests:
        ct["source"] = "custom"
        merged.append(ct)
    
    return merged

@api_router.post("/catalog/lab-tests")
async def add_custom_lab_test(data: Dict):
    """Add a custom lab test to the catalog."""
    test = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "diseases": data.get("diseases", []),
        "frequency_months": data.get("frequency_months", 6),
        "price": data.get("price", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.custom_lab_tests.insert_one(test)
    return {k: v for k, v in test.items() if k != "_id"}

@api_router.put("/catalog/lab-tests/{test_name}/price")
async def update_lab_test_price(test_name: str, data: Dict):
    """Update the price of any lab test (built-in or custom)."""
    new_price = data.get("price")
    if new_price is None:
        raise HTTPException(status_code=400, detail="price is required")
    
    # Check if it's a custom test
    result = await db.custom_lab_tests.update_one(
        {"name": test_name},
        {"$set": {"price": new_price}}
    )
    if result.matched_count > 0:
        return {"message": "Custom test price updated"}
    
    # Check if it's a built-in test — store override
    if any(t["name"] == test_name for t in LAB_TEST_CATALOG):
        await db.lab_test_overrides.update_one(
            {"test_name": test_name},
            {"$set": {"test_name": test_name, "price": new_price}},
            upsert=True
        )
        return {"message": "Test price updated"}
    
    raise HTTPException(status_code=404, detail="Lab test not found")

@api_router.put("/catalog/lab-tests/{test_id}")
async def update_custom_lab_test(test_id: str, data: Dict):
    """Update a custom lab test."""
    updates = {}
    for key in ["name", "diseases", "frequency_months", "price"]:
        if key in data:
            updates[key] = data[key]
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.custom_lab_tests.update_one({"id": test_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Custom lab test not found")
    return {"message": "Lab test updated"}

@api_router.delete("/catalog/lab-tests/{test_id}")
async def delete_custom_lab_test(test_id: str):
    """Delete a custom lab test."""
    result = await db.custom_lab_tests.delete_one({"id": test_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom lab test not found")
    return {"message": "Lab test deleted"}

# ======================== LABORATORIES ========================

@api_router.get("/laboratories")
async def get_laboratories():
    """Get all laboratories."""
    labs = await db.laboratories.find({}, {"_id": 0}).to_list(500)
    return labs

@api_router.post("/laboratories")
async def add_laboratory(data: Dict):
    """Add a new laboratory."""
    lab = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "address": data.get("address", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
        "pincode": data.get("pincode", ""),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "tests_available": data.get("tests_available", []),
        "notes": data.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.laboratories.insert_one(lab)
    return {k: v for k, v in lab.items() if k != "_id"}

@api_router.put("/laboratories/{lab_id}")
async def update_laboratory(lab_id: str, data: Dict):
    """Update a laboratory."""
    updates = {}
    for key in ["name", "address", "city", "state", "pincode", "phone", "email", "tests_available", "notes"]:
        if key in data:
            updates[key] = data[key]
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.laboratories.update_one({"id": lab_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return {"message": "Laboratory updated"}

@api_router.delete("/laboratories/{lab_id}")
async def delete_laboratory(lab_id: str):
    """Delete a laboratory."""
    result = await db.laboratories.delete_one({"id": lab_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return {"message": "Laboratory deleted"}

# ======================== MEDICINE ANALYSIS ========================

@api_router.post("/medicine/analyze")
async def analyze_medicine(medicine_name: str = Query(...)):
    """Analyze a medicine name and detect associated diseases."""
    detected = []
    name_lower = medicine_name.lower()
    for key, diseases in MEDICINE_DISEASE_MAP.items():
        if key in name_lower:
            detected.extend(diseases)
    detected = list(set(detected))
    
    products = get_product_suggestions(detected) if detected else []
    lab_tests = await get_lab_test_suggestions_with_custom(detected) if detected else []
    
    return {
        "medicine": medicine_name,
        "detected_diseases": detected,
        "suggested_products": products[:5],
        "suggested_lab_tests": lab_tests[:10]
    }

# ======================== SYNC ENDPOINTS (Mock enCARE Data Pull) ========================

# Simulated enCARE data - represents what would come from the main enCARE app
MOCK_ENCARE_PATIENTS = {
    "ENC001": {
        "name": "Arjun Mehta",
        "email": "arjun.mehta@email.com",
        "phone": "+91 98765 11111",
        "picture": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150",
        "age": 52,
        "sex": "Male",
        "address": "22, MG Road",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "pincode": "411001",
        "diabetes_type": "Type 2",
        "relative_name": "Sonia Mehta",
        "relative_whatsapp": "+91 98765 11112",
        "relative_email": "sonia.mehta@email.com",
        "medicines": [
            {
                "name": "Metformin 1000mg",
                "dosage": "1000mg",
                "form": "Tablet",
                "color": "#4ECDC4",
                "schedule": {"frequency": "daily", "dosage_timings": [{"time": "08:00", "amount": "1"}, {"time": "20:00", "amount": "1"}]},
                "refill_reminder": {"enabled": True, "pills_remaining": 20, "threshold": 10},
                "tablet_stock_count": 20,
                "cost_per_unit": 5.5,
                "include_in_invoice": True
            },
            {
                "name": "Amlodipine 5mg",
                "dosage": "5mg",
                "form": "Tablet",
                "color": "#3498DB",
                "schedule": {"frequency": "daily", "dosage_timings": [{"time": "09:00", "amount": "1"}]},
                "refill_reminder": {"enabled": True, "pills_remaining": 15, "threshold": 10},
                "tablet_stock_count": 15,
                "cost_per_unit": 3.0,
                "include_in_invoice": True
            }
        ],
        "medicine_invoice_amount": 1200,
        "adherence_rate": 82,
    },
    "ENC002": {
        "name": "Lakshmi Iyer",
        "email": "lakshmi.iyer@email.com",
        "phone": "+91 98765 22222",
        "picture": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150",
        "age": 67,
        "sex": "Female",
        "address": "45, Anna Nagar",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "pincode": "600040",
        "diabetes_type": None,
        "relative_name": "Venkat Iyer",
        "relative_whatsapp": "+91 98765 22223",
        "medicines": [
            {
                "name": "Levothyroxine 100mcg",
                "dosage": "100mcg",
                "form": "Tablet",
                "color": "#9B59B6",
                "schedule": {"frequency": "daily", "dosage_timings": [{"time": "06:00", "amount": "1"}]},
                "refill_reminder": {"enabled": True, "pills_remaining": 30, "threshold": 10},
                "tablet_stock_count": 30,
                "cost_per_unit": 6.0,
                "include_in_invoice": True
            },
            {
                "name": "Atorvastatin 20mg",
                "dosage": "20mg",
                "form": "Tablet",
                "color": "#E74C3C",
                "schedule": {"frequency": "daily", "dosage_timings": [{"time": "21:00", "amount": "1"}]},
                "refill_reminder": {"enabled": True, "pills_remaining": 25, "threshold": 10},
                "tablet_stock_count": 25,
                "cost_per_unit": 8.0,
                "include_in_invoice": True
            }
        ],
        "medicine_invoice_amount": 780,
        "adherence_rate": 91,
    },
    "ENC003": {
        "name": "Mohammed Faiz",
        "email": "mohammed.faiz@email.com",
        "phone": "+91 98765 33333",
        "picture": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
        "age": 44,
        "sex": "Male",
        "address": "78, Jubilee Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "pincode": "500033",
        "diabetes_type": "Type 1",
        "relative_name": "Fatima Faiz",
        "relative_whatsapp": "+91 98765 33334",
        "medicines": [
            {
                "name": "Insulin Glargine",
                "dosage": "20 IU",
                "form": "Injection",
                "color": "#1ABC9C",
                "schedule": {"frequency": "daily", "dosage_timings": [{"time": "22:00", "amount": "20"}]},
                "refill_reminder": {"enabled": True, "pills_remaining": 0, "threshold": 1},
                "injection_iu_remaining": 600,
                "injection_iu_per_package": 300,
                "injection_stock_count": 2,
                "cost_per_unit": 450,
                "include_in_invoice": True
            }
        ],
        "medicine_invoice_amount": 2200,
        "adherence_rate": 76,
    }
}

MOCK_ENCARE_VITALS = {
    "ENC001": {
        "blood_glucose": [
            {"value": 145, "time": "08:00", "meal_context": "Fasting", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"value": 180, "time": "14:00", "meal_context": "After Lunch", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"value": 130, "time": "08:00", "meal_context": "Fasting", "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")},
        ],
        "blood_pressure": [
            {"systolic": 138, "diastolic": 88, "pulse": 78, "time": "09:00", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"systolic": 142, "diastolic": 90, "pulse": 80, "time": "09:00", "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")},
        ]
    },
    "ENC002": {
        "blood_pressure": [
            {"systolic": 125, "diastolic": 82, "pulse": 72, "time": "10:00", "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")},
        ]
    },
    "ENC003": {
        "blood_glucose": [
            {"value": 210, "time": "08:00", "meal_context": "Fasting", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"value": 165, "time": "08:00", "meal_context": "Fasting", "date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")},
        ]
    }
}


@api_router.get("/sync/encare-patients")
async def list_encare_patients():
    """List available patients from the simulated enCARE system."""
    result = []
    for encare_id, data in MOCK_ENCARE_PATIENTS.items():
        # Check if already synced
        existing = await db.patients.find_one({"encare_user_id": encare_id}, {"_id": 0, "id": 1, "name": 1})
        result.append({
            "encare_user_id": encare_id,
            "name": data["name"],
            "phone": data["phone"],
            "city": data.get("city"),
            "diseases_hint": [m["name"] for m in data.get("medicines", [])],
            "already_synced": existing is not None,
            "crm_patient_id": existing["id"] if existing else None
        })
    return result


@api_router.post("/sync/patient/{encare_user_id}")
async def sync_patient(encare_user_id: str):
    """Simulate pulling patient data from the enCARE app and creating/updating in CRM."""
    encare_data = MOCK_ENCARE_PATIENTS.get(encare_user_id)
    if not encare_data:
        raise HTTPException(status_code=404, detail=f"enCARE user {encare_user_id} not found")

    # Check if patient already synced
    existing = await db.patients.find_one({"encare_user_id": encare_user_id}, {"_id": 0})

    now_iso = datetime.now(timezone.utc).isoformat()
    patient_id = existing["id"] if existing else str(uuid.uuid4())

    # Build medicines with IDs
    medicines = []
    for med_data in encare_data.get("medicines", []):
        med = {**med_data, "id": str(uuid.uuid4()), "user_id": patient_id, "created_at": now_iso, "updated_at": now_iso}
        medicines.append(med)

    # Detect diseases
    diseases = detect_diseases_from_medicines(medicines)
    age = encare_data.get("age", 0)
    if age and age >= 65:
        diseases.append("Elderly Care")
    diseases = list(set(diseases))

    # Build caregivers
    caregivers = []
    if encare_data.get("relative_name"):
        caregivers.append({
            "name": encare_data["relative_name"],
            "phone": encare_data.get("relative_whatsapp", ""),
            "email": encare_data.get("relative_email", ""),
            "relationship": "Family"
        })

    patient_doc = {
        "id": patient_id,
        "encare_user_id": encare_user_id,
        "name": encare_data["name"],
        "email": encare_data.get("email"),
        "phone": encare_data.get("phone"),
        "picture": encare_data.get("picture"),
        "age": age,
        "sex": encare_data.get("sex"),
        "address": encare_data.get("address"),
        "city": encare_data.get("city"),
        "state": encare_data.get("state"),
        "country": encare_data.get("country"),
        "pincode": encare_data.get("pincode"),
        "diabetes_type": encare_data.get("diabetes_type"),
        "diseases": diseases,
        "relative_name": encare_data.get("relative_name"),
        "relative_email": encare_data.get("relative_email"),
        "relative_whatsapp": encare_data.get("relative_whatsapp"),
        "caregivers": caregivers,
        "medicines": medicines,
        "medicine_invoice_amount": encare_data.get("medicine_invoice_amount"),
        "adherence_rate": encare_data.get("adherence_rate", 85),
        "priority": "normal",
        "interactions": existing.get("interactions", []) if existing else [],
        "last_contact": existing.get("last_contact") if existing else None,
        "created_at": existing.get("created_at", now_iso) if existing else now_iso,
        "updated_at": now_iso,
        "last_synced_at": now_iso,
        "sync_source": "encare",
    }

    if existing:
        await db.patients.replace_one({"id": patient_id}, patient_doc)
        action = "updated"
    else:
        await db.patients.insert_one(patient_doc)
        action = "created"

    # Log sync activity
    sync_log = {
        "id": str(uuid.uuid4()),
        "encare_user_id": encare_user_id,
        "patient_id": patient_id,
        "patient_name": encare_data["name"],
        "action": action,
        "sync_type": "patient",
        "details": f"Synced patient profile with {len(medicines)} medicines, {len(diseases)} diseases detected",
        "synced_at": now_iso,
    }
    await db.sync_logs.insert_one(sync_log)

    return {
        "message": f"Patient {action} from enCARE",
        "patient_id": patient_id,
        "encare_user_id": encare_user_id,
        "action": action,
        "medicines_synced": len(medicines),
        "diseases_detected": diseases,
    }


@api_router.post("/sync/medications/{encare_user_id}")
async def sync_medications(encare_user_id: str):
    """Simulate syncing medication data from enCARE for an already-imported patient."""
    encare_data = MOCK_ENCARE_PATIENTS.get(encare_user_id)
    if not encare_data:
        raise HTTPException(status_code=404, detail=f"enCARE user {encare_user_id} not found")

    patient = await db.patients.find_one({"encare_user_id": encare_user_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not synced yet. Sync patient first.")

    patient_id = patient["id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    medicines = []
    for med_data in encare_data.get("medicines", []):
        med = {**med_data, "id": str(uuid.uuid4()), "user_id": patient_id, "created_at": now_iso, "updated_at": now_iso}
        medicines.append(med)

    diseases = detect_diseases_from_medicines(medicines)
    if patient.get("age", 0) >= 65:
        diseases.append("Elderly Care")
    diseases = list(set(diseases))

    await db.patients.update_one(
        {"id": patient_id},
        {"$set": {
            "medicines": medicines,
            "diseases": diseases,
            "medicine_invoice_amount": encare_data.get("medicine_invoice_amount"),
            "adherence_rate": encare_data.get("adherence_rate", 85),
            "updated_at": now_iso,
            "last_synced_at": now_iso,
        }}
    )

    sync_log = {
        "id": str(uuid.uuid4()),
        "encare_user_id": encare_user_id,
        "patient_id": patient_id,
        "patient_name": encare_data["name"],
        "action": "medications_synced",
        "sync_type": "medications",
        "details": f"Synced {len(medicines)} medications",
        "synced_at": now_iso,
    }
    await db.sync_logs.insert_one(sync_log)

    return {
        "message": "Medications synced from enCARE",
        "patient_id": patient_id,
        "medicines_synced": len(medicines),
        "diseases_detected": diseases,
    }


@api_router.post("/sync/vitals/{encare_user_id}")
async def sync_vitals(encare_user_id: str):
    """Simulate syncing vitals data from enCARE."""
    vitals_data = MOCK_ENCARE_VITALS.get(encare_user_id)
    if not vitals_data:
        raise HTTPException(status_code=404, detail=f"No vitals data for enCARE user {encare_user_id}")

    patient = await db.patients.find_one({"encare_user_id": encare_user_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not synced yet. Sync patient first.")

    patient_id = patient["id"]
    now_iso = datetime.now(timezone.utc).isoformat()
    counts = {"blood_glucose": 0, "blood_pressure": 0, "body_metrics": 0}

    for reading in vitals_data.get("blood_glucose", []):
        glucose = BloodGlucose(user_id=patient_id, **reading)
        await db.blood_glucose.insert_one(glucose.model_dump())
        counts["blood_glucose"] += 1

    for reading in vitals_data.get("blood_pressure", []):
        bp = BloodPressure(user_id=patient_id, **reading)
        await db.blood_pressure.insert_one(bp.model_dump())
        counts["blood_pressure"] += 1

    for reading in vitals_data.get("body_metrics", []):
        height = reading.get("height", 170)
        weight = reading["weight"]
        bmi = round(weight / ((height / 100) ** 2), 1)
        metrics = BodyMetrics(user_id=patient_id, weight=weight, height=height, bmi=bmi, date=reading["date"])
        await db.body_metrics.insert_one(metrics.model_dump())
        counts["body_metrics"] += 1

    sync_log = {
        "id": str(uuid.uuid4()),
        "encare_user_id": encare_user_id,
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "action": "vitals_synced",
        "sync_type": "vitals",
        "details": f"Synced {counts['blood_glucose']} glucose, {counts['blood_pressure']} BP readings",
        "synced_at": now_iso,
    }
    await db.sync_logs.insert_one(sync_log)

    return {
        "message": "Vitals synced from enCARE",
        "patient_id": patient_id,
        "counts": counts,
    }


@api_router.get("/sync/status")
async def get_sync_status():
    """Get sync history/logs."""
    logs = await db.sync_logs.find({}, {"_id": 0}).sort("synced_at", -1).to_list(100)
    return logs


@api_router.get("/sync/status/{patient_id}")
async def get_patient_sync_status(patient_id: str):
    """Get sync status for a specific patient."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0, "encare_user_id": 1, "last_synced_at": 1, "sync_source": 1})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    logs = await db.sync_logs.find({"patient_id": patient_id}, {"_id": 0}).sort("synced_at", -1).to_list(20)

    return {
        "patient_id": patient_id,
        "encare_user_id": patient.get("encare_user_id"),
        "last_synced_at": patient.get("last_synced_at"),
        "sync_source": patient.get("sync_source"),
        "sync_logs": logs,
    }


# ======================== ONBOARDING PROFILE ========================

@api_router.get("/patients/{patient_id}/onboarding")
async def get_onboarding_profile(patient_id: str):
    """Get patient onboarding profile data aligned with enCARE fields."""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Return structured onboarding fields
    return {
        "id": patient["id"],
        "encare_user_id": patient.get("encare_user_id"),
        "last_synced_at": patient.get("last_synced_at"),
        "sync_source": patient.get("sync_source"),
        # Personal info
        "name": patient.get("name", ""),
        "email": patient.get("email", ""),
        "phone": patient.get("phone", ""),
        "picture": patient.get("picture", ""),
        "age": patient.get("age"),
        "sex": patient.get("sex", ""),
        # Address
        "address": patient.get("address", ""),
        "city": patient.get("city", ""),
        "state": patient.get("state", ""),
        "country": patient.get("country", "India"),
        "pincode": patient.get("pincode", ""),
        # Medical
        "diseases": patient.get("diseases", []),
        "adherence_rate": patient.get("adherence_rate", 85),
        "main_disease": patient.get("main_disease", ""),
        "consulting_doctor_name": patient.get("consulting_doctor_name", ""),
        "clinic_hospital_details": patient.get("clinic_hospital_details", ""),
        "last_doctor_visit_date": patient.get("last_doctor_visit_date", ""),
        "regular_lab_details": patient.get("regular_lab_details", ""),
        "last_lab_visit_date": patient.get("last_lab_visit_date", ""),
        "mobility_status": patient.get("mobility_status", ""),
        "other_critical_info": patient.get("other_critical_info", ""),
        "marketing_consent": patient.get("marketing_consent", ""),
        # Caregiver / Emergency
        "relative_name": patient.get("relative_name", ""),
        "relative_email": patient.get("relative_email", ""),
        "relative_whatsapp": patient.get("relative_whatsapp", ""),
        "caregivers": patient.get("caregivers", []),
        # Invoice
        "medicine_order_link": patient.get("medicine_order_link", ""),
        "medicine_invoice_link": patient.get("medicine_invoice_link", ""),
        "medicine_invoice_amount": patient.get("medicine_invoice_amount"),
        "injection_order_link": patient.get("injection_order_link", ""),
        "injection_invoice_link": patient.get("injection_invoice_link", ""),
        "injection_invoice_amount": patient.get("injection_invoice_amount"),
        # Meta
        "priority": patient.get("priority", "normal"),
        "created_at": patient.get("created_at"),
        "updated_at": patient.get("updated_at"),
    }


@api_router.put("/patients/{patient_id}/onboarding")
async def update_onboarding_profile(patient_id: str, data: Dict):
    """Update patient onboarding profile — full profile update mirroring enCARE fields."""
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Allowed onboarding fields (enCARE-aligned)
    allowed_fields = [
        "name", "email", "phone", "picture", "age", "sex",
        "address", "city", "state", "country", "pincode",
        "adherence_rate",
        "main_disease", "consulting_doctor_name", "clinic_hospital_details",
        "last_doctor_visit_date", "regular_lab_details", "last_lab_visit_date",
        "mobility_status", "other_critical_info", "marketing_consent",
        "relative_name", "relative_email", "relative_whatsapp",
        "medicine_order_link", "medicine_invoice_link", "medicine_invoice_amount",
        "injection_order_link", "injection_invoice_link", "injection_invoice_amount",
        "priority"
    ]

    updates = {}
    for field in allowed_fields:
        if field in data:
            updates[field] = data[field]

    # Rebuild caregivers from relative fields
    rel_name = data.get("relative_name", patient.get("relative_name"))
    if rel_name:
        updates["caregivers"] = [{
            "name": rel_name,
            "phone": data.get("relative_whatsapp", patient.get("relative_whatsapp", "")),
            "email": data.get("relative_email", patient.get("relative_email", "")),
            "relationship": "Family"
        }]

    # Auto-update Elderly Care disease if age >= 65
    new_age = data.get("age", patient.get("age", 0))
    current_diseases = patient.get("diseases", [])
    if new_age and new_age >= 65 and "Elderly Care" not in current_diseases:
        current_diseases.append("Elderly Care")
        updates["diseases"] = current_diseases
    elif new_age and new_age < 65 and "Elderly Care" in current_diseases:
        current_diseases.remove("Elderly Care")
        # Re-detect from medicines
        med_diseases = detect_diseases_from_medicines(patient.get("medicines", []))
        updates["diseases"] = list(set(med_diseases + [d for d in current_diseases if d != "Elderly Care"]))

    updates["updated_at"] = now_iso

    await db.patients.update_one({"id": patient_id}, {"$set": updates})

    # Auto-create/update appointment records from onboarding visit dates
    if "last_doctor_visit_date" in data and data["last_doctor_visit_date"]:
        await db.appointments.update_one(
            {"user_id": patient_id, "source": "onboarding", "type": "doctor"},
            {
                "$set": {
                    "user_id": patient_id,
                    "type": "doctor",
                    "title": "Doctor Visit (from onboarding)",
                    "doctor": data.get("consulting_doctor_name", patient.get("consulting_doctor_name", "")),
                    "hospital": data.get("clinic_hospital_details", patient.get("clinic_hospital_details", "")),
                    "date": data["last_doctor_visit_date"],
                    "time": "00:00",
                    "status": "done",
                    "source": "onboarding",
                    "notes": "Auto-recorded from onboarding profile",
                },
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now_iso}
            },
            upsert=True
        )

    if "last_lab_visit_date" in data and data["last_lab_visit_date"]:
        await db.appointments.update_one(
            {"user_id": patient_id, "source": "onboarding", "type": "lab"},
            {
                "$set": {
                    "user_id": patient_id,
                    "type": "lab",
                    "title": "Lab Visit (from onboarding)",
                    "doctor": "",
                    "hospital": data.get("regular_lab_details", patient.get("regular_lab_details", "")),
                    "date": data["last_lab_visit_date"],
                    "time": "00:00",
                    "status": "done",
                    "source": "onboarding",
                    "notes": "Auto-recorded from onboarding profile",
                },
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now_iso}
            },
            upsert=True
        )

    return await db.patients.find_one({"id": patient_id}, {"_id": 0})


# ======================== SEED DATA ========================

@api_router.post("/seed")
async def seed_database():
    """Seed the database with sample data aligned with enCARE structure."""
    await db.patients.delete_many({})
    await db.opportunities.delete_many({})
    await db.blood_glucose.delete_many({})
    await db.blood_pressure.delete_many({})
    await db.body_metrics.delete_many({})
    await db.appointments.delete_many({})
    await db.lab_bookings.delete_many({})
    await db.custom_lab_tests.delete_many({})
    await db.lab_test_overrides.delete_many({})
    await db.laboratories.delete_many({})
    await db.doctor_appointments.delete_many({})
    await db.sync_logs.delete_many({})
    # Note: appointments collection is already cleared above
    
    sample_patients = [
        {
            "name": "Rajesh Kumar",
            "email": "rajesh.kumar@email.com",
            "phone": "+91 98765 43210",
            "picture": "https://images.unsplash.com/photo-1597045226382-dee4ba273d3a?w=150",
            "age": 58,
            "sex": "Male",
            "address": "42, MG Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "India",
            "pincode": "560001",
            "diabetes_type": "Type 2",
            "relative_name": "Priya Kumar",
            "relative_whatsapp": "+91 98765 43211",
            "relative_email": "priya.kumar@email.com",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Metformin 500mg",
                    "dosage": "500mg",
                    "form": "Tablet",
                    "color": "#FF6B6B",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [
                            {"time": "08:00", "amount": "1"},
                            {"time": "20:00", "amount": "1"}
                        ],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 8, "threshold": 10},
                    "tablet_stock_count": 8,
                    "tablets_per_strip": 10,
                    "cost_per_unit": 2.5,
                    "include_in_invoice": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Amlodipine 5mg",
                    "dosage": "5mg",
                    "form": "Tablet",
                    "color": "#4ECDC4",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "08:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 25, "threshold": 10},
                    "tablet_stock_count": 25,
                    "cost_per_unit": 3.0,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 1500,
            "adherence_rate": 82,
            "priority": "high"
        },
        {
            "name": "Anita Sharma",
            "email": "anita.sharma@email.com",
            "phone": "+91 87654 32109",
            "picture": "https://images.unsplash.com/photo-1547121591-ebfd615332af?w=150",
            "age": 67,
            "sex": "Female",
            "address": "15, Sector 21",
            "city": "Noida",
            "state": "Uttar Pradesh",
            "country": "India",
            "pincode": "201301",
            "diabetes_type": "Type 2",
            "relative_name": "Vikram Sharma",
            "relative_whatsapp": "+91 87654 32110",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Eltroxin 50mcg",
                    "dosage": "50mcg",
                    "form": "Tablet",
                    "color": "#9B59B6",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "06:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 5, "threshold": 10},
                    "tablet_stock_count": 5,
                    "cost_per_unit": 4.0,
                    "include_in_invoice": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Telmisartan 40mg",
                    "dosage": "40mg",
                    "form": "Tablet",
                    "color": "#3498DB",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "08:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 15, "threshold": 10},
                    "tablet_stock_count": 15,
                    "cost_per_unit": 5.5,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 1200,
            "adherence_rate": 65,
            "priority": "high"
        },
        {
            "name": "Prakash Singh",
            "email": "prakash.singh@email.com",
            "phone": "+91 76543 21098",
            "picture": "https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150",
            "age": 70,
            "sex": "Male",
            "address": "67, Civil Lines",
            "city": "Jaipur",
            "state": "Rajasthan",
            "country": "India",
            "pincode": "302006",
            "diabetes_type": "Type 2",
            "relative_name": "Meena Singh",
            "relative_whatsapp": "+91 76543 21099",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Insulin Glargine",
                    "dosage": "20 units",
                    "form": "Injection",
                    "color": "#E74C3C",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "22:00", "amount": "20"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 0, "threshold": 1},
                    "injection_iu_remaining": 180,
                    "injection_iu_per_package": 300,
                    "injection_stock_count": 1,
                    "cost_per_unit": 850,
                    "include_in_invoice": True,
                    "injection_invoice_amount": 2550
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Metformin 1000mg",
                    "dosage": "1000mg",
                    "form": "Tablet",
                    "color": "#FF6B6B",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [
                            {"time": "08:00", "amount": "1"},
                            {"time": "20:00", "amount": "1"}
                        ],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 4, "threshold": 10},
                    "tablet_stock_count": 4,
                    "cost_per_unit": 4.0,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 800,
            "injection_invoice_amount": 2550,
            "adherence_rate": 68,
            "priority": "high"
        },
        {
            "name": "Lakshmi Devi",
            "email": "lakshmi.devi@email.com",
            "phone": "+91 65432 10987",
            "picture": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=150",
            "age": 72,
            "sex": "Female",
            "address": "23, Jubilee Hills",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "pincode": "500033",
            "diabetes_type": "Type 2",
            "relative_name": "Suresh",
            "relative_whatsapp": "+91 65432 10988",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Losartan 50mg",
                    "dosage": "50mg",
                    "form": "Tablet",
                    "color": "#3498DB",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "08:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 7, "threshold": 10},
                    "tablet_stock_count": 7,
                    "cost_per_unit": 6.0,
                    "include_in_invoice": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Ecosprin 75mg",
                    "dosage": "75mg",
                    "form": "Tablet",
                    "color": "#E74C3C",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "20:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 28, "threshold": 10},
                    "tablet_stock_count": 28,
                    "cost_per_unit": 1.5,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 950,
            "adherence_rate": 75,
            "priority": "normal"
        },
        {
            "name": "Mohammed Ali",
            "email": "mohammed.ali@email.com",
            "phone": "+91 54321 09876",
            "picture": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            "age": 52,
            "sex": "Male",
            "address": "78, Anna Nagar",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India",
            "pincode": "600040",
            "diabetes_type": "Type 2",
            "relative_name": "Fatima Ali",
            "relative_whatsapp": "+91 54321 09877",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Glimepiride 2mg",
                    "dosage": "2mg",
                    "form": "Tablet",
                    "color": "#9B59B6",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "07:30", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 30, "threshold": 10},
                    "tablet_stock_count": 30,
                    "cost_per_unit": 3.5,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 650,
            "adherence_rate": 90,
            "priority": "normal"
        },
        {
            "name": "Geeta Patel",
            "email": "geeta.patel@email.com",
            "phone": "+91 43210 98765",
            "picture": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150",
            "age": 61,
            "sex": "Female",
            "address": "89, CG Road",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "country": "India",
            "pincode": "380009",
            "diabetes_type": "Type 2",
            "relative_name": "Ramesh Patel",
            "relative_whatsapp": "+91 43210 98766",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Sitagliptin 100mg",
                    "dosage": "100mg",
                    "form": "Tablet",
                    "color": "#1ABC9C",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "08:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 9, "threshold": 10},
                    "tablet_stock_count": 9,
                    "cost_per_unit": 25.0,
                    "include_in_invoice": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Ramipril 5mg",
                    "dosage": "5mg",
                    "form": "Tablet",
                    "color": "#3498DB",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "20:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 20, "threshold": 10},
                    "tablet_stock_count": 20,
                    "cost_per_unit": 4.5,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 1850,
            "adherence_rate": 78,
            "priority": "normal"
        },
        {
            "name": "Sunil Verma",
            "email": "sunil.verma@email.com",
            "phone": "+91 32109 87654",
            "picture": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            "age": 45,
            "sex": "Male",
            "address": "56, Salt Lake",
            "city": "Kolkata",
            "state": "West Bengal",
            "country": "India",
            "pincode": "700091",
            "diabetes_type": None,
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Salbutamol Inhaler",
                    "dosage": "100mcg",
                    "form": "Inhaler",
                    "color": "#3498DB",
                    "schedule": {
                        "frequency": "as-needed",
                        "dosage_timings": [],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 0, "threshold": 1},
                    "cost_per_unit": 120,
                    "include_in_invoice": True
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Montelukast 10mg",
                    "dosage": "10mg",
                    "form": "Tablet",
                    "color": "#9B59B6",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "21:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 22, "threshold": 10},
                    "tablet_stock_count": 22,
                    "cost_per_unit": 8.0,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 450,
            "adherence_rate": 88,
            "priority": "normal"
        },
        {
            "name": "Kavitha Menon",
            "email": "kavitha.menon@email.com",
            "phone": "+91 21098 76543",
            "picture": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150",
            "age": 48,
            "sex": "Female",
            "address": "34, Marine Drive",
            "city": "Kochi",
            "state": "Kerala",
            "country": "India",
            "pincode": "682001",
            "diabetes_type": None,
            "relative_name": None,
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Levothyroxine 75mcg",
                    "dosage": "75mcg",
                    "form": "Tablet",
                    "color": "#9B59B6",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "06:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 25, "threshold": 10},
                    "tablet_stock_count": 25,
                    "cost_per_unit": 5.0,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 350,
            "adherence_rate": 92,
            "priority": "low"
        },
        {
            "name": "Dinesh Rao",
            "email": "dinesh.rao@email.com",
            "phone": "+91 10987 65432",
            "picture": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
            "age": 55,
            "sex": "Male",
            "address": "12, Koramangala",
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "India",
            "pincode": "560034",
            "diabetes_type": None,
            "relative_name": "Sunita Rao",
            "relative_whatsapp": "+91 10987 65433",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Diclofenac 50mg",
                    "dosage": "50mg",
                    "form": "Tablet",
                    "color": "#E74C3C",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [
                            {"time": "08:00", "amount": "1"},
                            {"time": "20:00", "amount": "1"}
                        ],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 6, "threshold": 10},
                    "tablet_stock_count": 6,
                    "cost_per_unit": 2.0,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 280,
            "adherence_rate": 85,
            "priority": "normal"
        },
        {
            "name": "Rani Kapoor",
            "email": "rani.kapoor@email.com",
            "phone": "+91 09876 54321",
            "picture": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150",
            "age": 63,
            "sex": "Female",
            "address": "45, Banjara Hills",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "pincode": "500034",
            "diabetes_type": "Type 2",
            "relative_name": "Vijay Kapoor",
            "relative_whatsapp": "+91 09876 54322",
            "medicines": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Pioglitazone 30mg",
                    "dosage": "30mg",
                    "form": "Tablet",
                    "color": "#1ABC9C",
                    "schedule": {
                        "frequency": "daily",
                        "dosage_timings": [{"time": "08:00", "amount": "1"}],
                        "start_date": "2025-01-01"
                    },
                    "refill_reminder": {"enabled": True, "pills_remaining": 12, "threshold": 10},
                    "tablet_stock_count": 12,
                    "cost_per_unit": 6.5,
                    "include_in_invoice": True
                }
            ],
            "medicine_invoice_amount": 580,
            "adherence_rate": 80,
            "priority": "normal"
        }
    ]
    
    # Process each patient
    seeded_patient_ids = []
    for patient_data in sample_patients:
        # Detect diseases from medicines
        diseases = detect_diseases_from_medicines(patient_data.get("medicines", []))
        if patient_data.get("age", 0) >= 65:
            diseases.append("Elderly Care")
        patient_data["diseases"] = list(set(diseases))
        
        # Build caregivers array
        caregivers = []
        if patient_data.get("relative_name"):
            caregivers.append({
                "name": patient_data["relative_name"],
                "phone": patient_data.get("relative_whatsapp", ""),
                "email": patient_data.get("relative_email", ""),
                "relationship": "Family"
            })
        patient_data["caregivers"] = caregivers
        
        # Add user_id to each medicine
        patient_id = str(uuid.uuid4())
        for med in patient_data.get("medicines", []):
            med["user_id"] = patient_id
        
        # Create patient
        patient_obj = Patient(
            id=patient_id,
            interactions=[],
            **patient_data
        )
        await db.patients.insert_one(patient_obj.model_dump())
        seeded_patient_ids.append(patient_id)
        
        # Add sample vitals
        now = datetime.now(timezone.utc)
        for i in range(5):
            date = (now - timedelta(days=i*7)).strftime("%Y-%m-%d")
            
            if "Diabetes" in diseases:
                glucose = BloodGlucose(
                    user_id=patient_id,
                    value=100 + (i * 15) % 80,
                    time="08:00",
                    meal_context="Fasting",
                    date=date
                )
                await db.blood_glucose.insert_one(glucose.model_dump())
            
            if "Hypertension" in diseases or "Heart Disease" in diseases:
                bp = BloodPressure(
                    user_id=patient_id,
                    systolic=120 + (i * 5) % 30,
                    diastolic=80 + (i * 3) % 15,
                    pulse=72 + (i * 2) % 10,
                    time="09:00",
                    date=date
                )
                await db.blood_pressure.insert_one(bp.model_dump())
    
    # Generate opportunities
    await generate_opportunities()

    # Seed sample doctor appointments (some old to trigger 3-month overdue)
    import random as _rnd
    specializations = ["General Medicine", "Cardiology", "Endocrinology", "Orthopedics", "Pulmonology"]
    doctor_names = ["Dr. Suresh Reddy", "Dr. Meena Iyer", "Dr. Anil Gupta", "Dr. Priya Nair", "Dr. Farhan Sheikh"]
    hospital_names = ["Apollo Hospital", "Fortis Healthcare", "Max Hospital", "Manipal Hospital", "AIIMS"]

    for pid in seeded_patient_ids:
        # One old appointment (4-5 months ago) — triggers 3-month overdue
        old_date = (datetime.now() - timedelta(days=_rnd.randint(120, 150))).strftime("%Y-%m-%d")
        old_appt = Appointment(
            user_id=pid,
            type="doctor",
            title="Regular Checkup",
            doctor=_rnd.choice(doctor_names),
            hospital=_rnd.choice(hospital_names),
            date=old_date,
            time=f"{_rnd.randint(9,16):02d}:00",
            location=f"{_rnd.choice(['Bangalore','Mumbai','Delhi','Chennai'])}",
            notes="Routine follow-up visit",
            status="done",
        )
        await db.appointments.insert_one(old_appt.model_dump())

    return {"message": f"Seeded {len(sample_patients)} patients with enCARE-aligned data"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
