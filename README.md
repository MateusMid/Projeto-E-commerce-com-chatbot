COMO FAZER O PROJETO FUNCIONAR
================================

1. Instale o Python (python.org/downloads), se ainda não tiver.
   No instalador do Windows, marque "Add python.exe to PATH".

2. Extraia a pasta do projeto

3. Abra o terminal dentro da pasta do projeto.

4. Instale as dependências:
   pip install -r requirements.txt

5. Crie o arquivo .env a partir do modelo:
   Windows: copy .env.example .env
   Mac/Linux: cp .env.example .env

6. Consiga sua chave gratuita do Gemini:
   - Acesse aistudio.google.com/apikey
   - Faça login com uma conta Google
   - Clique em "Create API key"
   - Copie a chave gerada (começa com "AIza")

7. Abra o arquivo .env com o Bloco de Notas e cole a chave assim:
   GEMINI_API_KEY=sua-chave-aqui

   Salve e feche.

8. Rode o servidor:
   python app.py

9. Abra o navegador em:
   http://localhost:3000

Pronto, o site e o chatbot vão estar funcionando.


