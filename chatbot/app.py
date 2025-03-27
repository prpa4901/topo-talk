from langchain_ollama.embeddings import OllamaEmbeddings
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
import uuid
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import JSONLoader, DirectoryLoader
from langchain_experimental.text_splitter import SemanticChunker
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv
import os
from langchain.retrievers.multi_query import MultiQueryRetriever

load_dotenv()

OLLAMA_LLM_URL = os.getenv("BASE_LLM_URL")

prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are an expertise in computer networking and internet with immense experience,"\
    "there might a chat history as well present here in case,"\
    "you are an excellent troubleshooter and design expert in "\
    "the field of computer networking and internet. You can analyze any device topology having Cisco, Arista and other vendors "\
    "Use the retrieved context to answer the question in a detailed manner."\
    "\n Context: {context}"),
    MessagesPlaceholder("chat_history"),
    ("human","Question: {input}")
])

contextualize_q_system_prompt = (
    "A chat history may or may not be present but given the the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


class ChatBot:

    """
    ChatBot class
    """

    def __init__(self):

        self.embeddings = OllamaEmbeddings(model="llama3",base_url=OLLAMA_LLM_URL)
        self.text_splitter = SemanticChunker(self.embeddings,
                                             breakpoint_threshold_type='percentile',
                                             breakpoint_threshold_amount=95.0,
                                             add_start_index=True,
                                             buffer_size=3
                                             )
        self.file_loader = None
        self.llm = OllamaLLM(model="mistral",
                             base_url=OLLAMA_LLM_URL,
                             temperature=0.05,  # Lower for factual accuracy
                             repeat_penalty=1.2,
                             num_ctx=8192,  # Larger context window
                             top_k=40,
                             )
        self.conversation_history = []
        self.page_docs = []
        self.chunks = []
        self.workflow = StateGraph(state_schema=MessagesState)
        self.initialize_loader()
        self.vector_store = None
        self.memory = MemorySaver()
        self.rag_chain = None
        self.app_memory = None


    def initialize_loader(self):
        """
        Initialize the document loader
        """
        self.repo_dir = os.getcwd()
        self.file_loader = DirectoryLoader(
            f"{self.repo_dir}/topology_data/",
            show_progress=True,
            loader_cls=JSONLoader,
            loader_kwargs={
                'text_content': False,
                'jq_schema': '.[]'
            }
        )

    def load_file(self):
        """
        Load the file from the given path
        """
        self.page_docs = self.file_loader.load_and_split()

    def split_text_chunks(self):
        """
        Split the text into semantic chunks
        """
        self.chunks = self.text_splitter.split_documents(self.page_docs)

    def store_in_chroma(self):
        """
        Store the chunks in the Chroma vector store
        """
        try:
            self.vector_store = Chroma.from_documents(self.chunks,
                                                      embedding=self.embeddings,
                                                      persist_directory="vectorstore_db/")
        except Exception as e:
            print(f"Error: {e}")

    def create_conversational_chain(self):
        """Create the Conversational Retrieval Chain."""

        retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 100,  # Increased from default to get more context  # Only return relevant results
                "fetch_k": 200,
                "lambda_mult": 0.7,
                "score_threshold": 0.78
            }
        )

        retriever = MultiQueryRetriever.from_llm(
            retriever=retriever,
            llm=self.llm,
            include_original=True
            )

        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            retriever,
            contextualize_q_prompt
        )
        question_answer_chain = create_stuff_documents_chain(
            self.llm,
            prompt_template
        )

        self.rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )


    async def call_retrieval_node(self, state: MessagesState):
        """
        Call the retrieval node
        """
        print(state["messages"])
        user_query = state["messages"][-1].content
        chat_history = state["messages"][:-1]

        response = await self.rag_chain.ainvoke({
            "input": user_query,
            "chat_history": chat_history,
        })
        print(response)
        state["messages"].append(SystemMessage(response["answer"]))
        return state

    def setup_graph(self):
        """
        Setup the graph
        """
        self.workflow.add_edge(START, "retrieval_node")
        self.workflow.add_node("retrieval_node", self.call_retrieval_node)
        self.app_memory = self.workflow.compile(checkpointer=self.memory)

    def setup_graph_async(self):
        """
        Setup the graph asynchronously
        """
        self.load_file()
        self.split_text_chunks()
        self.store_in_chroma()
        self.create_conversational_chain()
        # Ensure workflow is initialized
        if not hasattr(self, 'workflow') or self.workflow is None:
            self.workflow = StateGraph(state_schema=MessagesState)
            
        # Add node and edge
        self.workflow.add_edge(START, "retrieval_node")
        self.workflow.add_node("retrieval_node", self.call_retrieval_node)
        
        # Compile and return
        self.app_memory = self.workflow.compile(checkpointer=self.memory)
        print(f"Async graph setup complete, app_memory: {self.app_memory}")
        return self.app_memory