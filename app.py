import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. SETUP AND CONFIGURATION ---

st.set_page_config(page_title="Lesson Creation Bot", layout="centered")

# Configure the Gemini API key securely
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (AttributeError, KeyError):
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        st.error("API Key not found. Please set your GEMINI_API_KEY in Streamlit secrets or as an environment variable.", icon="🚨")
        st.stop()

# --- 2. HELPER FUNCTIONS ---

@st.cache_data
def load_data():
    """Loads the recommendation data from CSV files."""
    try:
        recommendations_df = pd.read_csv('recommendations_final.csv')
        problem_rec_df = pd.read_csv('problem_recommendations_final.csv')
        return recommendations_df, problem_rec_df
    except FileNotFoundError as e:
        st.error(f"Error: A required data file was not found: `{e.filename}`.", icon="🚨")
        return None, None

def find_problem_recommendation(user_problem_text, recommendations_df):
    """Scans user text for keywords to find the correct client audience."""
    if not user_problem_text or not isinstance(user_problem_text, str): return None
    for _, row in recommendations_df.iterrows():
        if row['problem_keyword'].lower() in user_problem_text.lower(): return row
    return None

def generate_content(prompt):
    """A single function to send any prompt to the Gemini API."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while contacting the AI model: {e}", icon="🔥")
        return None

# Initialize session state to manage the multi-step form
if 'stage' not in st.session_state:
    st.session_state.stage = 0
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

def set_stage(stage):
    st.session_state.stage = stage

# --- 3. MAIN APPLICATION UI ---

st.image("logo.png", width=100)

# STAGE 0: Initial Profile Form
if st.session_state.stage == 0:
    st.title("Welcome to the Lesson Creation Bot!")
    st.info("This bot acts as your personal instructional designer, guiding you from a high-level idea to a complete, ready-to-film lesson plan.", icon="✍️")
    
    st.header("Step 1: What would you like to create now?", divider="gray")
    
    goal_type = st.radio(
        "Select the type of content you are creating:",
        ["A Single Lesson (for 'additional classes')", "A Lesson that is part of your 12-lesson program"],
        index=None
    )

    lesson_number = None
    if goal_type == "A Lesson that is part of your 12-lesson program":
        lesson_number = st.selectbox("Which lesson of the program are you working on?", range(1, 13))

    if st.button("Next Step", use_container_width=True, type="primary"):
        if not goal_type:
            st.error("Please select a content type to continue.")
        else:
            st.session_state.form_data['goal_type'] = goal_type
            if lesson_number:
                st.session_state.form_data['lesson_number'] = lesson_number
            set_stage(1)
            st.rerun()

# STAGE 1: Import Blueprint
if st.session_state.stage == 1:
    st.header("Step 2: Import Your Blueprint", divider="gray")
    
    has_blueprint = st.radio("Do you have your 'Program Blueprint' from the Program Advisor Bot?", ["Yes, I have it", "No, I need to create one"])

    if has_blueprint == "Yes, I have it":
        blueprint = st.text_area("Great! Please paste the full 'Program Blueprint' you received below.", height=250)
        if st.button("Next Step", use_container_width=True, type="primary"):
            if not blueprint:
                st.error("Please paste your blueprint to continue.")
            else:
                st.session_state.form_data['blueprint'] = blueprint
                set_stage(2)
                st.rerun()
    else:
        st.warning("No problem! A blueprint is essential for the best results. Please visit our Program Advisor Bot to create your plan. Once you have it, please come back here to continue.")
        st.link_button("Go to Program Advisor Bot", "YOUR_LINK_TO_THE_FIRST_BOT_HERE")


# STAGE 2: Define Lesson Core
if st.session_state.stage == 2:
    st.header("Step 3: Define the Lesson's Core", divider="gray")
    
    lesson_type = st.radio(
        "What type of lesson are you creating?",
        ["An Educational Lesson (explaining a concept)", "A Hands-on Tutorial (a practical, follow-along guide)"],
        key="lesson_type"
    )
    st.write("---")

    with st.form("lesson_core_form"):
        if lesson_type == "An Educational Lesson (explaining a concept)":
            st.subheader("Educational Lesson Details")
            q1 = st.text_area("The Core Question: What is the one key question this lesson will answer for your student?", placeholder="e.g., Why does my skin get oily in the afternoon?")
            q2 = st.text_area("Key Teaching Points: What are the 3 most important points or takeaways you will teach?", placeholder="e.g., 1. The role of sebum production...")
            q3 = st.text_input("Core Analogy: What is a simple analogy or real-world example you can use?", placeholder="e.g., Think of your skin like a plant that needs water...")
            q4 = st.text_input("Actionable Tip: What is one simple tip the student can apply immediately?", placeholder="e.g., Try adding a hydrating serum before your moisturizer...")
            submitted = st.form_submit_button("Generate Lesson Structure", use_container_width=True, type="primary")
            if submitted:
                if not all([q1, q2, q3, q4]):
                    st.error("Please fill in all fields to continue.")
                else:
                    st.session_state.form_data['lesson_type'] = 'Educational'
                    st.session_state.form_data['methodology'] = {"core_question": q1, "teaching_points": q2, "analogy": q3, "actionable_tip": q4}
                    set_stage(3)
                    st.rerun()
        else:
            st.subheader("Hands-on Tutorial Details")
            q1 = st.text_input("The Specific Outcome: What tangible, physical result will the student achieve?", placeholder="e.g., A visibly lifted jawline after a 5-minute guasha routine.")
            q2 = st.text_area("Critical Steps: What are the 3-5 most critical physical steps or movements?", placeholder="e.g., 1. Prepping skin with oil...")
            q3 = st.text_input("The Common Mistake: What is the number one mistake beginners make?", placeholder="e.g., Using too much pressure. It should be gentle...")
            q4 = st.text_input("Required Tools: What specific tools and products must the student have ready?", placeholder="e.g., A clean guasha tool and facial oil.")
            submitted = st.form_submit_button("Generate Lesson Structure", use_container_width=True, type="primary")
            if submitted:
                if not all([q1, q2, q3, q4]):
                    st.error("Please fill in all fields to continue.")
                else:
                    st.session_state.form_data['lesson_type'] = 'Hands-on'
                    st.session_state.form_data['methodology'] = {"outcome": q1, "steps": q2, "mistake": q3, "tools": q4}
                    set_stage(3)
                    st.rerun()

# STAGE 3: Generate Final Lesson Structure
if st.session_state.stage == 3:
    st.header("✅ Your Complete Lesson Plan", divider="gray")
    data = st.session_state.form_data
    
    with st.spinner("Your personal instructional designer is building your lesson plan..."):
        prompt = ""
        if data.get('lesson_type') == 'Educational':
            prompt = f"""
            You are an expert instructional designer creating a plan for an EDUCATIONAL video lesson.
            **Base Information from Program Blueprint:**\n---\n{data.get('blueprint')}\n---
            **Specific Lesson Methodology:**
            * Core Question to Answer: {data['methodology']['core_question']}
            * Key Teaching Points: {data['methodology']['teaching_points']}
            * Core Analogy: {data['methodology']['analogy']}
            * Actionable Tip: {data['methodology']['actionable_tip']}
            **Your Task:**
            Generate a complete lesson structure with these sections:
            1. **Lesson Title:** (A compelling, 2-3 word title)
            2. **Lesson Description:** (A concise, 3-4 line description for an app)
            3. **Targeted Concepts:** (List the key concepts based on the provided info)
            4. **Detailed Video Script Outline (7-12 minutes):**
                * Part 1: The Hook (0-30s)
                * Part 2: The "What & Why" (1-2m)
                * Part 3: The Main Content (5-8m)
                * Part 4: The Summary & Call to Action (1m)
            Format the entire output using Markdown.
            """
        else: # Hands-on
            prompt = f"""
            You are an expert instructional designer creating a plan for a HANDS-ON tutorial.
            **Base Information from Program Blueprint:**\n---\n{data.get('blueprint')}\n---
            **Specific Lesson Methodology:**
            * Specific Outcome: {data['methodology']['outcome']}
            * Critical Steps: {data['methodology']['steps']}
            * Common Mistake to Avoid: {data['methodology']['mistake']}
            * Required Tools: {data['methodology']['tools']}
            **Your Task:**
            Generate a complete lesson structure with these sections:
            1. **Lesson Title:** (A powerful, 2-3 word title)
            2. **Lesson Description:** (A concise, 3-4 line description for an app)
            3. **Targeted Zones:** (List the relevant physical zones)
            4. **Short Video Series Content Plan (7-15 videos, 30-60s each):**
                * Introduction (1-2 Videos)
                * Core Exercises (5-10 Videos)
                * Conclusion (1-3 Videos)
            Format the entire output using Markdown.
            """

        lesson_plan = generate_content(prompt)
        if lesson_plan:
            st.info("You can now edit your lesson plan below and copy the text for your records.", icon="📋")
            st.text_area("Your Editable Lesson Plan", value=lesson_plan, height=500)

            # ** NEW: NON-EDITABLE GUIDE FOR HANDS-ON TUTORIALS **
            if data.get('lesson_type') == 'Hands-on':
                st.info(
                    """
                    **How to Use These Recommendations:**

                    Think of this as your creative blueprint, not a mandatory script! Feel free to adjust the video lengths, add your own personal touch, and tailor the language to your specific audience. The key is to maintain a positive, encouraging, and easy-to-follow approach. Remember to emphasize the importance of gentle pressure and consistent practice for optimal results. You can also add text overlays, music, and other visual elements to enhance the learning experience. The goal is to empower your students to achieve a radiant, healthy complexion through this simple yet effective technique.
                    """,
                    icon="💡"
                )

    if st.button("Create Another Lesson", use_container_width=True):
        set_stage(0)
        st.session_state.form_data = {}
        st.rerun()

