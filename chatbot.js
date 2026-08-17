// chatbot.js
// Frontend for the S.G Acessórios chat widget.
// Talks to the local backend (server.js) at /api/chat, which does the RAG
// retrieval over products.json and calls the LLM. No API keys live here.
(function () {
  "use strict";

  var API_URL = "/api/chat"; // same-origin: works when server.js serves this page

  var launcher = document.getElementById("chatLauncher");
  var win = document.getElementById("chatWindow");
  var closeBtn = document.getElementById("chatClose");
  var body = document.getElementById("chatBody");
  var form = document.getElementById("chatForm");
  var input = document.getElementById("chatInput");
  var sendBtn = document.getElementById("chatSend");

  if (!launcher || !win || !form) return; // widget not on this page

  var history = []; // [{role: 'user'|'assistant', content: '...'}]
  var isOpen = false;
  var isSending = false;

  var GREETING =
    "Olá! ✦ Sou o assistente da S.G Acessórios. Me pergunte sobre um colar ou pulseira " +
    "(preço, material, descrição ou se tem em estoque) que eu te ajudo!";

  function open() {
    isOpen = true;
    win.classList.add("open");
    win.setAttribute("aria-hidden", "false");
    if (body.children.length === 0) {
      addMessage("bot", GREETING);
    }
    input.focus();
  }

  function close() {
    isOpen = false;
    win.classList.remove("open");
    win.setAttribute("aria-hidden", "true");
  }

  launcher.addEventListener("click", function () {
    isOpen ? close() : open();
  });
  closeBtn.addEventListener("click", close);

  function addMessage(role, text) {
    var el = document.createElement("div");
    el.className = "chat-msg chat-msg--" + role;
    el.textContent = text;
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
    return el;
  }

  function showTyping() {
    var el = document.createElement("div");
    el.className = "chat-typing";
    el.id = "chatTyping";
    el.innerHTML = "<span></span><span></span><span></span>";
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  }

  function hideTyping() {
    var el = document.getElementById("chatTyping");
    if (el) el.remove();
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text || isSending) return;

    addMessage("user", text);
    history.push({ role: "user", content: text });
    input.value = "";
    setSending(true);
    showTyping();

    fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history })
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw new Error(data.error || "Erro desconhecido");
          return data;
        });
      })
      .then(function (data) {
        hideTyping();
        addMessage("bot", data.reply);
        history.push({ role: "assistant", content: data.reply });
      })
      .catch(function (err) {
        hideTyping();
        addMessage(
          "error",
          "Não consegui falar com o assistente agora (" +
            err.message +
            "). Tente novamente ou fale com a gente pelo WhatsApp."
        );
      })
      .finally(function () {
        setSending(false);
        input.focus();
      });
  });

  function setSending(state) {
    isSending = state;
    sendBtn.disabled = state;
  }
})();
