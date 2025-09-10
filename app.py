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

def calculate_room_price(beds:int):
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
from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.route("/")
def index():
    # showcase rooms and services
    return render_template("index.html",
                           food_menu=FOOD_MENU,
                           drink_menu=DRINK_MENU,
                           entertainment=ENTERTAINMENT)

@app.route("/rooms")
def rooms():
    # Show room options with bed counts (2..6 for demo)
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

    food_total = 0
    food_items = []
    for key in selected_food:
        item = FOOD_MENU.get(key)
        if item:
            food_items.append(item)
            food_total += item["price"]

    drinks_total = 0
    drink_items = []
    for key in selected_drinks:
        item = DRINK_MENU.get(key)
        if item:
            drink_items.append(item)
            drinks_total += item["price"]

    ent_total = 0
    ent_items = []
    for key in selected_ent:
        item = ENTERTAINMENT.get(key)
        if item:
            ent_items.append(item)
            ent_total += item["price"]

    total = room_price + food_total + drinks_total + ent_total

    # Create order id and store
    order_id = str(uuid.uuid4())
    ORDERS[order_id] = {
        "id": order_id,
        "name": name,
        "phone": phone,
        "beds": beds,
        "nights": nights,
        "room_price": room_price,
        "food_items": food_items,
        "drink_items": drink_items,
        "ent_items": ent_items,
        "totals": {
            "food": food_total,
            "drinks": drinks_total,
            "entertainment": ent_total,
            "total": total
        },
        "paid": False,
        "created_at": datetime.utcnow().isoformat()
    }

    return render_template("checkout.html", order=ORDERS[order_id], mpesa_test_phone=phone)

@app.route("/simulate_mpesa", methods=["POST"])
def simulate_mpesa():
    """
    Simulate a payment request to M-Pesa.
    In production you will call Safaricom Daraja here and handle callbacks.
    """
    data = request.json
    order_id = data.get("order_id")
    phone = data.get("phone")
    if order_id not in ORDERS:
        return jsonify({"status": "error", "message": "Order not found"}), 404

    # For demo: simulate immediate success
    ORDERS[order_id]["paid"] = True
    ORDERS[order_id]["mpesa_receipt"] = "MPESA-"+str(uuid.uuid4())[:8]
    ORDERS[order_id]["paid_at"] = datetime.utcnow().isoformat()

    return jsonify({"status":"success", "order_id": order_id, "receipt": ORDERS[order_id]["mpesa_receipt"]})

@app.route("/receipt/<order_id>")
def receipt(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return "Order not found", 404
    return render_template("receipt.html", order=order)

if __name__ == "__main__":
    app.run(debug=True)
