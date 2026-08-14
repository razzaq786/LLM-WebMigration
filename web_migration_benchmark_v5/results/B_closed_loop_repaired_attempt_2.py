from flask import Flask, jsonify, request

app = Flask(__name__)

ITEMS = [
    {"id": 1, "name": "Alpha", "qty": 2},
    {"id": 2, "name": "Beta", "qty": 5}
]

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/items")
def items():
    return jsonify({"items": ITEMS})

@app.get("/items/<int:item_id>")
def get_item(item_id):
    for x in ITEMS:
        if x["id"] == item_id:
            return jsonify(x)
    return jsonify({"error": "not_found"}), 404

@app.post("/items")
def create():
    data = request.get_json(silent=True) or {}
    if "name" not in data or "qty" not in data:
        return jsonify({"error": "bad_request"}), 400
    new_id = max(item["id"] for item in ITEMS) + 1 if ITEMS else 1
    new_item = {"id": new_id, "name": data["name"], "qty": data["qty"]}
    ITEMS.append(new_item)
    return jsonify(new_item), 201

@app.put("/items/<int:item_id>")
def update(item_id):
    data = request.get_json(silent=True) or {}
    if "name" not in data or "qty" not in data:
        return jsonify({"error": "bad_request"}), 400
    for item in ITEMS:
        if item["id"] == item_id:
            item["name"] = data["name"]
            item["qty"] = data["qty"]
            return jsonify(item)
    return jsonify({"error": "not_found"}), 404

@app.delete("/items/<int:item_id>")
def delete(item_id):
    for i, item in enumerate(ITEMS):
        if item["id"] == item_id:
            ITEMS.pop(i)
            return '', 204
    return jsonify({"error": "not_found"}), 404
