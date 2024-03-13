# Render prompts for LLM

Mext can be integrated into existing LLM pipeline easily.

### Integration with Langchain

Mext template:
```mext
Answer the following questions one by one:
{@for q in questions}
- {q}
{@endfor}

Answer:
```

Python:
```python
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
```

Example output:
```plaintext
==== PROMPT ====
Answer the following questions one by one:
- The distance of sun to earth
- Who is Alan Turing
- What is the name of the planet where the Foundation established?

Answer:
==== OUTPUT ====
1. The distance of the sun to earth is approximately 93 million miles.
2. Alan Turing was a British mathematician, logician, and computer scientist who is considered one of the founding fathers of computer science.
3. The name of the planet where the Foundation established is Terminus.
```

You can run this example with:
```bash
$ python examples/prompts_for_llm.py
```