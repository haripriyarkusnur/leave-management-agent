from fastapi import FastAPI
from db.mongo_client import get_db
from models.employee import Employee
from datetime import datetime
import httpx
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()
db = get_db()
collection = db["employees"]

# Email configuration
OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL", "your outlook mail")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD", "your app pswd")
OUTLOOK_SMTP_SERVER = "smtp.gmail.com"  # Changed to Gmail SMTP server
OUTLOOK_SMTP_PORT = 587
ADMIN_EMAIL = "kusnur.haripriya@infokalash.com"  # Admin email for notifications

# Use env var for security; fallback to hardcoded ONLY for testing (not recommended in production)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your open api key")
MODEL = "deepseek/deepseek-r1-0528"

async def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = OUTLOOK_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(OUTLOOK_SMTP_SERVER, OUTLOOK_SMTP_PORT)
        server.starttls()
        server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

# ---- AI AGENT LOGIC ----
async def ai_agent_response(employee: dict) -> str:
    # Check leave policy based on probation status
    if employee['is_on_probation']:
        # Probation employees: 1 leave per month
        if employee['applied_leaves'] == 1:
            return "Leave approved automatically."
        else:
            return "Your leave request has been notified to your manager. Note: Probation employees are allowed only 1 leave per month."
    else:
        # Regular employees: 2 leaves per month
        if employee['applied_leaves'] <= 2:
            return "Leave approved automatically."
        else:
            return "Your leave request has been notified to your manager. Note: Regular employees are allowed up to 2 leaves per month."

# ---- POST EMPLOYEE ----
@app.post("/employees/")
async def create_employee(employee: Employee):
    employee_dict = employee.dict()

    try:
        # Convert date string to datetime
        employee_dict["date_of_joining"] = datetime.strptime(employee_dict["date_of_joining"], "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # Insert into DB
    result = collection.insert_one(employee_dict)

    # AI response
    ai_response = await ai_agent_response(employee.dict())
    
    # Send email notification to admin (kusnur.haripriya@infokalash.com)
    admin_email_subject = f"Leave Request | {employee_dict['emp_name']} | {datetime.now().strftime('%d %B %Y')}"
    
    # Customize admin email based on leave policy
    if (employee_dict['is_on_probation'] and employee_dict['applied_leaves'] == 1) or \
       (not employee_dict['is_on_probation'] and employee_dict['applied_leaves'] <= 2):
        admin_email_body = f"""
Dear {employee_dict['emp_name']},

Your leave request has been successfully approved as per company policy.

📌 Leave Summary:
- Employee ID       : {employee_dict['emp_id']}
- Department        : {employee_dict['dept']}
- Role             : {employee_dict['role']}
- Leaves Applied    : {employee_dict['applied_leaves']}
- Total Leaves      : {employee_dict['total_leaves']}
- Status           : Approved
- Employee Type     : {'Probation' if employee_dict['is_on_probation'] else 'Regular'}

Wishing you a restful time off. Please reach out if any changes are required.

Warm regards,
HR Department
    """
    else:
        admin_email_body = f"""
Dear {employee_dict['emp_name']},

Your leave request has been notified to your manager.

📌 Leave Summary:
- Employee ID       : {employee_dict['emp_id']}
- Department        : {employee_dict['dept']}
- Role             : {employee_dict['role']}
- Leaves Applied    : {employee_dict['applied_leaves']}
- Total Leaves      : {employee_dict['total_leaves']}
- Status           : Pending Manager Approval
- Employee Type     : {'Probation' if employee_dict['is_on_probation'] else 'Regular'}
- Policy Note      : {'1 leave per month' if employee_dict['is_on_probation'] else '2 leaves per month'}

Wishing you a restful time off. Please reach out if any changes are required.

Warm regards,
HR Department
    """
    
    # Send email to admin
    admin_email_sent = await send_email(
        to_email=ADMIN_EMAIL,
        subject=admin_email_subject,
        body=admin_email_body
    )

    # Send email notification to employee
    employee_email_subject = f"Leave Request Status | {employee_dict['emp_name']} | {datetime.now().strftime('%d %B %Y')}"
    
    # Customize employee email based on leave policy
    if (employee_dict['is_on_probation'] and employee_dict['applied_leaves'] == 1) or \
       (not employee_dict['is_on_probation'] and employee_dict['applied_leaves'] <= 2):
        employee_email_body = f"""
Dear {employee_dict['emp_name']},

Your leave request has been successfully approved as per company policy.

📌 Leave Summary:
- Employee ID       : {employee_dict['emp_id']}
- Department        : {employee_dict['dept']}
- Role             : {employee_dict['role']}
- Leaves Applied    : {employee_dict['applied_leaves']}
- Total Leaves      : {employee_dict['total_leaves']}
- Status           : Approved
- Employee Type     : {'Probation' if employee_dict['is_on_probation'] else 'Regular'}

Wishing you a restful time off. Please reach out if any changes are required.

Warm regards,
HR Department
        """
    else:
        employee_email_body = f"""
Dear {employee_dict['emp_name']},

Your leave request has been notified to your manager.

📌 Leave Summary:
- Employee ID       : {employee_dict['emp_id']}
- Department        : {employee_dict['dept']}
- Role             : {employee_dict['role']}
- Leaves Applied    : {employee_dict['applied_leaves']}
- Total Leaves      : {employee_dict['total_leaves']}
- Status           : Pending Manager Approval
- Employee Type     : {'Probation' if employee_dict['is_on_probation'] else 'Regular'}
- Policy Note      : {'1 leave per month' if employee_dict['is_on_probation'] else '2 leaves per month'}

Wishing you a restful time off. Please reach out if any changes are required.

Warm regards,
HR Department
        """
    
    # Send email to employee
    employee_email_sent = await send_email(
        to_email=employee_dict['email'],
        subject=employee_email_subject,
        body=employee_email_body
    )

    return {
        "message": "Employee added",
        "id": str(result.inserted_id),
        "agent_response": ai_response,
        "admin_email_sent": admin_email_sent,
        "employee_email_sent": employee_email_sent
    }

# ---- GET ALL EMPLOYEES ----
@app.get("/employees/")
def get_all_employees():
    try:
        employees = list(collection.find())
        for emp in employees:
            emp["_id"] = str(emp["_id"])
            # Handle date serialization safely
            if "date_of_joining" in emp and isinstance(emp["date_of_joining"], datetime):
                emp["date_of_joining"] = emp["date_of_joining"].strftime("%Y-%m-%d")
        return employees
    except Exception as e:
        return {"error": f"Failed to fetch employees: {str(e)}"}
