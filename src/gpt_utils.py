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


instructions=f"You are a helpful AI software assistant that reasons about how code behaves. Given a program,\
you can find loop invariants, which can then be used to verify some property in the program.\
Frama-C is a software verification tool for C programs. The input to Frama-C is a C program\
file with ACSL (ANSI/ISO C Specification Language) annotations. You are only allowed to make function calls. Do not respond with text.\
For the given program, find the necessary loop invariants of the while loop to help Frama-C verify the post-condition.\
Instructions:\
• Make a note of the pre-conditions or variable assignments in the program.\
• Analyze the loop body and make a note of the loop condition.\
• Output loop invariants that are true\
(i) before the loop execution,\
(ii) in every iteration of the loop and\
(iii) after the loop termination,\
such that the loop invariants imply the post condition.\
• If a loop invariant is a conjunction, split it into its parts.\
• Use the appropriate function to test if the invariats are correct. Create one invariant for each loop in the program.\
• All the loops in the same line of code must be joined into a single invariant with &&s\
Rules:\
• **Do not use variables or functions that are not declared in the program.**\
• **Do not make any assumptions about functions whose definitions are not given.**\
• **All undefined variables contain garbage values. Do not use variables that have garbage\
values.**\
• **Do not use keywords that are not supported in ACSL annotations for loops.**\
• **Variables that are not explicitly initialized, could have garbage values. Do not make\
any assumptions about such values.**\
• **Do not use the at(x, Pre) notation for any variable x.**\
• **Do not use non-deterministic function calls.**\
"

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

    

