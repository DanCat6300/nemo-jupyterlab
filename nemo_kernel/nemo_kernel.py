from metakernel import MetaKernel
from nmo_python import load_string, NemoEngine
from IPython.display import display, HTML
import re
import pandas as pd
# from ipykernel.kernelbase import Kernel


__version__ = "0.1"
BRACKET_REGEX = r'^<[^>]*>$'
OUTPUT_REGEX = r"@output\s+(\w+)"


class NemoKernel(MetaKernel):
    implementation = 'Nemo Kernel'
    implementation_version = '0.1'
    language = 'text'
    language_version = '0.1'
    banner = " Nemo: Your Friendly and Versatile Rule Reasoning Toolkit"
    language_info = {
        'mimetype': 'text/plain',
        'name': 'text',
        'file_extension': '.txt',
        'help_links': MetaKernel.help_links,
    }

    def __init__(self, **kwargs):
        self.global_state = {}
        super(NemoKernel, self).__init__(**kwargs)


    def get_usage(self):
        return "Reason your rules."
    

    def do_execute(self, code, cell_id, silent=False, store_history=True, user_expressions=None, allow_stdin=False):
        """
        Receive and reason on rules received from the client.
        Args:
            code (str): rules received from server.
            cell_id (uuid): cell id retrieved from client
        Returns:
            Func: Call the default do_execute.
        """
        # Record rules into global_state
        print("cell_id:", cell_id)
        self.global_state[cell_id] = code
        print("global_state:", self.global_state)

        # Compile rules from global_state into a string
        rules_to_reason = ""
        for cell_id in self.global_state:
            rules_to_reason += (str(self.global_state[cell_id]) + '\n')
        
        print(rules_to_reason)

        return super().do_execute(rules_to_reason, silent, store_history, user_expressions, allow_stdin)


    def do_execute_direct(self, rules):
        """
        Receive and reason on rules received from the client.
        Args:
            rules (str): rules received from server.
        Returns:
            Obj: The results returned by Nemo Engine or error.
        """
        # Return if no @Output statement in the current cell
        output_statements = get_output_statement(rules)
        if not output_statements: return
        
        try:
            # Create a nemo engine and reason on rules
            engine = NemoEngine(load_string(rules))
            engine.reason()

            # Get results and convert it to dataframes
            results = get_results(output_statements, engine)
            dfs = convert_to_df(results)

            # Inject html to visualise dataframes on frontend
            output = "".join(
                f"<details><summary><b>{key}</b></summary>{df.to_html(notebook=True)}</details><br>" 
                for key, df in dfs.items()
            )

            return HTML(output)

        except Exception as error:
            return f"Error: {str(error)}"


    def repr(self, data):
        return repr(data)


def get_output_statement(rules):
    """
    Extract output predicate recognised by '@output'.
    Args:
        rules (str): Rules received from server.
    Returns:
        List: List of extracted predicates.
    """ 
    output_statements = re.findall(OUTPUT_REGEX, rules)
    return output_statements


def get_results(output_statements, nemo_engine):
    """
    Extract results from nemo engine for each output predicates.
    Args:
        output_Statements (List): Output statements extracted from the rules.
        nemo_engine (NemoEngine): The instantiated nemo object. 
    Returns:
        dict: Dictionary containing results by out predicates.
    """
    raw_results = {}

    for output_key in output_statements:
        raw_results[output_key] = list(nemo_engine.result(output_key))
    formatted_results = format_results(raw_results)

    return formatted_results


def format_results(output_object):
    """
    Transform all elements in the results object into a more workable format
    Args:
        results (dict): the retrieved result dictionary after reasoning
    Returns:
        dict: the results dictionary with all elements formatted.
    """
    formatted_results = {}

    for key, sublists in output_object.items():
        formatted_results[key] = [
            [element[1:-1] if isinstance(element, str) 
             and bool(re.match(BRACKET_REGEX, element)) 
             else element 
             for element in sublist] 
            for sublist in sublists
        ]

    return formatted_results


def convert_to_df(results):
    """
    Convert result dictionary to pandas dataframe
    """
    dfs = {}

    for key, value in results.items():
        df = pd.DataFrame(value)
        df.columns = [f"Node {i+1}" for i in range(df.shape[1])]
        dfs[key] = df

    return dfs


# Expose kernel methods to backend server
# kernel = NemoKernel()

# def execute_kernel_reasoning(rules):
#     return kernel.do_execute_direct(rules)

# def get_kernel_usage():
#     return kernel.get_usage()

# def terminate_kernel():
#     kernel.do_shutdown()

if __name__ == '__main__':
    NemoKernel.run_as_main()
