# topo-talk


Setting up debian server for SSH so that Ubuntu VM can access
sudo apt update && sudo apt install openssh-server -y

# 🚀 Containerlab RAG-Powered Network Chatbot

## 📌 Overview
This project is a **RAG-based network topology chatbot** that:
- 🖥️ **Analyzes network topologies from Containerlab.**
- 📱 **Retrieves startup configs over SSH using Paramiko.**
- 📂 **Uses ChromaDB for vector-based retrieval.**
- 🧠 **Generates topology-aware answers using Mistral LLM.**

💡 **Use Case:**  
Provides insights into network **device connectivity, routing, and configurations** from startup configs of **Cisco, Arista, and other vendors**.

---

## ⚙️ **How It Works**
### 🧐 **Step-by-Step Process**
1️⃣ **User Inputs Containerlab File:**  
   - Provide the topology file (`.yaml`) via the Streamlit UI.  

2️⃣ **Topology Data Collection:**  
   - Uses **Paramiko SSH** to fetch startup configurations from network devices.  
   - Data is stored in JSON format.

3️⃣ **Vector Storage (ChromaDB):**  
   - Splits configs into **semantic chunks** using `SemanticChunker`.  
   - Stores them as embeddings for retrieval.  

4️⃣ **Retrieval-Augmented Generation (RAG):**  
   - **MultiQueryRetriever** generates alternative queries.  
   - Uses **MMR (Maximal Marginal Relevance)** to fetch diverse but relevant context.  

5️⃣ **LLM Query Processing:**  
   - **Ollama's Mistral model** processes topology-related queries.  
   - Responses are structured with network-specific insights.  

---

## 🚀 **Quick Start Guide**
### ⚖️ **1. Install Dependencies**
```sh
pip install -r requirements.txt
```

### 🏢 **2. Set Up Ollama LLM**
```sh
ollama serve
```

### 💾 **3. Run the Chatbot**
```sh
streamlit run app.py
```

---

## ⚙️ **Configuration**
The chatbot retrieves settings from `.env`.  
Create a `.env` file with:
```ini
BASE_LLM_URL=http://localhost:11434
```

Modify model settings via the **Streamlit sidebar UI**:
- **Temperature**: Adjusts response accuracy vs. creativity.
- **MMR Retrieval Settings**: Tuned for **balanced context relevance**.

---
---

## 🛠 **Troubleshooting & Debugging**
### ⚠️ **1. Event Loop Closed Error**
**Issue:**  
`RuntimeError: Event loop is closed`  
**Fix:**  
Ensure **one persistent event loop**:
```python
if 'loop' not in st.session_state:
    st.session_state['loop'] = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state['loop'])
```

---

### ⚠️ **2. VectorDB Not Found**
**Issue:**  
`ChromaDB: No database found at vectorstore_db/`  
**Fix:**  
- Ensure `topology_data/` contains valid JSON files.
- Rebuild the vectorstore:
```python
chatbot.store_in_chroma()
```

---

### ⚠️ **3. LLM Not Responding**
**Issue:**  
LLM fails to process queries.  
**Fix:**  
- Check if **Ollama is running**:
  ```sh
  ollama serve
  ```
- Verify `.env` has the **correct BASE_LLM_URL**.

---

## 🏆 **Key Features**
✅ **Supports Cisco, Arista, and Other Vendors**  
✅ **Uses MMR + MultiQuery Retrieval for Better Accuracy**  
✅ **Persistent Chat Memory** (Streamlit session state)  
✅ **Dynamic LLM Temperature Control**  

---

## 🎯 **Future Improvements**
🔹 **Deploy to Cloud (GCP/AWS)**  
🔹 **Support More Network Vendors (Juniper, Palo Alto)**  
🔹 **Optimize Retrieval Speed (FAISS for Faster Queries)**  

---

## 📈 **Credits & Contributors**
- Developed by **[Your Name]**  
- **Special Thanks** to OpenAI, LangChain, and Containerlab teams  

---

🔹 **Feel free to fork & contribute!** 🚀

