import sys
import argparse

from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.memory import VectorStoreRetrieverMemory
# from langchain_community.vectorstores import FAISS
# from langchain.docstore import InMemoryDocstore

from .libs.config_loader import CFG
from .libs.utils import setupLogging, LOG_VERBOSE

def parse_args(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--config", type=str, default="configs/autocode.yaml", help="The config file for the program.")
  args = parser.parse_args(argv)
  return args

def main():
  args = parse_args()
  cfg = CFG.load_config_as_obj(args.config)
  openai_creds = CFG.load_config_as_obj(cfg.credentials.openai)

  messages = ChatPromptTemplate.from_messages([
    ("system", "You are a chatbot having a conversation with a human.\n{chat_history}"),
    ("human", "{input}"),
  ])
  # prompt_template = "You are a chatbot having a conversation with a human.\n{chat_history}\nHuman: {input}\nChatbot:"
  # prompt = PromptTemplate(input_variables=["chat_history", "input"], template=prompt_template)

  llm = ChatOpenAI(model_name=cfg.model_name, openai_api_key=openai_creds.api_key)

  # embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
  # index = faiss.IndexFlatL2(embedding_size)
  # embedding_fn = OpenAIEmbeddings().embed_query
  # vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
  # retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))

  # memory = VectorStoreRetrieverMemory(retriever=retriever)

  llm_chain = LLMChain(llm=llm, prompt=messages)

  inputs = {
      "input": "What's the capital of the US?",
      "chat_history": "User: Hi\nBot: Hello, how can I assist you?",
  }
  outputs = llm_chain.invoke(inputs)

  print(outputs)

if __name__ == "__main__":
  main()
