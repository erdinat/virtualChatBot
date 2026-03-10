"""
🎓 Sanal Öğretmen Asistanı – Ana Uygulama

Python Programlama Eğitiminde RAG Destekli ve Adaptif Öğrenme Tabanlı
Sanal Öğretmen Asistanı.

Çalıştırmak için:
    streamlit run app.py
"""

import streamlit as st
from pathlib import Path


# ===== Sayfa Konfigürasyonu =====
st.set_page_config(
    page_title="Sanal Öğretmen Asistanı",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Oturum durum değişkenlerini başlatır."""
    defaults = {
        "messages": [],           # Sohbet geçmişi
        "rag_chain": None,        # RAG zinciri
        "vector_store": None,     # Vektör veritabanı
        "student_mastery": {},    # Öğrenci bilgi seviyeleri
        "current_topic": None,    # Mevcut konu
        "pdfs_loaded": False,     # PDF'ler yüklendi mi?
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar():
    """Yan panel: PDF yükleme ve öğrenci bilgi paneli."""
    with st.sidebar:
        st.header("🎓 Sanal Öğretmen Asistanı")
        st.caption("Python Programlama Eğitimi")

        st.divider()

        # --- PDF Yükleme ---
        st.subheader("📄 Ders Notu Yükleme")
        uploaded_files = st.file_uploader(
            "PDF ders notlarınızı yükleyin",
            type=["pdf"],
            accept_multiple_files=True,
            help="Eğitmen tarafından onaylanmış ders notları",
        )

        if uploaded_files:
            if st.button("📥 Ders Notlarını İşle", type="primary"):
                with st.spinner("Ders notları işleniyor..."):
                    process_uploaded_pdfs(uploaded_files)

        # --- Durum Bilgisi ---
        st.divider()
        if st.session_state.pdfs_loaded:
            st.success("✅ Ders notları yüklendi")
        else:
            st.info("⏳ Henüz ders notu yüklenmedi")

        # --- Bilgi Seviyesi ---
        if st.session_state.student_mastery:
            st.divider()
            st.subheader("📊 Bilgi Seviyeniz")
            for topic, score in st.session_state.student_mastery.items():
                st.progress(score, text=f"{topic}: {score:.0%}")


def process_uploaded_pdfs(uploaded_files):
    """Yüklenen PDF'leri işle ve vektör veritabanı oluştur."""
    # PDF'leri geçici dizine kaydet
    save_dir = Path("data/raw_pdfs")
    save_dir.mkdir(parents=True, exist_ok=True)

    for file in uploaded_files:
        file_path = save_dir / file.name
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        st.sidebar.write(f"  📄 {file.name}")

    try:
        from modules.rag import (
            load_all_pdfs,
            split_documents,
            get_embedding_model,
            create_vector_store,
            build_rag_chain,
        )

        # Pipeline: PDF → Chunks → Vectors → RAG Chain
        documents = load_all_pdfs(save_dir)
        chunks = split_documents(documents)
        embedding_model = get_embedding_model()
        vector_store = create_vector_store(chunks, embedding_model)

        st.session_state.vector_store = vector_store
        st.session_state.rag_chain = build_rag_chain(vector_store=vector_store)
        st.session_state.pdfs_loaded = True

        st.sidebar.success(f"✅ {len(uploaded_files)} PDF işlendi, {len(chunks)} parça oluşturuldu!")

    except Exception as e:
        st.sidebar.error(f"❌ Hata: {e}")


def render_chat():
    """Ana sohbet arayüzü."""
    st.title("🎓 Sanal Öğretmen Asistanı")
    st.caption("Python Programlama • Sokratik Yönlendirme • RAG Destekli")

    # Sohbet geçmişini göster
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Kullanıcı girişi
    if prompt := st.chat_input("Python ile ilgili sorunuzu sorun..."):
        # Kullanıcı mesajını ekle
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Asistan cevabı
        with st.chat_message("assistant"):
            if st.session_state.rag_chain is not None:
                with st.spinner("Düşünüyorum..."):
                    try:
                        from modules.rag import ask
                        result = ask(st.session_state.rag_chain, prompt)
                        response = result["answer"]
                    except Exception as e:
                        response = f"⚠️ Bir hata oluştu: {e}"
            else:
                response = (
                    "📚 Henüz ders notu yüklenmedi. "
                    "Lütfen sol panelden PDF ders notlarınızı yükleyin, "
                    "böylece size müfredata uygun cevaplar verebilirim."
                )

            st.markdown(response)
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )


def main():
    """Ana uygulama akışı."""
    init_session_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
