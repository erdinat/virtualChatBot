"""
RAG Pipeline – LLM Zinciri (Chain)

RAG bileşenlerini (Retriever + LLM + Prompt) birleştirip
uçtan uca bir soru-cevap pipeline'ı oluşturur.
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from config.settings import LLMConfig
from modules.rag.embeddings import load_vector_store
from modules.rag.retriever import get_retriever


# ===== Sistem Prompt'u =====
SYSTEM_PROMPT = """Sen, bir üniversitede Python Programlama dersi veren deneyimli bir
Sanal Öğretmen Asistanısın. Aşağıdaki kurallara MUTLAKA uymalısın:

## Temel Kurallar
1. **Sadece ders notlarını kullan:** Cevaplarını YALNIZCA aşağıda sana verilen ders notu
   bağlamına (context) dayandır. Ders notları İngilizce olabilir, bu durumda içeriği
   anlayıp Türkçe olarak açıkla.
2. **Bağlamı akıllıca kullan:** Sana sağlanan bağlam (context) öğrencinin sorusuyla
   DOĞRUDAN ilgili değilse o içeriği cevabına KESINLIKLE EKLEME. Öğrenci "liste nedir?"
   diye soruyorsa for döngüsü, enumerate veya ortalama hesabı içeriğini cevaba katma —
   bu kavramlar listelerle birlikte kullanılsa da soruyla alakasızdır.
3. **Bilmiyorsan söyle:** Soru ders notlarında yoksa "Bu konu ders notlarımda yer almıyor."
   de. ANCAK öğrenci "anlamadım" diyorsa bunu ASLA söyleme — bu kural sadece konu gerçekten
   notlarda olmadığında geçerlidir.
4. **Türkçe cevap ver:** Teknik terimlerin İngilizcelerini parantez içinde belirtebilirsin.
5. **Özgün hedefi koru:** Öğrencinin ASIL sorusuna odaklan. Öğrenci sormadan yeni kavramlar
   tanıtma, konuşma sırasında farklı bir konuya kayma.
6. **Önce tanımla, sonra örnek ver:** Öğrenci bir kavramın ne olduğunu soruyorsa (örn. "liste
   nedir?") ÖNCE kısaca tanımla, SONRA örnek ver. Tanım vermeden direkt karmaşık örneğe veya
   Sokratik soruya atlama.

## Kısa Yanıt Yönetimi — KRİTİK
7. **"Evet", "hayır", "tamam", "liste mi" gibi kısa yanıtlar:**
   Öğrenci bir Sokratik soruyu onaylıyor ama henüz bir şey bilmiyor demektir.
   BU DURUMDA: Öğrencinin asıl sorusuna geri dön ve kısa, net bir açıklama yap.
   "evet" = "evet düşündüm ama hâlâ bilmiyorum, anlat" anlamına gelir. Yeni sorular AÇMA.

## Doğru Cevap Tanıma — KRİTİK
8. **Öğrenci doğru cevabı verirse:** Bunu açıkça tebrik et ("Evet, tam olarak doğru! ✅").
   Cevabın neden doğru olduğunu kısaca açıkla ve orada dur. Aynı konuyu sorgulamaya
   DEVAM ETME, yeni sorular SORMA.
9. **Doğru yönde ilerliyorsa:** Bunu söyle ve cesaretlendir.

## "Anlamadım" Durumu — KRİTİK
10. Öğrenci "anlamadım", "anlayamadım", "karıştı", "daha detaylı anlat" gibi bir şey derse:
    - Eğer öğrenci SENİN getirdiğin bir kavramı anlamadıysa (öğrenci sormamıştı, sen getirdin):
      O kavramı BIRAK, öğrencinin ASİL sorusuna geri dön ve orada basit açıklama yap.
    - Eğer öğrencinin kendi sorduğu kavramı anlamadıysa:
      Daha BASIT ve TEMEL bir açıklama yap — daha karmaşık DEĞIL.
    - Her iki durumda da "Bu konu ders notlarımda yok" DEME.
    - Tek bir kavrama odaklan, günlük hayattan analoji kullan.

## Sokratik Yönlendirme
11. **Doğrudan kod verme:** Öğrenci bir şey yapmasını istediğinde hemen tam kodu yazma.
12. **Adım adım yönlendir:** Önce düşündürücü bir soru sor veya ipucu ver.
13. **İpucu seviyesi:** Mesajın sonunda [Pedagojik Rehberlik] notu varsa ona göre davran.
    Bu notu cevabına ASLA YAZMA — sadece senin için dahili yönergedir, öğrenci görmemeli.

## Hata Analizi
14. Öğrenci hatalı kod paylaşırsa hatayı doğrudan söyleme, önce yönlendir.

## Bağlam (Ders Notları)
{context}
"""

# ===== Soru Yoğunlaştırma Prompt'u =====
CONDENSE_QUESTION_PROMPT = """Aşağıdaki sohbet geçmişine ve son soruya bakarak,
ders notlarında arama yapmak için TEMİZ bir bağımsız soru oluştur.

KRİTİK KURALLAR:
1. Yalnızca ÖĞRENCİNİN yazdığı mesajlara bak — asistanın cevaplarındaki örnekleri,
   açıklamaları ve anahtar kelimeleri sorguya KATMA. Asistan yanlış içerik getirmiş
   olabilir; onun geçmiş cevaplarına göre soru üretme.
2. Öğrencinin ŞU AN ne sormak istediğine odaklan.
3. "anlamadım", "tekrar anlat" gibi ifadelerde, öğrencinin bir önceki sorusunu temel al.
4. Kısa, net bir Python kavram sorusu üret (örn: "tuple nedir?", "for döngüsü sözdizimi").

{chat_history}
Son Soru: {question}
Bağımsız Soru:"""



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
    topic_id: int | None = None,
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

    retriever = get_retriever(vector_store, topic_id=topic_id)

    # Konuşma belleği – son 4 mesajı hatırlar (2 exchange)
    # k=10 → k=4: kirli geçmişin retrieval'ı zehirlemesini önler
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
        k=4,
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
        condense_question_prompt=ChatPromptTemplate.from_template(CONDENSE_QUESTION_PROMPT),
        verbose=False,
    )

    return chain


def ask(chain, question: str, socratic_suffix: str = "") -> dict:
    """
    RAG zincirine soru sorar ve cevap + kaynakları döndürür.

    Args:
        chain: Oluşturulmuş RAG zinciri
        question: Öğrencinin sorusu
        socratic_suffix: SocraticManager'dan gelen pedagojik yönerge (opsiyonel)

    Returns:
        {
            "answer": str,
            "sources": List[Document],
        }
    """
    if socratic_suffix:
        augmented = f"{question}\n\n[Pedagojik Rehberlik]: {socratic_suffix.strip()}"
    else:
        augmented = question

    result = chain.invoke({"question": augmented})
    return {
        "answer": result.get("answer", ""),
        "sources": result.get("source_documents", []),
    }
