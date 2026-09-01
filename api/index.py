from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import os

app = FastAPI(title="KisanMandi Serverless API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Placeholder Configurations (Database / SMS Provider / Auth)
# -------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL", "postgresql://placeholder:placeholder@localhost:5432/mandidb")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC_PLACEHOLDER_TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "PLACEHOLDER_TWILIO_AUTH_TOKEN")
FAST2SMS_API_KEY = os.getenv("FAST2SMS_KEY", "PLACEHOLDER_FAST2SMS_KEY")

def send_sms_alert(phone: str, message: str):
    """
    Plug in real SMS dispatch (Twilio, Fast2SMS, MSG91) here.
    """
    print(f"[SMS DISPATCH] To: {phone} | Message: {message}")
    # Example placeholder:
    # requests.post("https://www.fast2sms.com/dev/bulkV2", headers={"authorization": FAST2SMS_API_KEY}, ...)

# -------------------------------------------------------------
# Mandi List by State (One Primary per State)
# -------------------------------------------------------------
STATE_MANDIS = {
    "Bihar": {"id": "bih-01", "name": "Gulabbagh Mandi (Purnea)", "state": "Bihar", "code": "GUL-01"},
    "Uttar Pradesh": {"id": "up-01", "name": "Sahibabad Mandi (Ghaziabad)", "state": "Uttar Pradesh", "code": "SHB-01"},
    "Punjab": {"id": "pb-01", "name": "Khanna Grain Market (Ludhiana)", "state": "Punjab", "code": "KHN-01"},
    "Haryana": {"id": "hr-01", "name": "Karnal Anaj Mandi", "state": "Haryana", "code": "KRN-01"},
    "Madhya Pradesh": {"id": "mp-01", "name": "Neemuch Mandi", "state": "Madhya Pradesh", "code": "NMC-01"},
    "Maharashtra": {"id": "mh-01", "name": "Lasalgaon Onion Mandi (Nashik)", "state": "Maharashtra", "code": "LSG-01"},
    "Rajasthan": {"id": "rj-01", "name": "Kota Grain Mandi", "state": "Rajasthan", "code": "KTA-01"},
    "West Bengal": {"id": "wb-01", "name": "Durgapur Agricultural Market", "state": "West Bengal", "code": "DGP-01"}
}

# -------------------------------------------------------------
# In-Memory Store (Connect persistent DB like Supabase/Neon here)
# -------------------------------------------------------------
USERS_DB = {}
OTP_STORE = {}
TIME_CHUNKS = [
    {"chunk": "08:00 AM - 10:00 AM", "hour_start": 8},
    {"chunk": "10:00 AM - 12:00 PM", "hour_start": 10},
    {"chunk": "12:00 PM - 02:00 PM", "hour_start": 12},
    {"chunk": "02:00 PM - 04:00 PM", "hour_start": 14},
    {"chunk": "04:00 PM - 06:00 PM", "hour_start": 16}
]

# Booking Schema:
# token_no, user_id, phone, name, state, mandi_id, crop, date, time_chunk, hour_start, status (Booked | In Queue | Under Process | Completed), payment_status (Pending | Paid)
BOOKINGS_DB: List[Dict] = []
CURRENT_TOKEN_INDEX = 1

# Models
class SendOTPRequest(BaseModel):
    phone: str
    name: str
    state: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class BookSlotRequest(BaseModel):
    phone: str
    mandi_id: str
    date: str
    time_chunk: str
    crop_type: str

class AdminStatusUpdateRequest(BaseModel):
    token: str
    status: Optional[str] = None
    payment_status: Optional[str] = None

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/api/mandis")
def get_mandis():
    return {"status": "success", "mandis": STATE_MANDIS}

@app.post("/api/auth/send-otp")
def send_otp(req: SendOTPRequest):
    if len(req.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    # Static demo OTP or connect SMS gateway
    generated_otp = "4321" if req.phone.endswith("00") else "1234"
    OTP_STORE[req.phone] = {
        "otp": generated_otp,
        "name": req.name,
        "state": req.state
    }
    send_sms_alert(req.phone, f"Your KisanMandi Verification OTP is: {generated_otp}")
    return {"status": "success", "message": "OTP sent successfully"}

@app.post("/api/auth/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    record = OTP_STORE.get(req.phone)
    if not record or record["otp"] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    mandi_info = STATE_MANDIS.get(record["state"], STATE_MANDIS["Bihar"])
    user = {
        "phone": req.phone,
        "name": record["name"],
        "state": record["state"],
        "mandi": mandi_info
    }
    USERS_DB[req.phone] = user
    return {"status": "success", "user": user}

@app.get("/api/slots/availability")
def get_slot_availability(date: str, mandi_id: str):
    response = []
    for tc in TIME_CHUNKS:
        booked_count = len([
            b for b in BOOKINGS_DB 
            if b["date"] == date and b["mandi_id"] == mandi_id and b["time_chunk"] == tc["chunk"]
        ])
        remaining = max(0, 12 - booked_count)
        response.append({
            "chunk": tc["chunk"],
            "hour_start": tc["hour_start"],
            "capacity": 12,
            "booked": booked_count,
            "remaining": remaining,
            "is_full": remaining == 0
        })
    return {"status": "success", "date": date, "slots": response}

@app.post("/api/slots/book")
def book_slot(req: BookSlotRequest):
    user_bookings_today = [
        b for b in BOOKINGS_DB 
        if b["phone"] == req.phone and b["date"] == req.date
    ]
    
    # Rule 1: Max 2 slots per day
    if len(user_bookings_today) >= 2:
        raise HTTPException(status_code=400, detail="Booking limit exceeded: You can book at most 2 slots per day.")
    
    # Match chunk start time
    selected_tc = next((tc for tc in TIME_CHUNKS if tc["chunk"] == req.time_chunk), None)
    if not selected_tc:
        raise HTTPException(status_code=400, detail="Invalid time chunk selected")

    # Rule 2: Minimum 2 hours interval between slots
    if len(user_bookings_today) == 1:
        prev_hour = user_bookings_today[0]["hour_start"]
        curr_hour = selected_tc["hour_start"]
        if abs(curr_hour - prev_hour) < 2:
            raise HTTPException(status_code=400, detail="Two slots must have an interval of at least 2 hours.")

    # Rule 3: Slot cap of 12
    booked_count = len([
        b for b in BOOKINGS_DB 
        if b["date"] == req.date and b["mandi_id"] == req.mandi_id and b["time_chunk"] == req.time_chunk
    ])
    if booked_count >= 12:
        raise HTTPException(status_code=400, detail="This time chunk is completely full (12/12).")

    global CURRENT_TOKEN_INDEX
    token_str = f"KM-{100 + CURRENT_TOKEN_INDEX}"
    CURRENT_TOKEN_INDEX += 1

    booking = {
        "token": token_str,
        "phone": req.phone,
        "mandi_id": req.mandi_id,
        "crop": req.crop_type,
        "date": req.date,
        "time_chunk": req.time_chunk,
        "hour_start": selected_tc["hour_start"],
        "status": "In Queue" if len(BOOKINGS_DB) == 0 else "Slot Booked",
        "payment_status": "Pending",
        "created_at": datetime.now().isoformat()
    }
    BOOKINGS_DB.append(booking)
    
    send_sms_alert(req.phone, f"KisanMandi: Slot Confirmed! Token {token_str} for {req.crop_type} on {req.date} ({req.time_chunk}).")
    return {"status": "success", "booking": booking}

@app.get("/api/queue/realtime")
def get_realtime_queue(token: Optional[str] = None):
    active_tokens = [b for b in BOOKINGS_DB if b["status"] != "Completed"]
    currently_serving = next((b for b in BOOKINGS_DB if b["status"] == "Under Process"), None)
    
    if not currently_serving and active_tokens:
        currently_serving = active_tokens[0]

    user_booking = next((b for b in BOOKINGS_DB if b["token"] == token), None) if token else None

    ahead_count = 0
    eta_mins = 0
    if user_booking and user_booking["status"] != "Completed":
        user_idx = next((i for i, b in enumerate(active_tokens) if b["token"] == token), 0)
        ahead_count = max(0, user_idx)
        eta_mins = ahead_count * 15

    return {
        "status": "success",
        "currently_serving": currently_serving["token"] if currently_serving else "None",
        "currently_serving_crop": currently_serving["crop"] if currently_serving else "-",
        "total_active": len(active_tokens),
        "your_token": token,
        "tokens_ahead": ahead_count,
        "eta_minutes": eta_mins,
        "user_booking": user_booking
    }

@app.get("/api/admin/all")
def get_admin_dashboard():
    return {
        "status": "success",
        "bookings": BOOKINGS_DB
    }

@app.post("/api/admin/update")
def update_admin_booking(req: AdminStatusUpdateRequest):
    booking = next((b for b in BOOKINGS_DB if b["token"] == req.token), None)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if req.status:
        booking["status"] = req.status
    if req.payment_status:
        booking["payment_status"] = req.payment_status
        if req.payment_status == "Paid":
            send_sms_alert(booking["phone"], f"KisanMandi: Payment for Token {booking['token']} has been marked as SUCCESSFUL.")

    return {"status": "success", "booking": booking}
