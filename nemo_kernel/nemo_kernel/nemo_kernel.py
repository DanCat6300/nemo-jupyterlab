import ast
from metakernel import MetaKernel
from nmo_python import load_string, NemoEngine, NemoOutputManager
from IPython.display import HTML
import re
import pandas as pd
import os
import matplotlib.pyplot as plt

__version__ = "0.1"
BRACKET_REGEX = r'^<[^>]*>$'
OUTPUT_REGEX = r"(?<![\s%])\s*@output\s+(\S+)\s*\."
EXPORT_REGEX = r"@export\s+(\w+)\s*:- "
PLOT_REGEX = r"(?<![\s%])\s*@plot\s+(\S+)\s*\."


class NemoKernel(MetaKernel):
    implementation = 'Nemo Kernel'
    implementation_version = '0.1'
    language = 'nemo'
    banner = " Nemo: Your Friendly and Versatile Rule Reasoning Toolkit"
    language_info = {
        'mimetype': 'text/x-nemo',
        'name': 'nemo',
        "version": '1'
    }

    def __init__(self, **kwargs):
        self.global_state = {}
        self.output_predicates = []
        self.export_predicates = []
        self.plot_predicates = []
        self.current_cell_id = ''
        self.assert_outputs = {}
        self.actual_outputs = {}
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
        # On cell removal event, update global state and return
        if 'cell_removal_event' in code:
            self.global_state = handle_cell_removal(self.global_state, code)
            return

        self.current_cell_id = cell_id

        # Extract output predicates from the rules 
        self.output_predicates = re.findall(OUTPUT_REGEX, code)
        self.export_predicates = re.findall(EXPORT_REGEX, code)
        self.plot_predicates = re.findall(PLOT_REGEX, code)
        if '@assert' in code: self.assert_outputs = preprocess_assert(self, code)

        # Filter @output, @export and @plot statements from rules before recording to global_state if any
        rules_to_save = code
        if self.output_predicates or self.export_predicates or self.plot_predicates or self.assert_outputs:
            rules_to_save = filter_statements(code)

        # Record rules into global_state without @output, @export and @plot
        self.global_state[cell_id] = rules_to_save

        # Compile all active rules from global_state with the current cell into a string
        for key in self.global_state:
            if cell_id != key:
                code += (str(self.global_state[key]) + '\n')

        return super().do_execute(code, silent, store_history, user_expressions, allow_stdin)


    def do_execute_direct(self, rules):
        """
        Receive and reason on rules received from the client.
        Args:
            rules (str): rules received from server.
        Returns:
            Obj: The results returned by Nemo Engine or error.
        """
        if '@assert' in rules: rules = filter_assert_statements(rules)

        try:
            # Create a nemo engine and reason on rules
            modified_rules = re.sub(r'@plot', '@output', rules)
            engine = NemoEngine(load_string(modified_rules))
            engine.reason()

            #Export @export predicates when it is needed
            if self.export_predicates:
                export_results(engine,rules)

            # If plot statement exists, Plot the results:
            if self.plot_predicates:
                plot_results(self, engine) 

            output = ""
            # If no output statements, return without displaying results
            if self.output_predicates: 
                # Get results and convert it to dataframes
                results = get_results(self.output_predicates, engine)
                self.actual_outputs.update(results)

                dfs = convert_to_df(results)

                # Inject html to visualise dataframes on frontend
                output = "".join(
                    f"<details><summary><b>{key}</b></summary>{df.to_html(notebook=True)}</details><br>" 
                    for key, df in dfs.items()
                )

            if self.plot_predicates:
                output += f'<img src="{self.current_cell_id}.png"/>'

            if self.assert_outputs:            
                execute_assert(self)

            self.output_predicates = []
            self.export_predicates = []
            self.plot_predicates = []
            self.assert_outputs = {}

            # If there is no output, return without displaying any results
            if not output: return 

            return HTML(output)

        except Exception as error:
            # Remove error cell from global_state and clear cache
            self.global_state.pop(self.current_cell_id)
            self.output_predicates = []
            self.export_predicates = []
            self.plot_predicates = []
            self.assert_outputs = {}

            # Return error
            self.Error(f"Error: {str(error)}")
            self.kernel_resp = {
                "status": "error",
                "execution_count": self.execution_count,
                "ename": type(error).__name__,
                "evalue": str(error),
                "traceback": [rules],
            }
            return 

    def do_debug_request(self, msg):
        pass # Pass to keep the kernel console clean

    def repr(self, data):
        return repr(data)


