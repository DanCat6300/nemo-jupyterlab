import re
import pandas as pd


BRACKET_REGEX = r'^<[^>]*>$'


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
