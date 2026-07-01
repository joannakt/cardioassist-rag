from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Claude client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── HARDCODED CLINIC KNOWLEDGE BASE ──
CLINIC_FAQ = """
COMPREHENSIVE CARDIOLOGY — CLINIC INFORMATION

LOCATIONS:
- Nassau Bay: 2200 Nasa Pkwy, Ste 220, Houston, TX 77058
- Friendswood: 107 Woodlawn Dr, Ste 113, Friendswood, TX 77546

PHONE: (281) 333-9200
FAX: (281) 648-8603

OFFICE HOURS:
Monday through Friday. Please call (281) 333-9200 for specific hours.

APPOINTMENTS:
Patients can schedule an appointment by calling our office at (281) 333-9200 during business hours, Monday through Friday. We are currently accepting new patients.

INSURANCE:
We accept most major insurance plans including Medicare, Medicaid, Blue Cross Blue Shield, Aetna, Humana, and United Healthcare. Please call our office at (281) 333-9200 to verify your specific plan before your visit.

PATIENT PORTAL:
We use Healow as our patient portal. Patients can download the Healow app or access it through our website to view records, request refills, and message their provider. Call our office if you need help setting it up.

WHAT TO BRING TO YOUR FIRST APPOINTMENT:
- Valid photo ID
- Insurance card
- List of current medications and dosages
- Any relevant medical records, prior EKGs, echocardiograms, or lab results
- Completed new patient intake forms (available at the front desk or call ahead)
- Referral from your primary care physician if required by your insurance
- Arrive 15 minutes early for your first visit

NEW PATIENTS:
We welcome new patients! Visit our website and click "Become a Patient" or call us at (281) 333-9200 to get started.

OUR TEAM:
- Dr. Vince Nguyen, MD — Interventional Cardiologist
- Dr. Selvin Sudhakar, MD — Interventional Cardiologist
- Dr. Francis Uricchio, MD — Interventional Cardiologist
- Monina Tubat, NP — Nurse Practitioner
- Alma, NP — Nurse Practitioner

SERVICES WE OFFER:
- Echocardiogram: High-resolution ultrasound imaging to assess heart structure and function
- Electrocardiogram (EKG): Quick and painless test that records the electrical activity of the heart
- Stress Testing: Evaluates how the heart performs under physical exertion to detect coronary artery disease
- Cardiac PET Imaging: Advanced nuclear imaging to assess blood flow and heart muscle function
- Holter & Event Monitoring: Continuous heart rhythm monitoring worn over 24-48 hours
- Cardiac Catheterization: Minimally invasive procedure done at Houston Methodist Clear Lake and UTMB
- Vascular Services: Comprehensive vein and artery care including Doppler ultrasounds and endovenous ablation
- Preventive Cardiology: Personalized care to help prevent heart disease

HOSPITAL AFFILIATIONS:
- Houston Methodist Clear Lake Hospital
- UTMB (University of Texas Medical Branch)
- HCA Houston Clear Lake

EMERGENCIES:
For cardiac emergencies, call 911 immediately. Do not wait or call the office first.
"""

# Request model
class ChatRequest(BaseModel):
    messages: List[dict]

@app.post("/chat")
async def chat(request: ChatRequest):
    system_prompt = f"""You are CardioAssist, a friendly and professional virtual assistant for Comprehensive Cardiology, a cardiology clinic serving the Houston, TX area with two locations — Nassau Bay and Friendswood.

You help patients with questions about appointments, insurance, services, locations, and general cardiology information.

Use the following clinic information to answer patient questions accurately:

{CLINIC_FAQ}

Important rules:
- Always be warm, friendly, and professional
- For medical emergencies, always direct patients to call 911 immediately
- Never provide specific medical diagnoses or treatment advice
- If you are unsure about something not covered above, direct patients to call (281) 333-9200
- Keep responses concise and easy to read
- Never use markdown formatting like bold, headers, or bullet points with dashes. Use plain conversational text only
- You are not a substitute for professional medical advice"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        messages=request.messages
    )

    return {"reply": response.content[0].text}

@app.get("/")
async def root():
    return {"status": "CardioAssist backend is running!"}
