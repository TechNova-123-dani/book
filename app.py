from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import uuid

app = Flask(__name__)

# --- Pricing config (change as needed) ---
ROOM_BASE_PRICE_FOR_2_BEDS = 1200
ROOM_PRICE_FOR_3_BEDS = 1600
EXTRA_PER_BED_AFTER_3 = 200

# Example extras
FOOD_MENU = {
    "ugali_beef_plate": {"name": "Ugali & Beef Plate", "price": 450},
    "pilau_chicken": {"name": "Pilau with Chicken", "price": 500},
    "chips_sausage": {"name": "Chips & Sausage", "price": 350},
}

DRINK_MENU = {
    "water": {"name": "Bottled Water", "price": 50},
    "soft_drink": {"name": "Soft Drink (500ml)", "price": 120},
    "beer": {"name": "Local Beer", "price": 250},
}

ENTERTAINMENT = {
    "tv": {"name": "TV (per day)", "price": 300},
    "projector": {"name": "Projector (per day)", "price": 800},
}

# In-memory "orders" for demo (use DB in production)
ORDERS = {}

def calculate_room_price(beds: int):
    if beds <= 1:
        # not expected but handle gracefully (charge as single bed)
        return ROOM_BASE_PRICE_FOR_2_BEDS // 2
    if beds == 2:
        return ROOM_BASE_PRICE_FOR_2_BEDS
    if beds == 3:
        return ROOM_PRICE_FOR_3_BEDS
    # beds > 3
    extra = (beds - 3) * EXTRA_PER_BED_AFTER_3
    return ROOM_PRICE_FOR_3_BEDS + extra


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}


@app.route("/")
def index():
    return render_template(
        "index.html",
        food_menu=FOOD_MENU,
        drink_menu=DRINK_MENU,
        entertainment=ENTERTAINMENT,
    )


@app.route("/rooms")
def rooms():
    room_options = []
    for beds in range(2, 7):
        room_options.append({
            "beds": beds,
            "price": calculate_room_price(beds),
            "title": f"{beds}-Bed Room"
        })
    return render_template("rooms.html", room_options=room_options)


@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.form
    name = data.get("name")
    phone = data.get("phone")
    beds = int(data.get("beds", 2))
    nights = int(data.get("nights", 1))
    selected_food = data.getlist("food")
    selected_drinks = data.getlist("drinks")
    selected_ent = data.getlist("entertainment")

    room_price = calculate_room_price(beds) * nights

    food_total = sum(FOOD_MENU[f]["price"] for f in selected_food if f in FOOD_MENU)
    food_items = [FOOD_MENU[f] for f in selected_food if f in FOOD_MENU]

    drinks_total = sum(DRINK_MENU[d]["price"] for d in selected_drinks if d in DRINK_MENU)
    drink_items = [DRINK_MENU[d] for d in selected_drinks if d in DRINK_MENU]

    ent_total = sum(ENTERTAINMENT[e]["price"] for e in selected_ent if e in ENTERTAINMENT)
    ent_items = [ENTERTAINMENT[e] for e in selected_ent if e in ENTERTAINMENT]

    total = room_price + food_total + drinks_total + ent_total

    order_id = str(uuid.uuid4())
    ORDERS[order_id] = {
        "id": order_id,
        