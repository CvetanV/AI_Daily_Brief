import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.database.connection import SessionLocal
from app.database.models import Resource

st.title("🛠️ AI Resources & Tools")

db = SessionLocal()
try:
    st.write("A centralized repository for useful AI tools, configurations, and prompt engineering resources.")
    
    with st.expander("➕ Add New Resource"):
        with st.form("new_resource_form", clear_on_submit=True):
            r_name = st.text_input("Name (e.g., LocalLLaMA Config)")
            r_cat = st.selectbox("Category", ["Tool", "Prompt", "Configuration", "Repository", "Guide", "Other"])
            r_link = st.text_input("URL / Link")
            r_desc = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Resource")
            if submitted and r_name:
                new_res = Resource(name=r_name, category=r_cat, link=r_link, description=r_desc)
                db.add(new_res)
                db.commit()
                st.success("Resource added successfully!")
                st.rerun()

    st.divider()
    
    # List resources
    resources = db.query(Resource).order_by(Resource.category, Resource.created_at.desc()).all()
    
    if not resources:
        st.info("No resources added yet.")
    else:
        # Group by category
        categories = sorted(list(set([r.category for r in resources])))
        
        for cat in categories:
            st.subheader(cat)
            cat_resources = [r for r in resources if r.category == cat]
            
            for r in cat_resources:
                with st.container(border=True):
                    st.markdown(f"**{r.name}**")
                    if r.link:
                        st.markdown(f"[Link]({r.link})")
                    if r.description:
                        st.write(r.description)

except Exception as e:
    st.error(f"Error loading resources: {e}")
finally:
    db.close()
