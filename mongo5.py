from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
import pymongo
import json

import google.generativeai as gen

# Configure the Google Generative AI with API key
gen.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(question, prompt):
    model = gen.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.gj0kwwa.mongodb.net/cluster0")
db = client["cluster0"]  # Replace "cluster0" with your database name

# Collection attributes
collection_attributes = {
    "admins": ["name", "email", "username", "department", "dob", "joiningYear", "avatar", "contactNumber"],
    "attendances": ["student", "subject", "totalLecturesByFaculty", "lectureAttended"],
    "departments": ["department", "departmentCode"],
    "faculties": ["name", "email", "avatar","username", "gender", "designation", "department", "contactNumber", "dob", "joiningYear"],
    "marks": ["exam", "student", "marks"],
    "notices": ["topic", "date", "content", "from", "noticeFor"],
    "students": ["name", "email", "avatar","year", "subjects", "username", "gender", "fatherName", "motherName", "department", "section", "batch", "contactNumber", "fatherContactNumber", "dob"],
    "subjects": ["subjectName", "subjectCode", "department", "totalLectures", "year", "attendance"],
    "tests": ["test", "subjectCode", "department", "totalMarks", "year", "section", "date"]
}

# Base prompt for AI model
base_prompt = """
    You are an expert in converting English questions to MongoDB query!
    Generate queries without any errors.
    The MyDB database has multiple collections (admin, attendance, departments, faculty, marks, notice, students, subject, test).
    Each document in the collections has different attributes.
    For the question I give, generate a MongoDB query for me in valid JSON format.
    Please add double quotes to the keys also.
    Remove the prefix 'json\n'.
    Use only stages in the MongoDB aggregation pipeline. Don't forget the $ sign.
"""

def create_prompt(collection_name):
    attributes = collection_attributes[collection_name]
    attributes_str = ", ".join(attributes)
    return f"{base_prompt} The {collection_name} collection has attributes: {attributes_str}."

# Streamlit app configuration
st.set_page_config(page_title="Gemini App To Retrieve MongoDB Data")
st.header("Gemini App To Retrieve MongoDB Data")

# User input for collection and question
collection_name = st.selectbox("Select Collection", list(collection_attributes.keys()))
question = st.text_input("Input: ", key="input")
selected_fields = st.multiselect("Select Fields to Display", [attr for attr in collection_attributes[collection_name] if attr != "password"])

# Button to submit the question
submit = st.button("Ask the question")

# If submit is clicked
if submit:
    prompt = [create_prompt(collection_name)]
    response = get_gemini_response(question, prompt)
    try:
        # Parse the response to ensure it is a dictionary
        query = json.loads(response)
        collection = db[collection_name]  # Dynamically select the collection
        dl = collection.aggregate([query])
        
        results = list(dl)  # Convert the cursor to a list
        
        if results:
            # Display the selected fields
            display_results = [{field: doc.get(field, None) for field in selected_fields} for doc in results]
            st.table(display_results)
        else:
            st.header("No documents found")
    except json.JSONDecodeError:
        st.error("Failed to decode the response to a valid JSON dictionary.")
        st.error(repr(response))
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error(query)
