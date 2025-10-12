from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

model = OllamaLLM(model="llama3.2")

template="""
You are expert in answering questions about the trip queries
Here are some relevent information:{reviews} 
Here are the questions to answers:{question}
"""

prompt =ChatPromptTemplate.from_template(template)
chain =prompt|model
while True:
    print("\n\n-------------------------------------")
    question =input("Ask any queries about the Trip  (q to quit):")
    print("\n\n")
    if question == "q":
        break

    reviews= retriever.invoke(question)
    result = chain.invoke({"reviews":reviews,"question":question})
    print(result)