def filter_statements(rules):
    """
    Filter @output, @export, @plot and @assert statements from the rules
    Args:
        rules (str): Rules received from server.
    Returns:
        Str: Rules without @output, @export and @plot statements.
    """
    filtered_rules = []

    for rule in rules.split('.'):
        if ('@output' not in rule) and ('@export' not in rule) and ('@plot' not in rule) and ('@assert' not in rule):
                filtered_rules.append(rule)

    return('.'.join(filtered_rules))


def filter_assert_statements(rules):
    """
    Filter @assert statements from the rules
    Args:
        rules (str): Rules received from server.
    Returns:
        Str: Rules without @assert statements.
    """
    filtered_rules = []

    for rule in rules.split('.'):
        if ('@assert' not in rule):
                filtered_rules.append(rule)

    return('.'.join(filtered_rules))


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


def export_results(engine,rules):
    """
    Export all csv files in the results folder
    Args:
        engine (NemoEngine): The instantiated nemo object. 
        rules (str): Rules received from server.
    """
    exports = re.findall(EXPORT_REGEX, rules)
    for export in exports:
        output_manager = NemoOutputManager('./results', gzip=False)
        file_path = f"./results/{export}.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        engine.write_result(export, output_manager)


def plot_results(self, engine):
    """
    Plot the element in the cell.
    Args:
        engine (NemoEngine): The instantiated nemo object. 
        self (Self@NemoKernel): global variable of class NemoKernel.
    """
    # Get plot results and convert it to dataframes
    results = get_results(self.plot_predicates, engine)
    dfs = convert_to_df(results)

    for key, df in dfs.items():
        plt.plot(df['Node 1'], df['Node 2'], marker='o', label=str(key))
        plt.legend()  # Show legend
        plt.savefig(self.current_cell_id)
    plt.close()


def handle_cell_removal(global_state, code):
    """
    Update the global state when the client remove the cell.
    Args:
        global_state (Dict): The current global state containing active cells.
        code (String): Cell removal request containing the list of currently active cells of removal. 
    Returns:
        dict: The global state containing only the existing cells on the frontend.
    """
    current_cells = ast.literal_eval(code.split(',', 1)[1]) # Extract list of active cells from the request
    filtered_global_state = {key: value for key, value in global_state.items() if key in current_cells}
    return filtered_global_state


def preprocess_assert(self, code):
    """
    Register expected output for later assertion execution.
    Args:
        self (object): This instance of kernel.
        code (String): The code containing @assert statement.
    Returns:
        dict: The collection of all expected outputs by predicates.
    """
    expected_outputs = {}
    assert_statements = re.findall(r'@assert\s*(.*?)\s*\.', code)

    for statement in assert_statements:
        statement = statement.split(' ', 1)

        try:
            statement_value = eval(statement[1].strip())
        except Exception as e:
            self.Error(f"Cannot parse expected output for {statement[0]}")
            continue

        expected_outputs[statement[0].strip()] = statement_value
    
    return expected_outputs


def execute_assert(self):
    """
    Compare assert (python) on expected and actual outputs.
    Args:
        self (object): This instance of kernel.
    """
    for key in self.assert_outputs:
        if key not in self.actual_outputs: raise ValueError(f"{key} is not defined")
        assert self.assert_outputs[key] == self.actual_outputs[key], f"{key} assertion failed"
        print(f"{key} assertion passed")
