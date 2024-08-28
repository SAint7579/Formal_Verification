import os
import shutil
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).absolute().parent / "src" )
)

from gpt_utils import *
from validation_utils import *

def test_c_code(file_location):
    with open(file_location, 'r') as file:
        code = file.read()
    ## Add line numbers to the code
    code = code.split('\n')
    code_with_line_numbers = []
    for i, line in enumerate(code):
        code_with_line_numbers.append(f'{i+1}: {line}')
    code_with_line_numbers = '\n'.join(code_with_line_numbers)

    arguments = submit_message(f"Check for invariants in the following: {code_with_line_numbers}")
    
    invariants = []
    for a in arguments:
        invariants.append(("loop_invariant", a['line_number'], a['invariant']))

    print(invariants)
    
    yaml_file = create_witness_yaml(file_location, invariants, location='./Dataset/Temp')
    print(yaml_file)

if __name__ == '__main__':
    test_c_code('./Dataset/Raw Codes/test_code_1.c')