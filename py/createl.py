import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "鄭姿佳",
  "mail": "a0906967792@gmail.com",
  "lab": 579
}

doc_ref = db.collection("靜宜資管2026B").document("zijia")
doc_ref.set(doc)


