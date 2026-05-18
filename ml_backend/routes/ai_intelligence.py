from flask import Blueprint, request, jsonify
import os
import datetime
from groq import Groq
from database import chat_collection
from dotenv import load_dotenv

load_dotenv()

ai_bp = Blueprint('ai_intel', __name__)

# --- CONFIGURATION ---
# Yahan maine fallback laga diya hai agar .env load na ho raha ho toh
GROQ_KEY = os.getenv("GROQ_API_KEY") 

try:
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    print(f"FAILED TO INITIALIZE GROQ: {e}")

@ai_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    print("--- DEBUG: GROQ ROUTE HIT ---")
    try:
        data = request.get_json()
        user_email = data.get('email')
        user_msg = data.get('message')

        if not user_email or not user_msg:
            return jsonify({"error": "Email and Message are required"}), 400

        # Chat history fetch karo
        user_chat_doc = chat_collection.find_one({"user_email": user_email})
        past_messages = user_chat_doc.get('messages', [])[-5:] if user_chat_doc else []
        
        history = []
        for msg in past_messages:
            history.append({"role": "user", "content": msg['user']})
            history.append({"role": "assistant", "content": msg['ai']})
        
        history.append({"role": "user", "content": user_msg})

        # Model name wahi rakho jo curl mein list hua tha
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": "You are a professional Stock Market Assistant. Be concise."},
                *history
            ],
            temperature=0.7
        )
        
        ai_reply = completion.choices[0].message.content
        print(f"--- DEBUG: AI REPLY SUCCESSFUL ---")

        # Database save
        chat_collection.update_one(
            {"user_email": user_email},
            {
                "$push": {
                    "messages": {
                        "user": user_msg, 
                        "ai": ai_reply, 
                        "timestamp": datetime.datetime.utcnow()
                    }
                },
                "$set": {"last_active": datetime.datetime.utcnow()}
            },
            upsert=True
        )

        return jsonify({"reply": ai_reply}), 200

    except Exception as e:
        # Ye line terminal mein asli error dikhayegi
        print(f"--- DEBUG: GROQ ERROR -> {str(e)} ---")
        return jsonify({"error": str(e)}), 500

@ai_bp.route('/history/<email>', methods=['GET'])
def get_chat_history(email):
    try:
        chat_data = chat_collection.find_one({"user_email": email})
        return jsonify({"history": chat_data.get('messages', []) if chat_data else []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500