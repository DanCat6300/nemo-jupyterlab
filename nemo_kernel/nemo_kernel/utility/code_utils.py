def strip_comments(code: str):
    lines = code.splitlines()
    filtered_code = []

    for line in lines:
        print(line)
        if not line.strip().startswith('%') and '%' in line:
            line = line.split('%', 1)
            filtered_code.append(line[0].strip())
        elif not line.strip().startswith('%'):
            filtered_code.append(line.strip())

    return(''.join(filtered_code))


def filter_statements(rules, to_save=False):
    """
    Filter @output, @export, @plot and @assert statements from the rules
    Args:
        rules (str): Rules received from server.
    Returns:
        Str: Rules without @output, @export and @plot statements.
    """
    filtered_rules = []
    statements = ['@output', '@export', '@plot', '@assert']

    for rule in rules.split('.'):
        if to_save and not any(statement in rule for statement in statements):
            filtered_rules.append(rule)
        elif not to_save and '@assert' not in rule:
            filtered_rules.append(rule)

    return('.'.join(filtered_rules))