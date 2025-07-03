import pandas as pd
import pickle
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("cred.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

with open('predict_introvert.pkl', 'rb') as f:
    isIntrovert = pickle.load(f)

app = Flask(__name__)

ALLOWED_IP = '192.168.50.'

@app.before_request
def limit_remote_addr():
    client_ip = request.remote_addr
    if not client_ip.startswith(ALLOWED_IP):
    	abort(403)  

@app.route('/') 
def home():

	doc = {
		"description": "Expected JSON payload structure for the prediction of introvertion.",
        "payload": {
            "time_alone": "int - Time spent alone (hours per day)",
            "fear": "bool - Stage fear, True or False",
            "events_attendance": "int - Number of social events attended in a months",
            "going_out": "int - Frequency of going outside during a week",
            "drain_social": "bool - Drained after socializing, True or False",
            "num_friends": "int - Number of friends in social circle",
            "post_frequency": "int - Frequency of social media posts in a week"
    	},
        "example_payload": {
            "time_alone": 3,
            "fear": False,
            "events_attendance": 4,
            "going_out": 2,
            "drain_social": True,
            "num_friends": 10,
            "post_frequency": 1
        }
	}        
	return jsonify(doc)

@app.route('/predict_introvert', methods=['GET']) 
def predecir_si_introvert():

	#0.- conseguir datos payload
	time_alone = request.get_json().get('time_alone')
	fear = int(request.get_json().get('fear'))
	events = request.get_json().get('events_attendance')
	going_out = request.get_json().get('going_out')
	drain_social = int(request.get_json().get('drain_social'))
	friends = request.get_json().get('num_friends')
	post_freq = request.get_json().get("post_frequency")

	#1.- predecir
	x = pd.DataFrame([{"Time_spent_Alone":time_alone, "Stage_fear":fear, "Social_event_attendance":events, "Going_outside":going_out, "Drained_after_socializing":drain_social, "Friends_circle_size":friends, "Post_frequency":post_freq}])
	prediccion = isIntrovert.predict(x)
	if prediccion[0]:
		prediccion = "Introvert"
	else:
		prediccion = "Extrovert"

	#2.- guardar en bbdd
	predicciones_ref = db.collection('predicciones')
	document_data = {
            'date': firestore.SERVER_TIMESTAMP, 
            'result': prediccion,
            'data': str({"Time_spent_Alone":time_alone, "Stage_fear":fear, "Social_event_attendance":events, "Going_outside":going_out, "Drained_after_socializing":drain_social, "Friends_circle_size":friends, "Post_frequency":post_freq})
        }
	predicciones_ref.add(document_data)

	#3.- devolver
	return jsonify({
            "message": "Prediccion guardada exitosamente",
            "prediction": str(prediccion[0])
        }), 201

@app.route('/predictions', methods=['GET']) 
def devolver_predicciones():
	#1.- chequear bbdd
	predicciones_ref = db.collection('predicciones')
	docs = predicciones_ref.stream() 

	predictions_list = []
	for doc in docs:
		prediction_data = doc.to_dict()
		if 'date' in prediction_data and isinstance(prediction_data['date'], firestore.SERVER_TIMESTAMP.__class__):
			prediction_data['date'] = prediction_data['date'].isoformat()
		predictions_list.append(prediction_data)

	#2.- devolver todo
	return jsonify(predictions_list), 200

if __name__ == "__main__":
	app.run()
