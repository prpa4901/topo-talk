import uuid
import asyncio
import json
from langchain_core.messages import HumanMessage
from clab_utility_tools.clabInfoCollector import ClabInfoCollector
from chatbot.app import ChatBot
import streamlit as st
import os


def gather_topology_information(topo_file):
    cic = ClabInfoCollector()
    curr_working_dir = os.getcwd()
    cic.save_gather_info(topo_file, curr_working_dir)
    return True

async def get_llm_response(bot, message, config):
    input_message = HumanMessage(content=message)
    response = ""
    # print(bot)
    if bot.app_memory is None:
        bot.setup_graph_async()
    async for event in bot.app_memory.astream({"messages": [input_message]}, config, stream_mode="values"):
        response = event
    return response


if __name__ == '__main__':
    st.title('Topology Talk')
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatBot()

    if 'loop' not in st.session_state:
        st.session_state['loop'] = asyncio.new_event_loop()
        asyncio.set_event_loop(st.session_state['loop'])

    if st.session_state.get('conversation_history') is None:
        st.session_state['conversation_history'] = []

    if st.session_state.get('thread_id') is None:
        st.session_state['thread_id'] = str(uuid.uuid4())
        st.session_state['config'] = {"configurable": {"thread_id": st.session_state['thread_id']}}
    with st.sidebar:
        st.write('This app will gather information about a CML2 topology')
        st.info('Please wait for the app to gather the information before asking questions')
        topo_file_name = st.text_input('Enter the name of the topology file')
        if topo_file_name:
            if 'cic' not in st.session_state:
                with st.spinner('Gathering information'):
                    st.text("Please wait while the app gathers information")
                    st.session_state['cic'] = gather_topology_information(topo_file_name)
                    if st.session_state.get('cic'):
                         st.session_state.chatbot.setup_graph_async()
                st.success('Information gathered successfully')
            st.write('You can now ask questions about the topology')
        else:
            st.warning('Please enter the name of the topology file')
        st.write("### Model Settings")
        temperature = st.slider("Temperature (lower = more accurate)", 
                               min_value=0.0, max_value=1.0, value=0.1, step=0.1)
        if temperature !=  st.session_state.chatbot.llm.temperature:
            st.session_state.chatbot.llm.temperature = temperature
            st.info(f"Temperature set to {temperature}")
        
    if st.session_state.get('cic'):
        for message in st.session_state.get('conversation_history', []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        question = st.chat_input('Ask a question on this topology')
        if question:
            st.chat_message("user").markdown(question)
            st.session_state['conversation_history'].append({"role": "user", "content": question})
            with st.spinner("Fetching response from model..."):
                bot_message = st.session_state['loop'].run_until_complete(get_llm_response(st.session_state.chatbot,
                                                                                           question,
                                                                                           st.session_state['config']))
                response = bot_message["messages"][-1].content
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.session_state['conversation_history'].append({"role": "assistant", "content": response})

    