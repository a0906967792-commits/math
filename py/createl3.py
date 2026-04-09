import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "鄭姿佳123",
  "mail": "a0906967792@gmail.com",
  "lab": 456
}

# doc_ref = db.collection("靜宜資管").document("tcyang")
# doc_ref.set(doc)

collection_ref = db.collection("靜宜資管")
collection_ref.add(doc)
