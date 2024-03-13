from mext import Mext

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser

def questions2prompt(params):
  mext = Mext()
  prompt = mext.compose(template_fn="examples/prompts_for_llm.mext", params=params)
  print('==== PROMPT ====')
  print(prompt) # print the prompt for debug purpose
  return prompt

# Set your api key in environment: OPENAI_API_KEY=<your_api_key>
llm = ChatOpenAI(model_name="gpt-3.5-turbo")
output_parser = StrOutputParser()
chain = RunnableLambda(questions2prompt) | llm | output_parser

params = {
  "questions": [
    'The distance of sun to earth',
    'Who is Alan Turing',
    'What is the name of the planet where the Foundation established?',
  ],
}
output = chain.invoke(params)
print('==== OUTPUT ====')
print(output)