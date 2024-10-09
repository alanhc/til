---
title: Building Your Own Database Agent
date: 2024-07-16
tags:
  - llm
updated: 2024-07-16
up:
---
**Building Your Own Database Agent**

[**https://learn.deeplearning.ai/courses/building-your-own-database-agent/lesson/1/introduction**](https://learn.deeplearning.ai/courses/building-your-own-database-agent/lesson/1/introduction)
![[Database Agent 1.png]]
  ![[Artificial Intelligence.png]]
![[Fine tuning.png]]
  ![[Database Agents.png]]

  

  

  

from langchain.agents.agent_types import AgentType

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

  

agent = create_pandas_dataframe_agent(llm=model,df=df,verbose=True)

  

agent.invoke("how many rows are there?")

**> Entering new AgentExecutor chain...**

**Thought: To find out the number of rows in a pandas DataFrame, I can use the `shape` attribute which returns a tuple with the number of rows and columns. The first element of the tuple will give me the number of rows.**

  

**Action: python_repl_ast**

**Action Input: df.shape[0]**

Observation: **20780**

Thought:**I now know the final answer.**

**Final Answer: There are 20780 rows in the dataframe `df`.**

  

**> Finished chain.**

{'input': 'how many rows are there?',

 'output': 'There are 20780 rows in the dataframe `df`.'}

  

  

CSV_PROMPT_PREFIX = """

First set the pandas display options to show all the columns,

get the column names, then answer the question.

"""

  

CSV_PROMPT_SUFFIX = """

- **ALWAYS** before giving the Final Answer, try another method.

Then reflect on the answers of the two methods you did and ask yourself

if it answers correctly the original question.

If you are not sure, try another method.

- If the methods tried do not give the same result,reflect and

try again until you have two methods that have the same result.

- If you still cannot arrive to a consistent result, say that

you are not sure of the answer.

- If you are sure of the correct answer, create a beautiful

and thorough response using Markdown.

- **DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE,

ONLY USE THE RESULTS OF THE CALCULATIONS YOU HAVE DONE**.

- **ALWAYS**, as part of your "Final Answer", explain how you got

to the answer on a section that starts with: "\n\nExplanation:\n".

In the explanation, mention the column names that you used to get

to the final answer.

"""

  

QUESTION = "How may patients were hospitalized during July 2020" 

"in Texas, and nationwide as the total of all states?"

"Use the hospitalizedIncrease column" 

  

  

agent.invoke(CSV_PROMPT_PREFIX + QUESTION + CSV_PROMPT_SUFFIX)
![[Database.png]]
  ![[Pasted Graphic 7.png]]

  

  

# Path to your SQLite database file

database_file_path = "./db/test.db"

  

# Create an engine to connect to the SQLite database

# SQLite only requires the path to the database file

engine = create_engine(f'sqlite:///{database_file_path}')

file_url = "./data/all-states-history.csv"

df = pd.read_csv(file_url).fillna(value = 0)

df.to_sql(

    'all_states_history',

    con=engine,

    if_exists='replace',

    index=False

)

MSSQL_AGENT_PREFIX = """

  

You are an agent designed to interact with a SQL database.

## Instructions:

- Given an input question, create a syntactically correct {dialect} query

to run, then look at the results of the query and return the answer.

- Unless the user specifies a specific number of examples they wish to

obtain, **ALWAYS** limit your query to at most {top_k} results.

- You can order the results by a relevant column to return the most

interesting examples in the database.

- Never query for all the columns from a specific table, only ask for

the relevant columns given the question.

- You have access to tools for interacting with the database.

- You MUST double check your query before executing it.If you get an error

while executing a query,rewrite the query and try again.

- DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.)

to the database.

- DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE, ONLY USE THE RESULTS

OF THE CALCULATIONS YOU HAVE DONE.

- Your response should be in Markdown. However, **when running  a SQL Query

in "Action Input", do not include the markdown backticks**.

Those are only for formatting the response, not for executing the command.

- ALWAYS, as part of your final answer, explain how you got to the answer

on a section that starts with: "Explanation:". Include the SQL query as

part of the explanation section.

- If the question does not seem related to the database, just return

"I don\'t know" as the answer.

- Only use the below tools. Only use the information returned by the

below tools to construct your query and final answer.

- Do not make up table names, only use the tables returned by any of the

tools below.

  

## Tools:

  

"""

MSSQL_AGENT_FORMAT_INSTRUCTIONS = """

  

## Use the following format:

  

Question: the input question you must answer.

Thought: you should always think about what to do.

Action: the action to take, should be one of [{tool_names}].

Action Input: the input to the action.

Observation: the result of the action.

... (this Thought/Action/Action Input/Observation can repeat N times)

Thought: I now know the final answer.

Final Answer: the final answer to the original input question.

  

Example of Final Answer:

<=== Beginning of example

  

Action: query_sql_db

Action Input: 

SELECT TOP (10) [death]

FROM covidtracking 

WHERE state = 'TX' AND date LIKE '2020%'

  

Observation:

[(27437.0,), (27088.0,), (26762.0,), (26521.0,), (26472.0,), (26421.0,), (26408.0,)]

Thought:I now know the final answer

Final Answer: There were 27437 people who died of covid in Texas in 2020.

  

Explanation:

I queried the `covidtracking` table for the `death` column where the state

is 'TX' and the date starts with '2020'. The query returned a list of tuples

with the number of deaths for each day in 2020. To answer the question,

I took the sum of all the deaths in the list, which is 27437.

I used the following query

  

```sql

SELECT [death] FROM covidtracking WHERE state = 'TX' AND date LIKE '2020%'"

```

===> End of Example

  

"""

llm = AzureChatOpenAI(

    openai_api_version="2023-05-15",

    azure_deployment="gpt-4-1106",

    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),

    temperature=0, 

    max_tokens=500

)

  

