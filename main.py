from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.templating import Jinja2Templates
import requests
import wikipediaapi
from datetime import datetime
import math
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = "..."
APOD_URL = "https://api.nasa.gov/planetary/apod"
ISS_URL = "http://api.open-notify.org/iss-now.json"

wiki_wiki = wikipediaapi.Wikipedia(user_agent='MyProjectName (merlin@example.com)', language='en')

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(track_iss())

@app.get("/")
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/get_apod")
async def get_apod(request: Request, date: str = Form(...)):
    apod_data = requests.get(f"{APOD_URL}?api_key={API_KEY}&date={date}").json()

    date_obj = datetime.strptime(date, "%Y-%m-%d")
    wiki_date = date_obj.strftime("%B %d")
    wiki_date_page = wiki_wiki.page(wiki_date)

    return templates.TemplateResponse("apod.html", {"request": request, "apod_data": apod_data, "wiki_summary" : wiki_date_page.summary if wiki_date_page.exists() else "No data in wikipedia"})

# TRACKING
last_iss_pos, curr_iss_pos = None, None

async def track_iss():
    global last_iss_pos, curr_iss_pos
    while True:
        last_iss_pos = curr_iss_pos
        iss_pos = requests.get(ISS_URL).json()
        curr_iss_pos = (float(iss_pos['iss_position']['latitude']), float(iss_pos['iss_position']['longitude']))
        await asyncio.sleep(5)



def haversine(pos1, pos2):
    if not pos1 or not pos2:
        return None
    lat1, lon1 = pos1
    lat2, lon2 = pos2

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371 

    return round(c * R, 2)
    

@app.get("/iss_position")
async def get_iss_position(request: Request):
    global last_iss_pos, curr_iss_pos

    distance = haversine(last_iss_pos, curr_iss_pos)
    
    iss_data = requests.get(ISS_URL).json()
    return templates.TemplateResponse("iss.html", {"request": request, "iss_data": iss_data, "distance": distance if distance else "Calculating..."})