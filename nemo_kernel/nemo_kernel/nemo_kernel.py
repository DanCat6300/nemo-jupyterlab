import ast
from metakernel import MetaKernel
from nmo_python import load_string, NemoEngine, NemoOutputManager
from IPython.display import HTML
import re
import pandas as pd
import os
import matplotlib.pyplot as plt
import networkx as nx
from .utility import result_utils as rlt
from .utility import code_utils as cd

__version__ = "0.1"
BRACKET_REGEX = r'^<[^>]*>$'
OUTPUT_REGEX = r"(?<![\s%])\s*@output\s+(\S+)\s*\."
EXPORT_REGEX = r"@export\s+(\w+)\s*:- "
Line_REGEX = r"(?<![\s%])\s*@line\s+(\S+)\s*\."
Bar_REGEX = r"(?<![\s%])\s*@bar\s+(\S+)\s*\."
Scatter_REGEX = r"(?<![\s%])\s*@scatter\s+(\S+)\s*\."
Shape_REGEX = r"(?<![\s%])\s*@shape\s+(\S+)\s*\."
Graph_REGEX = r"(?<![\s%])\s*@graph\s+(\S+)\s*\."


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
        self.line_predicates = []
        self.bar_predicates = []
        self.scatter_predicates = []
        self.shape_predicates = []
        self.graph_predicates = []
        self.current_cell_id = ''
        self.total_fig = 0
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
        code = cd.strip_comments(code)
        if 'cell_removal_event' in code:
            self.global_state = handle_cell_removal(self.global_state, code)
            return

        self.current_cell_id = cell_id

        # Extract output predicates from the rules 
        self.extract_predicates(code)

        # Filter @output, @export, @bar, @scatter, @graph, @shape and @line statements from rules before recording to global_state if any
        rules_to_save = cd.filter_statements(code, to_save=True)

        # Record rules into global_state without @output, @export, @bar, @scatter, @graph, @shape and @line
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
            modified_rules = re.sub(r'@line', '@output', rules)
            modified_rules = re.sub(r'@bar', '@output', modified_rules)
            modified_rules = re.sub(r'@scatter', '@output', modified_rules)
            modified_rules = re.sub(r'@shape', '@output', modified_rules)
            modified_rules = re.sub(r'@graph', '@output', modified_rules)
            output = ""
            if '@assert' in modified_rules:
                modified_rules = cd.filter_statements(modified_rules, to_save=False)

            # Create a nemo engine and reason on rules
            engine = NemoEngine(load_string(modified_rules))
            engine.reason()

            # Handle @export statement if any
            if self.export_predicates:
                export_results(engine, rules)

            # If line statement exists, plot the results:
            if self.line_predicates:
                plot_results(self, engine, 'line') 
            
            # If bar statement exists, plot the results:
            if self.bar_predicates:
                plot_results(self, engine, 'bar') 
            
            # If scatter statement exists, plot the results:
            if self.scatter_predicates:
                plot_results(self, engine, 'scatter') 
            
            # If shape statement exists, plot the results:
            if self.shape_predicates:
                plot_results(self, engine, 'shape') 

            # If graph statement exists, plot the results:
            if self.graph_predicates:
                plot_results(self, engine, 'graph') 

            # Handle @output statement
            if self.output_predicates: 
                # Get results and convert it to dataframes
                results = rlt.get_results(self.output_predicates, engine)
                self.actual_outputs.update(results)

                dfs = rlt.convert_to_df(results)

                # Inject html to visualise dataframes on frontend
                output = "".join(
                    f"<details><summary><b>{key}</b></summary>{df.to_html(notebook=True)}</details><br>" 
                    for key, df in dfs.items()
                )

            #plot images in the total number of figures
            for item in range(self.total_fig):
                output += f'<img src="{self.current_cell_id}{item}.png"/>'                

            # Perform assertion
            if '@assert' in rules:
                self.assert_outputs = self.preprocess_assert(rules, engine)
                self.execute_assert()

            self.flush_predicates()

            # If there is no output, return without displaying any results
            if not output: return 

            return HTML(output)

        except Exception as error:
            # Remove error cell from global_state and clear cache
            self.global_state.pop(self.current_cell_id)
            self.flush_predicates()

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
    
    def extract_predicates(self, code):
        """
        Find statements for tasks and extract predicates
        Args:
            code (str): The rules from the current cell
        """
        self.output_predicates = re.findall(OUTPUT_REGEX, code)
        self.export_predicates = re.findall(EXPORT_REGEX, code)
        self.line_predicates = re.findall(Line_REGEX, code)
        self.bar_predicates = re.findall(Bar_REGEX, code)
        self.scatter_predicates = re.findall(Scatter_REGEX, code)
        self.shape_predicates = re.findall(Shape_REGEX, code)
        self.graph_predicates = re.findall(Graph_REGEX, code)
        
        

    def flush_predicates(self):
        """
        Clean up predicates for the next execution
        """
        self.output_predicates = []
        self.export_predicates = []
        self.assert_outputs = {}
        self.line_predicates = []
        self.bar_predicates = []
        self.scatter_predicates = []
        self.shape_predicates = []
        self.graph_predicates = []
        self.total_fig = 0
    
    def preprocess_assert(self, code, engine):
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
                # Parse the value into a list
                statement_value = eval(statement[1].strip())
                if isinstance(statement_value, list):
                    expected_outputs[statement[0].strip()] = statement_value
                else: raise Exception

            except Exception:
                try:
                    # If not a list, try to get value from imported predicates
                    imported = rlt.get_results([statement[1]], engine)[statement[1]]
                    if not imported: raise Exception
                    expected_outputs[statement[0].strip()] = imported

                except Exception as e:
                    self.Error(f"Error: Cannot parse expected value for {statement[0]}")
                    continue
        
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

