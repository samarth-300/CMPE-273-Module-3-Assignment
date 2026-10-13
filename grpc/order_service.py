"""Order Service (HTTP on port 5000) -> calls Inventory over gRPC with a deadline."""
import grpc
from flask import Flask, jsonify, request
import inventory_pb2, inventory_pb2_grpc

app = Flask(__name__)
DEADLINE_SECONDS = 2
channel = grpc.insecure_channel("localhost:50051")
stub = inventory_pb2_grpc.InventoryStub(channel)

@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    item_id, qty = data.get("item_id"), data.get("quantity")
    if not isinstance(item_id, str) or not isinstance(qty, int) or qty <= 0:
        return jsonify(error="item_id (string) and quantity (positive int) required"), 400
    try:
        resp = stub.CheckInventory(inventory_pb2.CheckRequest(item_id=item_id, quantity=qty),
                                   timeout=DEADLINE_SECONDS)
        return jsonify(status="accepted", item_id=resp.item_id, quantity=qty,
                       available=resp.available), 201
    except grpc.RpcError as e:
        code = e.code()
        print(f"[order] gRPC error: {code.name} - {e.details()}", flush=True)
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            return jsonify(status="failed", error="inventory deadline exceeded"), 504
        if code == grpc.StatusCode.NOT_FOUND:
            return jsonify(status="rejected", error=e.details()), 404
        if code == grpc.StatusCode.FAILED_PRECONDITION:
            return jsonify(status="rejected", error=e.details()), 409
        if code == grpc.StatusCode.UNAVAILABLE:
            return jsonify(status="failed", error="inventory service unavailable"), 503
        return jsonify(status="failed", error=e.details()), 502

@app.get("/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5000, threaded=True)
