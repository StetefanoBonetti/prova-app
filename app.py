from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import pdfplumber
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI
import os
import uvicorn

app = FastAPI()

# Legge variabili ambiente da Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.post("/process")
async def process_file(file: UploadFile, email: str = Form(...)):
    try:
        text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        # Riassunto con GPT
        prompt = f"Riassumi il seguente testo in stile rassegna stampa:\n\n{text[:5000]}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        summary = response.choices[0].message.content

        # Invia mail
        msg = MIMEText(summary, "plain", "utf-8")
        msg["Subject"] = "Rassegna Stampa"
        msg["From"] = EMAIL_SENDER
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [email], msg.as_string())

        return JSONResponse({"status": "ok", "message": f"Email inviata a {email}"})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# Avvio server per Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render fornisce PORT
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
