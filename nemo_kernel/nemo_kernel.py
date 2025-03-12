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
        self.output_predicates = []
        self.export_predicates = []
        self.plot_predicates = []
        self.current_cell_id = ''
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
        self.current_cell_id = cell_id

        # Extract output predicates from the rules 
        self.output_predicates = re.findall(OUTPUT_REGEX, code)
        self.export_predicates = re.findall(EXPORT_REGEX, code)
        self.plot_predicates = re.findall(PLOT_REGEX, code)

        # Filter @output, @export and @plot statements from rules before recording to global_state if any
        rules_to_save = code
        if self.output_predicates or self.export_predicates or self.plot_predicates:
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
                dfs = convert_to_df(results)

                # Inject html to visualise dataframes on frontend
                output = "".join(
                    f"<details><summary><b>{key}</b></summary>{df.to_html(notebook=True)}</details><br>" 
                    for key, df in dfs.items()
                )

            if self.plot_predicates:
                output += f'<img src="{self.current_cell_id}.png"/>'

            self.output_predicates = []
            self.export_predicates = []
            self.plot_predicates = []

            # If there is no output, return without displaying any results
            if not output: return 

            return HTML(output)

        except Exception as error:
            # Remove error cell from global_state 
            self.global_state.pop(self.current_cell_id)
            return f"Error: {str(error)}"


    def repr(self, data):
        return repr(data)


def filter_statements(rules):
    """
    Filter @output, @export and @plot statements from the rules
    Args:
        rules (str): Rules received from server.
    Returns:
        Str: Rules without @output, @export and @plot statements.
    """
    filtered_rules = []

    for rule in rules.split('.'):
        if ('@output' not in rule) and ('@export' not in rule) and ('@plot' not in rule):
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


def plot_results(self,engine):
    """
    Plot the element in the cell
    Args:
        engine (NemoEngine): The instantiated nemo object. 
        self
    """
    # Get plot results and convert it to dataframes
    results = get_results(self.plot_predicates, engine)
    dfs = convert_to_df(results)

    for key, df in dfs.items():
        plt.plot(df['Node 1'], df['Node 2'], marker='o', label=str(key))
        plt.legend()  # Show legend
        plt.savefig(self.current_cell_id)
    plt.close()

if __name__ == '__main__':
    NemoKernel.run_as_main()