db = SQLDatabase.from_uri(f'sqlite:///{database_file_path}')

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

QUESTION = """How may patients were hospitalized during October 2020

in New York, and nationwide as the total of all states?

Use the hospitalizedIncrease column

"""

  

agent_executor_SQL = create_sql_agent(

    prefix=MSSQL_AGENT_PREFIX,

    format_instructions = MSSQL_AGENT_FORMAT_INSTRUCTIONS,

    llm=llm,

    toolkit=toolkit,

    top_k=30,

    verbose=True

)
![[Function Calling.png]]
  

def get_current_weather(location, unit="fahrenheit"):

    """Get the current weather in a given location. 

    The default unit when not specified is fahrenheit"""

    if "new york" in location.lower():

        return json.dumps(

            {"location": "New York", "temperature": "40", "unit": unit}

        )

    elif "san francisco" in location.lower():

        return json.dumps(

            {"location": "San Francisco", "temperature": "50", "unit": unit}

        )

    elif "las vegas" in location.lower():

        return json.dumps(

            {"location": "Las Vegas", "temperature": "70", "unit": unit}

        )

    else:

        return json.dumps(

            {"location": location, "temperature": "unknown"}

        )

  

get_current_weather("New York")

  

messages = [

    {"role": "user",

     "content": """What's the weather like in San Francisco,

                   New York, and Las Vegass?"""

    }

]

  

