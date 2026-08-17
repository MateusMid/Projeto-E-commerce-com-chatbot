# retrieval.py
# Recuperação simples por palavras-chave (o "R" do RAG) sobre o catálogo de
# produtos. Não usa embeddings nem serviços externos — funciona bem para um
# catálogo pequeno como este. Se o catálogo crescer muito, troque por busca
# vetorial (embeddings + similaridade de cosseno), mas mantenha a mesma
# assinatura de função para não precisar mexer no app.py.

import json
import os
import re
import unicodedata

PRODUCTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")


def load_products():
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text):
    """Remove acentos para que 'coração' combine com 'coracao', 'é' com 'e' etc."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text):
    return [t for t in normalize(text).split(" ") if t]


def product_haystack(product):
    """Monta uma grande string pesquisável a partir de todos os campos do produto."""
    parts = [
        product.get("name", ""),
        product.get("category", ""),
        product.get("description", ""),
        product.get("material", ""),
        *(product.get("keywords") or []),
    ]
    return normalize(" ".join(parts))


def retrieve(query, top_k=3):
    """Recupera os produtos mais relevantes para a pergunta do cliente.

    Args:
        query: mensagem crua do usuário.
        top_k: número máximo de produtos a retornar.
    Returns:
        Lista de produtos (dicts), do mais relevante para o menos relevante.
    """
    products = load_products()
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scored = []
    for product in products:
        haystack = product_haystack(product)
        name_tokens = tokenize(product.get("name", ""))
        category_tokens = tokenize(product.get("category", ""))

        score = 0
        for token in query_tokens:
            if len(token) < 3:
                continue  # ignora palavras muito curtas/comuns
            if token in haystack:
                score += 1
            if token in name_tokens:
                score += 3  # sinal forte: bate com o nome do produto
            if token in category_tokens:
                score += 2  # bate com a categoria (colar/pulseira)
        scored.append((product, score))

    relevant = [item for item in scored if item[1] > 0]
    relevant.sort(key=lambda item: item[1], reverse=True)
    return [product for product, _score in relevant[:top_k]]


def format_context(products):
    """Formata os produtos recuperados num bloco de texto compacto para a LLM."""
    if not products:
        return "Nenhum produto do catálogo corresponde à busca do cliente."

    blocks = []
    for p in products:
        stock = p.get("stock", 0)
        stock_text = f"{stock} unidade(s) em estoque" if stock > 0 else "no momento sem estoque (esgotado)"
        price_text = f"{p['price']:.2f}".replace(".", ",")
        blocks.append(
            f"- Nome: {p['name']}\n"
            f"  Categoria: {p['category']}\n"
            f"  Preço: R$ {price_text}\n"
            f"  Descrição: {p['description']}\n"
            f"  Material: {p['material']}\n"
            f"  Estoque: {stock_text}"
        )
    return "\n\n".join(blocks)
