"""
SUPPLIER – VENDOR MANAGEMENT SYSTEM
Pure Python Backend (NO external libraries)

Features:
- Supplier → Vendor (one supplier, many vendors)
- Vendor creation with full details
- Purchase records per vendor
- Invoice generation
- Invoice PDF generation (pure Python)
- Payment tracking
- Vendor loyalty score
- JSON data storage
- REST-like HTTP backend
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime

# -------------------- STORAGE --------------------

DATA_DIR = "data"
FILES = {
    "vendors": "vendors.json",
    "purchases": "purchases.json",
    "invoices": "invoices.json",
    "payments": "payments.json"
}


def init_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    for file in FILES.values():
        path = os.path.join(DATA_DIR, file)
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)


def load(name):
    try:
        with open(os.path.join(DATA_DIR, FILES[name]), "r") as f:
            return json.load(f)
    except:
        return []


def save(name, data):
    with open(os.path.join(DATA_DIR, FILES[name]), "w") as f:
        json.dump(data, f, indent=4)


def new_id(data):
    return max([d["id"] for d in data], default=0) + 1


# -------------------- BUSINESS LOGIC --------------------

def calculate_vendor_score(vendor_id):
    invoices = load("invoices")
    payments = load("payments")

    total = 0
    paid = 0

    for inv in invoices:
        if inv["vendor_id"] == vendor_id:
            total += 1
            for pay in payments:
                if pay["invoice_id"] == inv["id"] and pay["status"] == "PAID":
                    paid += 1

    return round((paid / total) * 100, 2) if total > 0 else 0


# -------------------- PDF GENERATION --------------------

def generate_invoice_pdf(invoice):
    filename = f"invoice_{invoice['id']}.pdf"
    path = os.path.join(DATA_DIR, filename)

    text = f"""
Invoice ID: {invoice['id']}
Vendor ID: {invoice['vendor_id']}
Amount: {invoice['amount']}
Status: {invoice['status']}
Date: {invoice['date']}
"""

    pdf = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length {len(text)} >> stream
{text}
endstream endobj
xref
0 5
0000000000 65535 f
trailer << /Root 1 0 R /Size 5 >>
startxref
0
%%EOF
"""

    with open(path, "w") as f:
        f.write(pdf)

    return filename


# -------------------- HTTP SERVER --------------------

class Handler(BaseHTTPRequestHandler):

    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/":
            self.respond({
                "message": "Supplier Vendor Management Backend Running",
                "endpoints": [
                    "/vendors",
                    "/vendor/create",
                    "/purchase/add",
                    "/invoice/create",
                    "/payment/pay"
                ]
            })

        elif self.path == "/vendors":
            vendors = load("vendors")
            self.respond(vendors)

        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        data = parse_qs(body)

        # CREATE VENDOR
        if self.path == "/vendor/create":
            vendors = load("vendors")

            vendor = {
                "id": new_id(vendors),
                "shop_name": data["shop_name"][0],
                "owner": data["owner"][0],
                "contact": data["contact"][0],
                "score": 0
            }

            vendors.append(vendor)
            save("vendors", vendors)
            self.respond(vendor)

        # ADD PURCHASE
        elif self.path == "/purchase/add":
            purchases = load("purchases")

            purchase = {
                "id": new_id(purchases),
                "vendor_id": int(data["vendor_id"][0]),
                "item": data["item"][0],
                "amount": float(data["amount"][0])
            }

            purchases.append(purchase)
            save("purchases", purchases)
            self.respond(purchase)

        # CREATE INVOICE
        elif self.path == "/invoice/create":
            invoices = load("invoices")

            invoice = {
                "id": new_id(invoices),
                "vendor_id": int(data["vendor_id"][0]),
                "amount": float(data["amount"][0]),
                "status": "PENDING",
                "date": str(datetime.now())
            }

            invoice["pdf"] = generate_invoice_pdf(invoice)
            invoices.append(invoice)
            save("invoices", invoices)
            self.respond(invoice)

        # PAY INVOICE
        elif self.path == "/payment/pay":
            invoice_id = int(data["invoice_id"][0])
            invoices = load("invoices")
            payments = load("payments")
            vendors = load("vendors")

            for inv in invoices:
                if inv["id"] == invoice_id:
                    inv["status"] = "PAID"
                    payments.append({
                        "id": new_id(payments),
                        "invoice_id": invoice_id,
                        "status": "PAID"
                    })

                    for v in vendors:
                        if v["id"] == inv["vendor_id"]:
                            v["score"] = calculate_vendor_score(v["id"])

                    save("invoices", invoices)
                    save("payments", payments)
                    save("vendors", vendors)

                    self.respond({"message": "Payment successful"})
                    return

            self.send_error(404)

        else:
            self.send_error(404)


# -------------------- RUN SERVER --------------------

def run():
    init_storage()
    server = HTTPServer(("localhost", 8000), Handler)
    print("Server running at http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
