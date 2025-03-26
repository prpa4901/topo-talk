from clab-utility-tools.clabInfoCollector import ClabInfoCollector
import asyncio
import json
from chatbot import ChatBot
import streamlit as st



if __name__ == '__main__':
    st.title('Topology Talk')
    if st.session_state.get('conversation_history') is None:
        st.session_state['conversation_history'] = []
    
    st.write('This app will gather information about a CML2 topology')
    st.info('Please wait for the app to gather the information before asking questions')
    topo_file_name = st.text_input('Enter the name of the topology file')
    if st.topo_file_name:
        cic = ClabInfoCollector()
        cic.inspect_clab_topo(topo_file_name)
        cic.gather_startup_configs(topo_file_name)
        st.info('Topology information gathered')