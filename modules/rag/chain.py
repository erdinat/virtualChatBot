"""
RAG Pipeline – LLM Zinciri (Chain)

RAG bileşenlerini (Retriever + LLM + Prompt) birleştirip
uçtan uca bir soru-cevap pipeline'ı oluşturur.
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from config.settings import LLMConfig, RAGConfig
from modules.rag.embeddings import get_embedding_model, load_vector_store
from modules.rag.retriever import get_retriever


# ===== Sistem Prompt'u (Sokratik Yönlendirme Dahil) =====
SYSTEM_PROMPT = """Sen, bir üniversitede Python Programlama dersi veren deneyimli bir 
Sanal Öğretmen Asistanısın. Aşağıdaki kurallara MUTLAKA uymalısın:

## Temel Kurallar
1. **Sadece ders notlarını kullan:** Cevaplarını YALNIZCA aşağıda sana verilen ders notu 
   bağlamına (context) dayandır. Ders notlarında olmayan bilgi verme.
2. **Bilmiyorsan söyle:** Eğer soru ders notlarında yoksa, "Bu konu ders notlarımda yer 
   almıyor. Lütfen eğitmeninize danışın." de.
3. **Türkçe cevap ver:** Tüm cevaplarını Türkçe olarak ver.

## Sokratik Yönlendirme Kuralları
4. **Doğrudan kod verme:** Öğrenci bir kod sorusu sorduğunda, ASLA hemen tam kodu yazma.
5. **Adım adım yönlendir:** Önce düşündürücü bir soru sor veya bir ipucu ver.
   - Seviye 1: "Bu problemi çözmek için hangi veri tipini kullanırdın?"
   - Seviye 2: "for döngüsü burada işe yarar mı? Neden?"
   - Seviye 3: Kısmi kod örneği ver, eksik kısmı öğrenciye bırak.
6. **Öğrenci ısrar ederse:** 3. denemeden sonra tam çözümü gösterebilirsin, ama açıklama ekle.

## Hata Analizi
7. Öğrenci hatalı kod paylaşırsa:
   - Hatayı doğrudan söyleme, önce "Kodunun şu satırını tekrar incele" gibi yönlendir.
   - Sözdizimi hatası ise basit bir hatırlatma yap.
   - Mantık hatası ise "Çıkış koşulunu kontrol ettin mi?" gibi düşündürücü soru sor.

## Bağlam (Ders Notları)
{context}
"""


def get_llm(
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
    temperature: float = None,
) -> ChatOpenAI:
    """DeepSeek-V3 LLM istemcisini oluşturur (OpenAI uyumlu API)."""
    return ChatOpenAI(
        api_key=api_key or LLMConfig.API_KEY,
        base_url=base_url or LLMConfig.BASE_URL,
        model=model_name or LLMConfig.MODEL_NAME,
        temperature=temperature if temperature is not None else LLMConfig.TEMPERATURE,
        max_tokens=LLMConfig.MAX_TOKENS,
    )


def build_rag_chain(
    llm: Optional[ChatOpenAI] = None,
    vector_store=None,
):
    """
    RAG zincirini oluşturur: Retriever + LLM + Konuşma Belleği.
    Sokratik yönlendirme system prompt'a gömülüdür.
    """
    if llm is None:
        llm = get_llm()

    if vector_store is None:
        vector_store = load_vector_store()
        if vector_store is None:
            raise ValueError(
                "Vektör veritabanı bulunamadı. Önce PDF yükleyip veritabanını oluşturun."
            )

    retriever = get_retriever(vector_store)

    # Konuşma belleği – son 10 mesajı hatırlar
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
        k=10,
    )

    # Prompt şablonu
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template("{question}"),
    ])

    # Konuşmalı RAG zinciri
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=False,
    )

    return chain


def ask(chain, question: str) -> dict:
    """
    RAG zincirine soru sorar ve cevap + kaynakları döndürür.

    Returns:
        {
            "answer": str,
            "sources": List[Document],
        }
    """
    result = chain.invoke({"question": question})
    return {
        "answer": result.get("answer", ""),
        "sources": result.get("source_documents", []),
    }
