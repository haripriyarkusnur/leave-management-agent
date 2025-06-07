# leave-management-agent
An AI-powered leave management system that auto-approves requests or notifies managers based on dynamic employee policies.


# Features

- Auto approval of leaves based on policies
- Sends email notifications to manager when rules are breached
- Handles probation and regular employee policies differently
- Built using FastAPI with Swagger UI for easy testing
- Uses MongoDB for storing employee and leave data
- Email service using SMTP
- Integrates OpenAI model {example: `deepseek/deepseek-r1-0528`} for smart leave analysis *(optional/extendable)*

---

# Tech Stack

- Python 3.11+
- FastAPI
- MongoDB
- OpenAI (deepseek-r1-0528)
- HTTPX
- SMTP for email
- Pydantic
- Uvicorn

# pip install requirements.txt

