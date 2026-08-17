# Chatbot RAG — S.G Acessórios (versão Python + Gemini)

Assistente virtual integrado ao site que responde perguntas sobre os produtos
(descrição, preço, material e estoque) usando um esquema simples de **RAG**
(Retrieval-Augmented Generation): busca no catálogo → monta um contexto →
envia pra LLM (Gemini) responder só com base nesse contexto.

Esta é a versão em **Python (Flask)** do projeto — o site original era em
Node/Express e usava a OpenAI; aqui o backend foi reescrito em Python e a LLM
trocada para o **Gemini** (Google), mantendo o mesmo comportamento.

## Como funciona

```
Cliente digita no chat
        │
        ▼
chatbot.js (frontend)  ──POST /api/chat──▶  app.py (backend Flask)
                                                   │
                                     1) retrieval.py busca no
                                        products.json os produtos
                                        que combinam com a pergunta
                                                   │
                                     2) monta um "contexto" só com
                                        esses produtos (preço,
                                        descrição, material, estoque)
                                                   │
                                     3) chama o Gemini com:
                                        - instruções fixas do sistema
                                        - o contexto retirado do RAG
                                        - a pergunta do cliente
                                                   │
                                     4) devolve a resposta pro chat
```

Por que precisa de um backend (`app.py`) e não dá pra chamar a LLM direto do
navegador? Porque isso exigiria colocar sua chave de API dentro do
JavaScript do site — qualquer pessoa poderia abrir o DevTools, copiar a
chave e usar sua conta. O servidor mantém a chave em segredo (arquivo
`.env`, que nunca vai pro navegador nem pro Git).

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | O site + o widget do chat (botão flutuante + janela) — não mudou |
| `chatbot.js` | JS do widget: manda a pergunta do cliente pro backend e mostra a resposta — não mudou |
| `app.py` | Backend Python/Flask: recebe a pergunta, faz a busca (RAG) e chama o Gemini |
| `retrieval.py` | A parte "R" do RAG: busca por palavras-chave no catálogo |
| `products.json` | Seu catálogo — a "base de conhecimento" do RAG. **Edite este arquivo** para adicionar/remover produtos ou atualizar estoque e preço |
| `.env.example` | Modelo do arquivo de variáveis de ambiente |
| `requirements.txt` | Dependências Python do backend |

## Como rodar localmente

1. Tenha o [Python 3.9+](https://www.python.org/) instalado.
2. No terminal, dentro da pasta do projeto, crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
5. Abra o `.env` e cole sua chave do Gemini:
   ```
   GEMINI_API_KEY=sua-chave-aqui
   ```
   (Crie uma chave gratuita em https://aistudio.google.com/apikey)
6. Inicie o servidor:
   ```bash
   python app.py
   ```
7. Abra **http://localhost:3000** no navegador (não abra o `index.html`
   direto/duplo-clique — o chat só funciona servido pelo `app.py`, porque
   ele chama `/api/chat` no mesmo endereço).

## Atualizando o catálogo

Edite `products.json`. Cada produto tem:

```json
{
  "id": "colar-elo-dourado",
  "name": "Colar Elo Dourado",
  "category": "Colar",
  "price": 20.00,
  "description": "...",
  "material": "...",
  "stock": 14,
  "keywords": ["colar", "dourado", "cartier"]
}
```

- `stock`: quantidade em estoque. Use `0` para "esgotado".
- `keywords`: sinônimos que ajudam a busca a encontrar o produto (opcional,
  mas melhora a precisão).

Não precisa mexer em `retrieval.py` nem em `app.py` para isso — o chatbot lê
o `products.json` a cada pergunta.

## Trocando o modelo do Gemini

Por padrão o `.env.example` usa `CHAT_MODEL=gemini-flash-latest` (aponta
sempre para o Flash mais atual). Se quiser fixar uma versão específica,
troque essa variável no seu `.env` (ex.: `gemini-2.5-flash`) — veja os
modelos disponíveis em https://ai.google.dev/gemini-api/docs/models.

## Colocando no ar (hospedagem)

Isso não é mais um site 100% estático — agora ele precisa de um processo
Python rodando. Opções simples:
- **Render** ou **Railway**: conectam direto no seu repositório Git, rodam
  `pip install -r requirements.txt` e `python app.py` (ou `gunicorn app:app`
  em produção) e cuidam do HTTPS.
- **PythonAnywhere**: hospedagem simples focada em Flask/Django.

Em qualquer uma delas, configure `GEMINI_API_KEY` nas variáveis de ambiente
do painel do serviço (nunca deixe a chave dentro do código). Para produção,
troque `debug=True` por `debug=False` em `app.py` e considere rodar com
`gunicorn` em vez do servidor de desenvolvimento do Flask.
