import asyncio
import aiohttp
import json

# =====================================================================
# 🔧 ZONA DE PRUEBAS: MODIFICA ESTE DICCIONARIO PARA PROBAR TUS REGLAS
# =====================================================================
# Simula el diccionario 'data' que le pasaría tu Workflow a la actividad
payload = {
"input": {
    "action": {
    "phase": "on",
    "task": "open_loan_file"
    },
    "subject": {
            "account_type": "user",
            "email": "",
            "full_name": "",
            "groups": [
              {
                "group_name": "credit_supplier",
                "roles": [
                  {
                    "actions": [
                      {
                        "action": "TAKE_SUPPLIER_ACTIVITY",
                        "details": "Action that allows to take a credit supplier activity"
                      }
                    ],
                    "role": "credit_supplier"
                  }
                ]
              }
            ],
            "password": "$2b$12$dcRVIKSGzjgy6TQRQTjn8Od7Pq5YTaa59R7XZ50NFDv8J7/0XlvW2",
            "permissions": {
              "actions": [
                "TAKE_SUPPLIER_ACTIVITY"
              ],
              "groups": [
                "credit_supplier"
              ],
              "roles": [
                "credit_supplier"
              ],
              "users": [
                "supplier1"
              ]
            },
            "username": "supplier1"
          },
    "object": {
            "ack": {
                "ack": True,
                "days": 1,
                "notification": {
                    "approved": True,
                    "msg": "Loan Approved",
                    "time": "2026-05-17T14:39:22.884404+00:00"
                }
                },
            "lastAccess": None,
            "loan_request": {
              "accepted": False,
              "account": "ES12345678901234567890",
              "amount": 25000,
              "cost": 1000,
              "creditSupplier": {
                "address": "-, Sevilla",
                "id": "supplier-01",
                "name": "Bank 01"
              },
              "customer": {
                "credentials": {
                  "revoked": False,
                  "validated": True
                },
                "email": "aleverbla@alum.us.es",
                "id": "cust-ale-01",
                "institution": "Universidad de Sevilla",
                "lastAccess": "2026-05-17T14:38:43.049141+00:00",
                "lastName": "Vera",
                "name": "Ale",
                "remuneration": 4000
              },
              "customerAccount": {
                "accountNumber": "ES12345678901234567890",
                "balance": 5000
              },
              "gpdrAgreement": {
                "gpdrValidated": True
              },
              "id": "req-c85af6ad",
              "loanTerms": True,
              "notified": False,
              "pending": True,
              "timestamp": "2026-05-17T14:38:43.049120+00:00"
            },
            "rate": 0,
            "risk": "LOW",
            "sent": False
          },
    "environment": {
            "control_time_system_active": True,
            "current_time": "10:00:00",
            "device_type": "desktop",
            "history": {
              "active_loan_reviews": 5,
              "active_loans": 2,
              "pending_inactive_reports": 2,
              "tasks_done": [
                [
                  "fulfil_loan_info",
                  "customer1"
                ],
                [
                  "request_a_loan",
                  "customer1"
                ],
                [
                  "collect_customer_information",
                  "supplier1"
                ],
                [
                  "receive_loan_request",
                  "staff1"
                ],
                [
                  "evaluate_risk_1",
                  "staff1"
                ],
                [
                  "evaluate_risk_2",
                  "staff2"
                ],
                [
                  "send_approved_notification",
                  "supplier1"
                ]
              ]
            }
    }
}
}

async def test_opa():
    
    # 1. Construir la URL dinámica según la fase
    phase = payload["input"]["action"]["phase"].lower()
    print(f"🚀 Iniciando simulación de OPA para fase: {phase}")
    opa_url = f"http://localhost:8181/v1/data/ucon/{phase}"
    print(f"🔗 URL de OPA: {opa_url}")

    print("-" * 50)
    print("📦 Payload formateado que se envía a OPA:")
    print(json.dumps(payload, indent=2))
    print("-" * 50)

    # 3. Conexión con OPA
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(opa_url, json=payload) as response:
                if response.status == 200:
                    opa_response = await response.json()
                    
                    # Extraer el resultado igual que en tu actividad
                    result = opa_response.get("result", {"allow": False})
                    
                    print(f"📡 Estado HTTP devuelto: {response.status}")
                    print("✅ Respuesta de OPA:")
                    print(json.dumps(result, indent=2))
                    
                    if result.get("allow"):
                        print("\n🟢 VEREDICTO: Acceso PERMITIDO")
                    else:
                        print("\n🔴 VEREDICTO: Acceso DENEGADO")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error HTTP de OPA: {response.status} - {error_text}")
                    
    except aiohttp.ClientError as e:
        print(f"❌ Error crítico de red conectando con OPA: {e}")
        print("💡 Pista: ¿Está el contenedor de OPA corriendo en localhost:8181?")

if __name__ == "__main__":
    asyncio.run(test_opa())