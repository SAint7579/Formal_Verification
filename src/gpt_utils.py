from openai import OpenAI
import configparser
import time
from ast import literal_eval

config = configparser.ConfigParser()
config.read('./config.ini')
OPENAI_KEY = config["API"]["OPENAI_KEY"]

function = [{
  "name": "test_loop_invariant",
  "description": "Function to test a set of loop invariants on the given C code",
  "strict": False,
  "parameters": {
    "type": "object",
    "properties": {
      "invariant_list": {
        "type": "array",
        "description": "List of invariants along with their line numbers",
        "items": {
          "type": "object",
          "properties": {
            "line_number": {
              "type": "integer",
              "description": "Line Number of the invariant"
            },
            "invariant": {
              "type": "string",
              "description": "The invariant string"
            }
          },
          "required": [
            "line_number",
            "invariant"
          ]
        }
      }
    },
    "required": [
      "invariant_list"
    ]
  }
}]

## Creating the assistant
client = OpenAI(api_key=OPENAI_KEY)
for i in [i.id for i in client.beta.assistants.list().data if i.name == "invariant_generator"]:
    client.beta.assistants.delete(i)


instructions=f'You are supposed to generate a loop invariant and function invariants for C codes. \
              The format should be usable in witness and should be written in a C syntax. For example: "(i == (6) && sn == (10)) || (i == (2) && sn == (2))". \
              Call the appropriate function as soon as you encounter a C code.  Create only one invariant per loop in the code. \
              If you get a failuer, use the debug output to generate and test another invariant.'

MESSAGES = [
    {
        "role": "system",
        "content": instructions
    }
]
## Functions
def submit_message(user_message):
    MESSAGES.append(
        {
            "role": "user",
            "content": user_message
        }
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=MESSAGES,
        functions=function,
        function_call="auto"
    )

    if response.choices[0].finish_reason == "function_call":
        MESSAGES.append(
            {
                "role": "assistant",
                "function_call": {"name": response.choices[0].message.function_call.name,
                                  "arguments": response.choices[0].message.function_call.arguments}
            }
        )

        # MESSAGES.append()
        return literal_eval(response.choices[0].message.function_call.arguments)['invariant_list']
    else:
        return None

def submit_function_response(success, debug_message, reason):
    function_name = MESSAGES[-1]['function_call']['name']
    MESSAGES.append(
        {
            "role": "function",
            "name": function_name,
            "content": str({
                "output": success,
                "debug_message": debug_message,
                "reason": reason
            })
        }
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=MESSAGES,
        functions=function,
        function_call="auto"
    )

    if response.choices[0].finish_reason == "function_call":
        MESSAGES.append(
            {
                "role": "assistant",
                "function_call": {"name": response.choices[0].message.function_call.name,
                                  "arguments": response.choices[0].message.function_call.arguments}
            }
        )
        return literal_eval(response.choices[0].message.function_call.arguments)['invariant_list']

    else:
        return None

    