tools = [

    {

        "type": "function",

        "function": {

            "name": "get_current_weather",

            "description": """Get the current weather in a given

                              location.The default unit when not

                              specified is fahrenheit""",

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": """The city and state,

                                        e.g. San Francisco, CA""",

                    },

                    "unit": {

                        "type": "string",

                        "default":"fahrenheit",

                        "enum": [ "fahrenheit", "celsius"],

                        "description": """The messuring unit for

                                          the temperature.

                                          If not explicitly specified

                                          the default unit is 

                                          fahrenheit"""

                    },

                },

                "required": ["location"],

            },

        },

    }

]

  

response = client.chat.completions.create(

    model="gpt-4-1106",

    messages=messages,

    tools=tools,

    tool_choice="auto", 

)

  

response_message = response.choices[0].message

tool_calls = response_message.tool_calls

  

if tool_calls:

    print (tool_calls)

    available_functions = {

        "get_current_weather": get_current_weather,

    } 

    messages.append(response_message)  

    for tool_call in tool_calls:

        function_name = tool_call.function.name

        function_to_call = available_functions[function_name]

        function_args = json.loads(tool_call.function.arguments)

        function_response = function_to_call(

            location=function_args.get("location"),

            unit=function_args.get("unit"),

        )

        messages.append(

            {

                "tool_call_id": tool_call.id,

                "role": "tool",

                "name": function_name,

                "content": function_response,

            }

        )  

    print (messages)

  

second_response = client.chat.completions.create(

            model="gpt-4-1106",

            messages=messages,

        )

print (second_response)
![[Building Your Own Database.png]]
  ![[for scenarios like e-commerce..png]]
![[Code Interpreter.png]]
  

from sqlalchemy import create_engine

import pandas as pd

  

df = pd.read_csv("./data/all-states-history.csv").fillna(value = 0)

  

  

response = client.chat.completions.create(

    model="gpt-4-1106",

    messages=messages,

    tools=tools_sql,

    tool_choice="auto",

)

  

response_message = response.choices[0].message

tool_calls = response_message.tool_calls

  

if tool_calls:

    print (tool_calls)

    available_functions = {

        "get_positive_cases_for_state_on_date": get_positive_cases_for_state_on_date,

        "get_hospitalized_increase_for_state_on_date":get_hospitalized_increase_for_state_on_date

    }  

    messages.append(response_message)  

    for tool_call in tool_calls:

        function_name = tool_call.function.name

        function_to_call = available_functions[function_name]

        function_args = json.loads(tool_call.function.arguments)

        function_response = function_to_call(

            state_abbr=function_args.get("state_abbr"),

            specific_date=function_args.get("specific_date"),

        )

        messages.append(

            {

                "tool_call_id": tool_call.id,

                "role": "tool",

                "name": function_name,

                "content": str(function_response),

            }

        ) 

    print(messages)

second_response = client.chat.completions.create(

            model="gpt-4-1106",

            messages=messages,

        )

print (second_response)

  

  

  

client = AzureOpenAI(

    api_key=os.getenv("AZURE_OPENAI_KEY"),

    api_version="2024-02-15-preview",

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    )

  

# I) Create assistant

assistant = client.beta.assistants.create(

  instructions="""You are an assistant answering questions 

                  about a Covid dataset.""",

  model="gpt-4-1106", 

  tools=Helper.tools_sql)

  

# II) Create thread

thread = client.beta.threads.create()

print(thread)

# III) Add message

message = client.beta.threads.messages.create(

    thread_id=thread.id,

    role="user",

    content="""how many hospitalized people we had in Alaska

               the 2021-03-05?"""

)

print(message)

messages = client.beta.threads.messages.list(

  thread_id=thread.id

)

  

print(messages.model_dump_json(indent=2))

# IV) Run assistant on thread

  

run = client.beta.threads.runs.create(

  thread_id=thread.id,

  assistant_id=assistant.id,

)

import time

from IPython.display import clear_output

  

start_time = time.time()

  

status = run.status

  

while status not in ["completed", "cancelled", "expired", "failed"]:

    time.sleep(5)

    run = client.beta.threads.runs.retrieve(

        thread_id=thread.id,run_id=run.id

    )

    print("Elapsed time: {} minutes {} seconds".format(

        int((time.time() - start_time) // 60),

        int((time.time() - start_time) % 60))

         )

    status = run.status

    print(f'Status: {status}')

    if (status=="requires_action"):

        available_functions = {

            "get_positive_cases_for_state_on_date": get_positive_cases_for_state_on_date,

            "get_hospitalized_increase_for_state_on_date":get_hospitalized_increase_for_state_on_date

        }

  

        tool_outputs = []

        for tool_call in run.required_action.submit_tool_outputs.tool_calls:

            function_name = tool_call.function.name

            function_to_call = available_functions[function_name]

            function_args = json.loads(tool_call.function.arguments)

            function_response = function_to_call(

                state_abbr=function_args.get("state_abbr"),

                specific_date=function_args.get("specific_date"),

            )

            print(function_response)

            print(tool_call.id)

            tool_outputs.append(

                { "tool_call_id": tool_call.id,

                 "output": str(function_response)

                }

            )

  

        run = client.beta.threads.runs.submit_tool_outputs(

          thread_id=thread.id,

          run_id=run.id,

          tool_outputs = tool_outputs

        )

  

  

messages = client.beta.threads.messages.list(

  thread_id=thread.id

)

  

print(messages)

print(messages.model_dump_json(indent=2))

file = client.files.create(

  file=open("./data/all-states-history.csv", "rb"),

  purpose='assistants'

)

assistant = client.beta.assistants.create(

  instructions="""You are an assitant answering questions about

                  a Covid dataset.""",

  model="gpt-4-1106", 

  tools=[{"type": "code_interpreter"}],

  file_ids=[file.id])

thread = client.beta.threads.create()

print(thread)

message = client.beta.threads.messages.create(

    thread_id=thread.id,

    role="user",

    content="""how many hospitalized people we had in Alaska

               the 2021-03-05?"""

)

print(message)

run = client.beta.threads.runs.create(

  thread_id=thread.id,

  assistant_id=assistant.id,

)

  

status = run.status

start_time = time.time()

while status not in ["completed", "cancelled", "expired", "failed"]:

    time.sleep(5)

    run = client.beta.threads.runs.retrieve(

        thread_id=thread.id,

        run_id=run.id

    )

    print("Elapsed time: {} minutes {} seconds".format(

        int((time.time() - start_time) // 60),

        int((time.time() - start_time) % 60))

         )

    status = run.status

    print(f'Status: {status}')

    clear_output(wait=True)

  

  

messages = client.beta.threads.messages.list(

  thread_id=thread.id

)

  

print(messages.model_dump_json(indent=2))