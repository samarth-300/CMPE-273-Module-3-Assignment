"""gRPC Inventory Service (port 50051).
Set INVENTORY_DELAY_SECONDS to simulate a slow service."""
import os, time
from concurrent import futures
import grpc
import inventory_pb2, inventory_pb2_grpc

STOCK = {"apple": 100, "banana": 5, "cherry": 0}
DELAY = float(os.environ.get("INVENTORY_DELAY_SECONDS", "0"))

class InventoryServicer(inventory_pb2_grpc.InventoryServicer):
    def CheckInventory(self, request, context):
        if request.quantity <= 0 or not request.item_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "item_id and positive quantity required")
        if DELAY:
            print(f"[inventory] sleeping {DELAY}s", flush=True)
            time.sleep(DELAY)
        if request.item_id not in STOCK:
            context.abort(grpc.StatusCode.NOT_FOUND, f"item '{request.item_id}' not found")
        avail = STOCK[request.item_id]
        if avail < request.quantity:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                          f"insufficient stock: requested {request.quantity}, available {avail}")
        return inventory_pb2.CheckResponse(item_id=request.item_id, requested=request.quantity,
                                           available=avail, in_stock=True)

if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServicer_to_server(InventoryServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC inventory listening on :50051", flush=True)
    server.wait_for_termination()
