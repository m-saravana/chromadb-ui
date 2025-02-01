import streamlit as st
import chromadb
from chromadb.config import Settings
import uuid

# Must be the first Streamlit command
st.set_page_config(layout="wide", page_title="ChromaDB UI")

# Custom CSS to match the dark theme and layout
st.markdown("""
<style>
    /* Dark theme colors */
    :root {
        --background-color: #1a1a1a;
        --text-color: #ffffff;
        --border-color: #333333;
        --hover-color: #2d2d2d;
    }
    
    /* Main container */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--background-color);
        border-right: 1px solid var(--border-color);
    }
    
    /* Collection list styling */
    .collection-list {
        padding: 10px;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Table styling */
    .stDataFrame {
        background-color: var(--background-color) !important;
    }
    
    .stDataFrame table {
        border-collapse: collapse;
        width: 100%;
    }
    
    .stDataFrame th {
        background-color: var(--border-color);
        padding: 12px;
        text-align: left;
    }
    
    .stDataFrame td {
        padding: 12px;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    
    .stButton>button:hover {
        background-color: #45a049;
    }
    
    /* Search box styling */
    .stTextInput>div>div>input {
        background-color: var(--background-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    
    /* Export button */
    .export-button {
        position: absolute;
        right: 20px;
        top: 20px;
    }
</style>
""", unsafe_allow_html=True)

def init_chroma_client(host_type):
    if host_type == "Local":
        return chromadb.Client()
    else:
        # You'll need to configure these values
        return chromadb.HttpClient(host=st.session_state.host, 
                                 port=st.session_state.port)

def display_documents(collection):
    # Get all documents
    result = collection.get()
    
    if result and result['documents']:
        st.markdown("### Documents")
        
        # Display documents in an expandable format
        for id, doc, metadata in zip(result['ids'], result['documents'], result['metadatas']):
            with st.expander(f"Document: {id}"):
                st.markdown("**ID:**")
                st.code(id)  # Using code block for better ID visibility
                
                st.markdown("**Content:**")
                st.text_area("", value=doc, height=150, disabled=True)  # Using text_area for scrollable content
                
                st.markdown("**Metadata:**")
                st.json(metadata)  # Pretty print metadata as JSON
                
                st.markdown("---")
    else:
        st.info("No documents in this collection")

def add_document_form(collection):
    with st.form("add_document_form"):
        doc_content = st.text_area("Document Content")
        col1, col2 = st.columns(2)
        with col1:
            metadata_key = st.text_input("Metadata Key (optional)")
        with col2:
            metadata_value = st.text_input("Metadata Value (optional)")
        
        submitted = st.form_submit_button("Add Document")
        if submitted and doc_content:
            metadata = {metadata_key: metadata_value} if metadata_key and metadata_value else {}
            doc_id = str(uuid.uuid4())
            collection.add(
                documents=[doc_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            st.success("Document added successfully!")
            st.rerun()
        elif submitted:
            st.error("Please enter document content")

def main():
    # Sidebar
    with st.sidebar:
        st.title("ChromaDB UI")
        
        # Connection Settings
        if 'host_type' not in st.session_state:
            st.session_state.host_type = "Local"
            
        host_type = st.radio("Select Host Type", ["Local", "Remote"], key='host_type')
        if host_type == "Remote":
            st.text_input("Host", value="localhost", key="host")
            st.number_input("Port", value=8000, key="port")
        
        st.markdown("---")
        
        # Danger Zone Toggle
        st.sidebar.markdown("### Danger Zone")
        enable_danger = st.sidebar.checkbox("Enable Delete Operations", key="enable_danger")
        
        # Create Collection button
        with st.expander("Collection Management"):
            new_collection_name = st.text_input("Collection Name")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Collection") and new_collection_name:
                    try:
                        client = init_chroma_client(host_type)
                        client.create_collection(name=new_collection_name)
                        st.success(f"Collection created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Delete Collection button (only shown when danger mode is enabled)
            with col2:
                if enable_danger and st.button("Delete Collection", type="secondary"):
                    try:
                        client = init_chroma_client(host_type)
                        client.delete_collection(name=new_collection_name)
                        st.success(f"Collection deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Main content
    try:
        client = init_chroma_client(host_type)
        collection_names = client.list_collections()
        
        # Export button in header
        col1, col2 = st.columns([6, 1])
        with col2:
            if collection_names:  # Only show export if there are collections
                st.download_button("Export", "data", "export.json")
        
        if not collection_names:
            st.info("No collections found")
        else:
            # Store selected collection in session state
            if 'selected_collection' not in st.session_state:
                st.session_state.selected_collection = collection_names[0]
                
            selected_collection = st.selectbox(
                "Select Collection",
                collection_names,
                key="selected_collection"
            )
            
            if selected_collection:
                collection = client.get_collection(name=selected_collection)
                
                tab1, tab2 = st.tabs(["Documents", "Add Document"])
                
                with tab1:
                    display_documents(collection)
                
                with tab2:
                    add_document_form(collection)
                
                
    except Exception as e:
        st.error(f"Error connecting to ChromaDB: {str(e)}")

if __name__ == "__main__":
    main() 