# def filter_statements(rules):
#     """
#     Filter @output, @export, @bar, @scatter, @graph, @shape and @line statements from the rules
#     Args:
#         rules (str): Rules received from server.
#     Returns:
#         Str: Rules without @output, @export, @bar, @scatter, @graph, @shape and @line statements.
#     """
#     filtered_rules = []

#     for rule in rules.split('.'):
#         if ('@output' not in rule) and ('@export' not in rule) and ('@line' not in rule) and ('@bar' not in rule) and ('@scatter' not in rule) and ('@graph' not in rule) and ('@shape' not in rule):
#                 filtered_rules.append(rule)

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


def plot_results(self, engine, plot_type):
    """
    plot the element in the cell.
    Args:
        engine (NemoEngine): The instantiated nemo object. 
        self (Self@NemoKernel): global variable of class NemoKernel.
        plot_type (String): the type of plot  
    """
    if plot_type == 'line':
        # Get line results and convert it to dataframes
        results = rlt.get_results(self.line_predicates, engine)
        dfs = rlt.convert_to_df(results)
        for key, df in dfs.items():
            plt.plot(df['Node 1'], df['Node 2'], marker='o', label=str(key))

    if plot_type == 'bar':
        results = rlt.get_results(self.bar_predicates, engine)
        dfs = rlt.convert_to_df(results)
        for key, df in dfs.items():
            plt.bar(df['Node 1'], df['Node 2'], label=str(key))

    if plot_type == 'scatter':
        results = rlt.get_results(self.scatter_predicates, engine)
        dfs = rlt.convert_to_df(results)
        for key, df in dfs.items():
            plt.scatter(df['Node 1'], df['Node 2'], label=str(key))
    
    if plot_type == 'shape':
        results = rlt.get_results(self.shape_predicates, engine)
        dfs = rlt.convert_to_df(results)
        for key, df in dfs.items():
            plt.plot(df['Node 1'], df['Node 2'], marker='o', label=str(key))
            plt.fill_between(df['Node 1'], df['Node 2'])

    if plot_type == 'graph':
        results = rlt.get_results(self.graph_predicates, engine)
        dfs = rlt.convert_to_df(results)
        G = nx.MultiDiGraph()
        for key, df in dfs.items():
            G.add_nodes_from(df['Node 1'])        
            # Add edges with key as an attribute (ensuring multiple edges)
            for i in range(len(df['Node 1'])):
                G.add_edge(df['Node 1'][i], df['Node 2'][i], label=key)  # Store key as label
            plt.figure(figsize=(8,6))
            pos = nx.shell_layout(G)  # Use shell layout for better spacing
            nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=12)
            edge_labels = {}
            for u, v, k, d in G.edges(keys=True, data=True):
                if (u, v) in edge_labels:
                    edge_labels[(u, v)] += "\n" + d["label"]  # Append new label with newline
                else:
                    edge_labels[(u, v)] = d["label"]  # First label
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='gray', font_size=10, label_pos=0.5)


    plt.legend()  # Show legend
    plt.savefig(f'{self.current_cell_id}{self.total_fig}')
    self.total_fig = self.total_fig + 1
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
