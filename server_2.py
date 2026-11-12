import os
import datetime
import json
import urllib.parse
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)

# Groq API Key
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE"))

notes_db = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant that can save notes, check time, create WhatsApp links, and search Google. Keep answers concise and helpful in Hindi or English as asked."},
                {"role": "user", "content": user_message}
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "save_note",
                        "description": "Save a note or task when user asks to remember or save something.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "note_content": {"type": "string", "description": "The text content of the note."}
                            },
                            "required": ["note_content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_time",
                        "description": "Get current local time.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "send_whatsapp",
                        "description": "Create a WhatsApp link when user asks to message someone.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "phone_number": {"type": "string", "description": "Phone number with country code (e.g. 919876543210)."},
                                "message": {"type": "string", "description": "The text message to send."}
                            },
                            "required": ["phone_number", "message"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_google",
                        "description": "Search Google when user asks to search or lookup something online.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search topic or query."}
                            },
                            "required": ["query"]
                        }
                    }
                }
            ],
            tool_choice="auto",
            max_tokens=400
        )

        response_message = completion.choices[0].message

        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "save_note":
                content = function_args.get("note_content")
                notes_db.append(content)
                ai_reply = f"मैंने आपका यह नोट सेव कर लिया है: '{content}'"

            elif function_name == "get_current_time":
                current_time = datetime.datetime.now().strftime("%I:%M %p")
                ai_reply = f"अभी समय हुआ है {current_time}"

            elif function_name == "send_whatsapp":
                phone = function_args.get("phone_number")
                msg = urllib.parse.quote(function_args.get("message"))
                wa_url = f"https://wa.me/{phone}?text={msg}"
                ai_reply = f"व्हाट्सएप मैसेज तैयार है: {wa_url}"

            elif function_name == "search_google":
                query = urllib.parse.quote(function_args.get("query"))
                search_url = f"https://www.google.com/search?q={query}"
                ai_reply = f"गूगल सर्च लिंक तैयार है: {search_url}"

            else:
                ai_reply = "माफ़ कीजिए, मैं यह काम नहीं कर सका।"
        else:
            ai_reply = response_message.content

        return jsonify({"reply": ai_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
