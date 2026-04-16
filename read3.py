import firebase_admin
from firebase_admin import credentials, firestore


cred = credentials.Certificate("serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

keyword = "楊"
collection_ref = db.collection("靜宜資管")
docs = collection_ref.get()
for doc in docs:
    teacher = doc.to_dict()
    if keyword in teacher["name"]:
        print(doc.to_dict()) # 這裡要縮排