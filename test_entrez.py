import sys
sys.path.append("d:/py_life")
from db.ncbi_fetch import NCBIFetcher

import streamlit as st
st.session_state['ncbi_email'] = "test@example.com"
st.session_state['ncbi_api_key'] = ""

head, seq = NCBIFetcher.fetch_fasta("JN005831")
print("HEAD:", head)
print("SEQ:", seq)
from algo.sequence_analysis import validate_sequence
print("VALID?", validate_sequence(seq.replace(" ", "").replace("\n", "").replace("\r", "")))
