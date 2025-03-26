from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
import uuid
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from IPython.display import Image, display
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import JSONLoader, DirectoryLoader
from langchain_experimental.text_splitter import SemanticChunker
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_ollama import OllamaLLM


prompt_template = ChatPromptTemplate.from_messages([
    ("system",
    "You are an expertise in computer networking and internet with immense experience,"\
    "there might a chat history as well present here in case,"\
    "you are an excellent troubleshooter and design expert in "\
    "the field of computer networking and internet. "\
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
        self.embeddings = OllamaEmbeddings(model="llama3",)
        self.text_splitter = SemanticChunker(self.embeddings,
                                             breakpoint_threshold_type='percentile')
        self.file_loader = None
        self.llm = OllamaLLM(model="mistral",
                             temperature=0.5,
                             base_url="http://localhost:11434")
        self.conversation_history = []
        self.vector_store = None
        self.page_docs = []
        self.chunks = []
        self.workflow = StateGraph(state_schema=MessagesState)
        self.initialize_loader()
        self.memory = MemorySaver()
        self.setup_graph()


    def initialize_loader(self):
        """
        Initialize the document loader
        """
        self.file_loader = DirectoryLoader(
            "topology_data",
            show_progress=True,
            loader_cls=JSONLoader,
            loader_kwargs={
                'text_content': False,
                'jq_schema': '.[]'
            }
        )

    def load_file(self, file_path):
        """
        Load the file from the given path
        """
        self.page_docs = self.file_loader.load_and_split(file_path)

    def split_text_chunks(self):
        """
        Split the text into semantic chunks
        """
        self.chunks = self.text_splitter.split_documents(self.page_docs)

    def store_in_chroma(self):
        """
        Store the chunks in the Chroma vector store
        """
        self.vector_store = Chroma.from_documents(self.chunks, embedding=self.embeddings)
        self.vector_store.persist()

    def create_conversational_chain(self):
        """Create the Conversational Retrieval Chain."""

        retriever = self.vector_store.as_retriever()
        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            retriever,
            contextualize_q_prompt
        )
        question_answer_chain = create_stuff_documents_chain(
            self.llm,
            prompt_template
        )

        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )

        return rag_chain

    def call_retrieval_node(self, chain, state: MessagesState):
        """
        Call the retrieval node
        """
        user_query = state.messages[-1].text
        chat_history = state.messages[:-1]

        response = chain.invoke({
            "input": user_query,
            "chat_history": chat_history,
        })
        state.messages.append(response["answer"])
        return state

    def setup_graph(self):
        """
        Setup the graph
        """
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", self.call_retrieval_node)
        self.app_memory = self.workflow.compile(checkpointer=self.memory)

