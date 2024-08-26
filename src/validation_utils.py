import yaml
import uuid
from datetime import datetime

def create_witness_yaml(c_file_name, invariants, location):
    # Generate the metadata
    metadata = {
        "format_version": "2.0",
        "uuid": str(uuid.uuid4()),
        "creation_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "producer": {
            "name": "CPAchecker",
            "version": "2.3.1-svn-cb293c3e5d+",
            "configuration": "predicateAnalysis"
        },
        "task": {
            "input_files": [f"./{c_file_name}"],
            "input_file_hashes": {
                f"./{c_file_name}": "<hash_placeholder>"
            },
            "specification": "CHECK( init(main()), LTL(G ! call(reach_error())) )",
            "data_model": "ILP32",
            "language": "C"
        }
    }
    
    # Create the content list with invariants
    content = []
    for invariant_type, line_number, string in invariants:
        invariant_entry = {
            "invariant": {
                "type": invariant_type,
                "location": {
                    "file_name": f"./{c_file_name}",
                    "line": line_number,
                    "column": 1,  # Assuming column is 1 if not provided
                    "function": "main"
                },
                "value": string,
                "format": "c_expression"
            }
        }
        content.append(invariant_entry)
    
    # Combine everything into a single dictionary as a list item
    witness = [{
        "entry_type": "invariant_set",
        "metadata": metadata,
        "content": content
    }]
    
    # Write to a YAML file
    yaml_file_name = c_file_name.replace('.c', '_witness.yaml')
    yaml_file_name = yaml_file_name.split('/')[-1]
    with open(f'{location}/{yaml_file_name}', 'w') as yaml_file:
        yaml.dump(witness, yaml_file, default_flow_style=False, sort_keys=False)

    return yaml_file_name



if __name__ == '__main__':
    # Example usage
    c_file_name = "metaval-c-2.0/examples/terminator02-2.c"
    invariants = [("loop_invariant", 26, "1")]

    yaml_file = create_witness_yaml(c_file_name, invariants, location='../Dataset/Temp')
    print(f"Witness YAML file created: {yaml_file}")