# app.py
# Backend em Python (Flask) do chatbot da S.G Acessórios.
#
# Por que um backend? O chatbot precisa chamar uma LLM (Gemini), e a chave de
# API nunca pode ficar exposta no JavaScript do navegador — qualquer pessoa
# abriria o DevTools, copiaria a chave e geraria custos na sua conta. Este
# servidor guarda a chave em segredo, faz a busca RAG no catálogo e é o
# único lugar que fala com a LLM.
#
# Como rodar:
#   1. pip install -r requirements.txt
#   2. copie .env.example para .env e adicione sua GEMINI_API_KEY
#   3. python app.py
#   4. abra http://localhost:3000

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types

from retrieval import format_context, retrieve

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("CHAT_MODEL", "gemini-flash-latest")
PORT = int(os.environ.get("PORT", 3000))

# Cliente do Gemini. Só é criado se a chave existir; caso contrário o
# /api/chat responde com um erro explicando o que falta configurar.
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_PROMPT_BASE = """Você é o assistente virtual da S.G Acessórios, uma loja de joias e acessórios femininos (colares e pulseiras).

Regras:
- Responda SOMENTE com base nas informações de produtos fornecidas abaixo no bloco "Catálogo relevante". Nunca invente preço, material, descrição ou estoque.
- Se o cliente perguntar por um item que não aparece no catálogo relevante, diga educadamente que não encontrou esse item e sugira dar mais detalhes ou ver a coleção no site.
- Sempre que falar de um produto, inclua: descrição breve, preço (em R$), do que é feito, e se está em estoque ou esgotado.
- Seja breve, simpática e use um tom acolhedor, coerente com uma loja de acessórios delicados.
- Responda em português do Brasil."""


@app.route("/")
def home():
    # Serve o site (index.html + o widget de chat embutido nele).
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    if not GEMINI_API_KEY or client is None:
        return jsonify({
            "error": "GEMINI_API_KEY não configurada no servidor. Copie .env.example para .env e adicione sua chave."
        }), 500

    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({"error": "Envie 'messages' (array) no corpo da requisição."}), 400

    last_user_message = next(
        (m for m in reversed(messages) if m.get("role") == "user"), None
    )
    query = last_user_message.get("content", "") if last_user_message else ""

    # ---- Etapa de retrieval (RAG): busca produtos relevantes para a pergunta ----
    relevant_products = retrieve(query, top_k=3)
    context = format_context(relevant_products)

    system_prompt = f"{SYSTEM_PROMPT_BASE}\n\nCatálogo relevante para a pergunta atual:\n{context}"

    # ---- Etapa de geração: pede pro Gemini responder só com base nesse contexto ----
    try:
        reply = call_gemini(system_prompt, messages)
    except Exception as exc:  # noqa: BLE001 - queremos capturar qualquer erro da API
        app.logger.error("Erro ao chamar o Gemini: %s", exc)
        return jsonify({"error": "Erro ao consultar o assistente. Tente novamente em instantes."}), 500

    return jsonify({
        "reply": reply,
        "sources": [p["id"] for p in relevant_products],
    })


def call_gemini(system_prompt, conversation):
    """Chama a API do Gemini com o histórico da conversa e o contexto do RAG.

    O SDK do Gemini usa o papel "model" em vez de "assistant" para as
    respostas da IA, então convertemos o histórico antes de enviar.
    """
    contents = []
    for msg in conversation:
        role = "model" if msg.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        ),
    )
    return response.text.strip()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
