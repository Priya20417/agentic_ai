import streamlit as st
from src import router_workflow
from IPython.display import Image

st.set_page_config(page_title="AI Workflow Architecture", layout="wide")

st.sidebar.header("Settings")
theme = st.sidebar.selectbox("Select Theme", ["Light", "Dark"])
toggle_agents = st.sidebar.checkbox("Show Agent Descriptions", value=True)

st.title("🚀 AI Assistant Workflow Architecture")
st.subheader("Visualizing the Routing Structure of Agents")

st.markdown(
    """
    <style>
    .big-font {
        font-size:18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="big-font">This diagram illustrates how different AI agents interact within the system.</p>',
    unsafe_allow_html=True,
)

graph_image = router_workflow.get_graph().draw_mermaid_png()

st.image(graph_image, caption="🛠 Workflow Routing Diagram", use_container_width=True)

if toggle_agents:
    with st.expander("🤖 **Meet Your AI Agents**", expanded=True):
        st.write(
            """
        - **📅 Calendar Manager**  
          Need to **schedule an event** without the hassle? Our AI-powered Calendar Manager is **seamlessly integrated with Google Calendar API**.  
          Simply provide a **date, time, email of the attendee, and duration**—and voilà! Your event is scheduled in seconds. No back-and-forth emails, no confusion.  

        - **📧 Email Manager**  
          Struggling with writing emails? Just give a **brief idea** of what you need, and our AI, powered by the **Gmail API**, will generate a **perfectly drafted email**—from subject line to content.  
          Need to follow up on a meeting? Apologize for a delay? Pitch an idea? Our **Email Manager** makes sure your message is **clear, professional, and impactful**.  

        - **🏋️ Health Coach**  
          Your **AI wellness buddy** is here! Whether you're looking for a **personalized workout plan, daily motivation, or health tips**, our Health Coach helps you **stay on track**.  
          From **dietary advice** to **mental well-being**, this AI agent acts like a **digital fitness trainer**, helping you build better habits—one step at a time.  

        - **🧠 Life Advisor**  
          Need a **boost in productivity**? Stuck on a tough decision? The **Life Advisor** agent is like your **personal strategist**—helping you **optimize routines, break procrastination, and set smart goals**.  
          Whether it's **career guidance, mindfulness techniques, or self-improvement hacks**, this AI ensures you're **always a step ahead**.  
        """
        )

st.markdown("---")
