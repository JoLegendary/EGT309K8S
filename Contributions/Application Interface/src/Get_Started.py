import streamlit as st

st.set_page_config(
    page_title="Get Started",
    page_icon="",
)

st.write("# Welcome to Pipeline Desinger!")

st.markdown(
    r"""
    This is the pipeline designer meant to demostrate the GUI of how an completed application built up from micro-services using kubernetes would look like and
    interact. This GUI is primarily powered by streamlit
    ### Want to learn more?
    - Check out [streamlit.io](https://streamlit.io)
    - Jump into our [documentation](https://docs.streamlit.io)
    - Ask a question in our [community
        forums](https://discuss.streamlit.io)
    ### See more complex demos
    - Use a neural net to [analyze the Udacity Self-driving Car Image
        Dataset](https://github.com/streamlit/demo-self-driving)
    - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
"""
)