from fastapi import FastAPI, Query, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ------------------ DATA ------------------
rooms = [
    {"id": 1, "room_number": "101", "type": "Single", "price_per_night": 1000, "floor": 1, "is_available": True},
    {"id": 2, "room_number": "102", "type": "Double", "price_per_night": 2000, "floor": 1, "is_available": True},
    {"id": 3, "room_number": "201", "type": "Suite", "price_per_night": 4000, "floor": 2, "is_available": True},
    {"id": 4, "room_number": "202", "type": "Deluxe", "price_per_night": 3000, "floor": 2, "is_available": False},
]

bookings = []
booking_counter = 1
cart = []

# ------------------ Q1 ------------------
@app.get("/")
def home():
    return {"message": "Welcome to Hotel Booking System"}

# ------------------ Q2 ------------------
@app.get("/rooms")
def get_rooms():
    return {
        "total": len(rooms),
        "available": sum(r["is_available"] for r in rooms),
        "rooms": rooms
    }

# ------------------ Q5 ------------------
@app.get("/rooms/summary")
def summary():
    types = {}
    for r in rooms:
        types[r["type"]] = types.get(r["type"], 0) + 1

    return {
        "total_rooms": len(rooms),
        "available": sum(r["is_available"] for r in rooms),
        "occupied": len(rooms) - sum(r["is_available"] for r in rooms),
        "types": types
    }

# ------------------ Q3 ------------------
@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    for r in rooms:
        if r["id"] == room_id:
            return r
    return {"error": "Room not found"}

# ------------------ Q4 ------------------
@app.get("/bookings")
def get_bookings():
    return {"total": len(bookings), "bookings": bookings}

# ------------------ Q6 ------------------
class BookingRequest(BaseModel):
    guest_name: str = Field(..., min_length=2)
    room_id: int = Field(..., gt=0)
    nights: int = Field(..., gt=0, le=30)
    phone: str = Field(..., min_length=10)
    meal_plan: Optional[str] = "none"
    early_checkout: Optional[bool] = False

# ------------------ Q7 ------------------
def find_room(room_id):
    for r in rooms:
        if r["id"] == room_id:
            return r
    return None

def calculate_cost(price, nights, meal_plan, early_checkout):
    total = price * nights

    if meal_plan == "breakfast":
        total += 500 * nights
    elif meal_plan == "all-inclusive":
        total += 1200 * nights

    discount = 0
    if early_checkout:
        discount = total * 0.1
        total -= discount

    return total, discount

# ------------------ Q8 ------------------
@app.post("/bookings")
def create_booking(data: BookingRequest):
    global booking_counter

    room = find_room(data.room_id)

    if not room:
        raise HTTPException(404, "Room not found")

    if not room["is_available"]:
        raise HTTPException(400, "Room not available")

    total, discount = calculate_cost(
        room["price_per_night"],
        data.nights,
        data.meal_plan,
        data.early_checkout
    )

    booking = {
        "booking_id": booking_counter,
        "guest_name": data.guest_name,
        "phone": data.phone,
        "room_id": data.room_id,
        "nights": data.nights,
        "total": total,
        "discount": discount
    }

    room["is_available"] = False
    bookings.append(booking)
    booking_counter += 1

    return booking
# ------------------ Q10 ------------------
@app.get("/rooms/filter")
def filter_rooms(
    type: Optional[str] = None,
    max_price: Optional[int] = None,
    is_available: Optional[bool] = None
):
    result = []

    for r in rooms:
        if type is not None and r["type"] != type:
            continue
        if max_price is not None and r["price_per_night"] > max_price:
            continue
        if is_available is not None and r["is_available"] != is_available:
            continue

        result.append(r)

    return {"total": len(result), "rooms": result}


# ------------------ Q11 ------------------
class NewRoom(BaseModel):
    room_number: str
    type: str
    price_per_night: int
    floor: int
    is_available: bool = True

@app.post("/rooms")
def add_room(data: NewRoom, response: Response):
    new_id = len(rooms) + 1
    room = data.dict()
    room["id"] = new_id
    rooms.append(room)
    response.status_code = 201
    return room

# ------------------ Q12 ------------------
@app.put("/rooms/{room_id}")
def update_room(room_id: int,
                price: Optional[int] = None,
                is_available: Optional[bool] = None):

    room = find_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")

    if price is not None:
        room["price_per_night"] = price

    if is_available is not None:
        room["is_available"] = is_available

    return room

# ------------------ Q13 ------------------
@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")

    rooms.remove(room)
    return {"message": "Deleted", "room": room}

# ------------------ Q14 ------------------
@app.post("/cart/add")
def add_cart(room_id: int, nights: int = 1):
    room = find_room(room_id)

    if not room or not room["is_available"]:
        return {"error": "Room not available"}

    cart.append({"room_id": room_id, "nights": nights})
    return {"cart": cart}

# ------------------ Q15 ------------------
@app.post("/cart/checkout")
def checkout(name: str, phone: str):
    global booking_counter

    if not cart:
        return {"error": "Cart empty"}

    result = []

    for c in cart:
        room = find_room(c["room_id"])
        total = room["price_per_night"] * c["nights"]

        booking = {
            "booking_id": booking_counter,
            "guest_name": name,
            "phone": phone,
            "room_id": c["room_id"],
            "total": total
        }

        room["is_available"] = False
        bookings.append(booking)
        result.append(booking)
        booking_counter += 1

    cart.clear()
    return {"bookings": result}

# ------------------ Q16 ------------------
@app.get("/rooms/search")
def search_rooms(keyword: str):
    result = [r for r in rooms if keyword.lower() in r["type"].lower()]
    return {"total": len(result), "rooms": result}

# ------------------ Q17 ------------------
@app.get("/rooms/sort")
def sort_rooms(sort_by: str = "price_per_night", order: str = "asc"):
    reverse = order == "desc"
    sorted_rooms = sorted(rooms, key=lambda x: x[sort_by], reverse=reverse)
    return sorted_rooms

# ------------------ Q18 ------------------
@app.get("/rooms/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    data = rooms[start:start + limit]

    return {
        "page": page,
        "total": len(rooms),
        "data": data
    }

# ------------------ Q19 ------------------
@app.get("/bookings/search")
def search_bookings(name: str):
    result = [b for b in bookings if name.lower() in b["guest_name"].lower()]
    return {"total": len(result), "bookings": result}

# ------------------ Q20 ------------------
@app.get("/rooms/browse")
def browse(keyword: Optional[str] = None,
           page: int = 1,
           limit: int = 2):

    data = rooms

    if keyword:
        data = [r for r in data if keyword.lower() in r["type"].lower()]

    start = (page - 1) * limit
    data = data[start:start + limit]

    return {"result": data}
