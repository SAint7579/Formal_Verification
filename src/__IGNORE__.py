import subprocess

def check_loop_invariant(file_path):
    # Define the frama-c command with necessary options
    frama_c_command = ['frama-c', '-wp', '-wp-prover', 'alt-ergo', file_path]
    
    try:
        # Run the frama-c command using subprocess
        result = subprocess.run(frama_c_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if there were any errors
        if result.returncode != 0:
            print("Frama-C encountered an error:")
            print(result.stderr)
            return False
        
        # Analyze the output to determine the status of the loop invariant verification
        output = result.stdout
        print(output)  # For debugging purposes, you may want to see the full output

        # Check for proved goals and timeouts
        proved_goals_line = [line for line in output.split('\n') if "Proved goals" in line]
        timeout_line = [line for line in output.split('\n') if "Timeout" in line]

        if proved_goals_line:
            print(proved_goals_line[0])
        
        if timeout_line:
            print(timeout_line[0])
        
        # Extract number of proved goals and timeouts
        proved_goals = int(proved_goals_line[0].split(':')[1].split('/')[0].strip()) if proved_goals_line else 0
        total_goals = int(proved_goals_line[0].split(':')[1].split('/')[1].strip()) if proved_goals_line else 0
        timeouts = int(timeout_line[0].split(':')[1].strip()) if timeout_line else 0

        # Determine if loop invariant verification was successful
        if proved_goals == total_goals:
            print("Loop invariant verification successful!")
            return True
        else:
            print(f"Loop invariant verification failed. {proved_goals} out of {total_goals} goals were proved. {timeouts} timeouts occurred.")
            return False

    except Exception as e:
        print(f"An error occurred while running frama-c: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    file_path = './Codebase/test_code_2.c'

    # frama_c_command = ['frama-c', '-wp', '-wp-prover', 'alt-ergo', file_path]
    # result = subprocess.run(frama_c_command)
    # print(result.stdout)

    is_successful = check_loop_invariant(file_path)
    print(f"Loop invariant verification result: {is_successful}")
