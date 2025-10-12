from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd

df=pd.read_csv("Dubai_trip.csv")
embeddings= OllamaEmbeddings(model="mxbai-embed-large")


db_location="./chrome_lamgchain_db"
add_documents=not os.path.exists(db_location)

if add_documents:
    documents=[]
    ids=[]

    for i,row in df.iterrows():
        document=Document(
            page_content=row["Date"] + " " + row["Activity"],
            metadata={
                "timing": row["Timing"],
                "location": row["Location"],
                "transport": row["Transport / Flight"],
                "attractions": row["Attractions / Details"],
                "meals_hotel": row["Meals / Hotel"]
            },
            id=str(i)
        )
        ids.append(str(i))
        documents.append(document)

vector_store=Chroma(
    collection_name="Dubai_Trip",
    persist_directory=db_location,
    embedding_function=embeddings

)

if add_documents:
    vector_store.add_documents(documents,ids=ids)
   
retriever=vector_store.as_retriever(
    search_kwargs={"k":1}
)