import os
import shutil
import sys
from pathlib import Path
import subprocess
import logging
from io import StringIO


sys.path.append(
    str(Path(__file__).absolute().parent / "src" )
)
sys.path.append(
    str(Path(__file__).absolute().parent / "metaval-c-2.0" / "lib" / "sv-transformer-lib" / "src")
)
sys.path.append(str(Path(__file__).absolute().parent / "metaval-c-2.0" / "src"))
sys.path.append(str(Path(__file__).absolute().parent / "metaval-c-2.0"))
sys.path.append(str(Path(__file__).absolute().parent / "metaval-c-2.0" / "lib" / "pip"))

from data_types import DeductiveVerifierTypes, Verdict
from deductive_verfiers import DeductiveVerifier, FramaC
from preprocessing import generate_annotated_program, preprocess_program
from sv_transformer_lib.data_types.program import Program, DataModel
from sv_transformer_lib.data_types.witness import Witness, WitnessType


from gpt_utils import *
from validation_utils import *

def verify_program(program_path, witness_path):

    '''
    This function verifies the program using the witness file

    Args:
    program_path: Path to the program file
    witness_path: Path to the witness file

    Returns:
    verdict: Verdict of the verification
    reason: Reason for the verdict
    '''
    backend_verifier: DeductiveVerifier = FramaC(plugin="wp")
    backend_clause_format = backend_verifier.required_clause_format()

    program = Program(Path(program_path).read_text())

    # In this case we want to annotate the program with the witness and run the
    # backend verifier on the annotated program
    if not Path(witness_path).exists():
        print("Witness file does not exist")
        sys.exit(1)

    witness = Witness.create(Path(witness_path).read_text())

    if witness.witness_type() != WitnessType.Correctness:
        print("Only correctness witnesses are supported")
        sys.exit(1)

    annotated_program, transformed_witness = generate_annotated_program(
        program, witness, backend_clause_format
    )

    debug_path = Path.cwd() / "debug"
    os.makedirs(debug_path, exist_ok=True)

    if transformed_witness is not None:
        debug_witness_path = debug_path / "witness.yml"
        debug_witness_path.write_text(transformed_witness.witness_str)

    debug_program_path = debug_path / "program.c"
    debug_program_path.write_text(annotated_program.program_str)

    verdict, reason = backend_verifier.verify(annotated_program, "LP64")

    return verdict, reason
    


def test_c_code(file_location):
    '''
    This function tests the C code by generating and checking for invariants

    Args:   
    file_location: Path to the C code file

    Returns:
    verdict: Verdict of the verification
    invariants: List of invariants
    '''
    with open(file_location, 'r') as file:
        code = file.read()
    ## Add line numbers to the code
    code = code.split('\n')
    code_with_line_numbers = []
    for i, line in enumerate(code):
        code_with_line_numbers.append(f'{i+1}: {line}')
    code_with_line_numbers = '\n'.join(code_with_line_numbers)

    counter = 0
    success = False
    while not success and counter < 5:
        ## Getting invariants
        arguments = submit_message(f"Check for invariants in the following: {code_with_line_numbers}")
        invariants = []
        for a in arguments:
            invariants.append(("loop_invariant", a['line_number'], a['invariant']))
            
        ## Creating Witness file
        yaml_file = create_witness_yaml(file_location, invariants, location='./Dataset/Temp')

        ## Testing Invariant
        print(f"Testing Invariant {invariants}...")
        # output = subprocess.run(['python', 'metaval-c-2.0/metaval_c_2.0.py', '--debug', '--witness', f'./Dataset/Temp/{yaml_file}', file_location])
        ## Setting up logger
        log_stream = StringIO()
        logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(log_stream)]
        )

        verdict, reason = verify_program(file_location, f'./Dataset/Temp/{yaml_file}')
        if verdict.name.lower() == "true":
            success = True
        else:
            print(log_stream.getvalue())
            print(f"Failed, resubmitting...")
            submit_function_response(verdict.name.lower(),debug_message=log_stream.getvalue(), reason=str(reason))
            counter += 1


    return verdict.name.lower(), invariants, reason
    
if __name__ == '__main__':
    output = test_c_code('./metaval-c-2.0/examples/terminator02-2_wrong.c')
    print(output)
