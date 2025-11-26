from pydantic import BaseModel,Field,field_validator
from fastapi import FastAPI, HTTPException, Request,File,UploadFile
from fastapi.responses import JSONResponse
from io import StringIO
import uvicorn
import csv

import os
import json


app = FastAPI()

DATA = {}
DATA2 = {}

class Soldier(BaseModel):
    personal_id : int
    first_name : str
    last_name : str
    gender : str
    city : str
    distance_km : int
    status : str = "waited"
    building : str | None = None
    room : int | None = None


    @field_validator("personal_id")
    def verifie_commence_par_8(cls, id):
        if not str(id).startswith("8"):
            raise ValueError("must be satrt with 8")
        return id
    
class Room:
    def __init__(self, num):
        self.num = num
        self.room_capacity = 8
        self.soldiers_in_room = []

    def have_place(self):
        return len(self.soldiers_in_room) < self.room_capacity

    def add_soldier_in_room(self, soldier):
        if self.have_place():
            self.soldiers_in_room.append(soldier)
            return True
        return False


class ResidentialHouse():
    def __init__(self, name):
        self.name = name
        self.rooms = [ Room(i + 1) for i in range(10) ]
        self.filled_room = 0
        # self.room_not_filled = 
        self.empty_room = 10
    def assign(self, soldier):
        for room in self.rooms:
            if room.have_place():
                room.add_soldier_in_room(soldier)
                soldier.status = "assigned"
                soldier.building = self.name
                soldier.room = room.num
                self.filled_room +=1
                self.empty_room -=1
                return True
        return False
    def info(self):
        return {'filled_room':self.filled_room,
                'empty_room' : self.empty_room}




class BaseChibolim:
    def __init__(self):
        self.buildings = [ResidentialHouse("Dorm A"), ResidentialHouse("Dorm B")]
        self.soldiers_waiting = []

    def assign_soldier(self, soldier):
        for b in self.buildings:
            if b.assign(soldier):
                return

        self.soldiers_waiting.append(soldier)


chibolim = BaseChibolim()
def create_and_sort(reader):
    soldiers = []

    for row in reader:
            s = Soldier(
                personal_id=row["personal_id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                gender=row["gender"],
                city=row["city"],
                distance_km=int(row["distance_km"])
            )
            soldiers.append(s)

    soldiers.sort(key=lambda x: x.distance_km, reverse=True)
    return soldiers



    
   
@app.post("/assignWithCsv")
async def assign_with_csv(file: UploadFile =  File(...)):
     global DATA 
     global DATA2
     if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
 

     data = await file.read()
     text = data.decode("utf-8")
     reader = csv.DictReader(StringIO(text))

     soldiers = create_and_sort(reader)

     for s in soldiers:
         chibolim.assign_soldier(s)

     res = {
        "nb_assigned": len([s for s in soldiers if s.status == "assigned"]),
        "nb_waited": len([s for s in soldiers if s.status == "waited"]),
        "soldiers": [
            {
                "personal_number": s.personal_id,
                "status": s.status,
                "building": s.building,
                "room": s.room
            }
            for s in soldiers
        ]
    }
     
     DATA = res
     DATA2 = chibolim.buildings
     return JSONResponse(res)



@app.get("/space")
def get_space():
    nb_empty_room = 0
    for i in DATA2:
        nb_empty_room += (i.empty_room)
    nb_filled_room = 0
    for i in DATA2:
        nb_empty_room += (i.filled_room)
    
    res = {'nb_empty_room':nb_empty_room,
           'nb_filled_room':nb_filled_room}
    return JSONResponse(res)


    
    
    


@app.get("/waitingList")
def get_waiting():
    waiting_soldiers=[]

    for i in DATA["soldiers"]:
        if i['status']=='waited':
            waiting_soldiers.append(i)
    res = {'waiting_soldiers': waiting_soldiers}
    return JSONResponse(res)



@app.get("/search/{personal_number}")
def get_soldier_by_id(personal_number:int):
    res = ''
    for i in DATA["soldiers"]:
        if i['personal_number'] == personal_number:
            res = i

    return JSONResponse(res)









# 'hayal_300_no_status.csv'