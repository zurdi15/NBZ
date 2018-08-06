#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: <Zurdi>


from lib.lib_log_nbz import Logging
from data.natives import NATIVES
try:
    from parser.nbz_lexer import tokens  # Get the token map from the lexer
    import ply.yacc as yacc
except LookupError:
    logger = Logging()
    raise Exception("Dependencies not installed. Please run install.sh.")


def NBZParser(script, interactive=False):
    """Parser of the nbz-script

    This module converts the nbz-script into a structure of lists,
    ready to be executed by the core module. Each function of this module uses the docstring
    to define the parser rules. The rules are documented themselves.

    Args:
        script: path of the nbz-script
        interactive: flag to call this module into manual user mode or file mode (you can write sentences directly
                     or you can pass a nbz-script)
    Returns:
        A lists structure with all the nbz-script converted
        A dict mapping variables of the script and their values
    """

    # z_code structure
    z_code = []

    # z_code_vars dictionary
    z_code_vars = {}

    # Functions dictionary
    functions = NATIVES

    # Initial state
    def p_sent_list(p):
        """sent_list : sent_list sent
                     | sent
                     | empty"""
        if len(p) == 2:
            if p[1] is None:
                p[0] = []
            else:
                p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_sent(p):
        """sent : sent_func_def
                | sent_assign
                | sent_func SEMI"""
        p[0] = p[1]

    # Functions definition
    def p_sent_funcs_def(p):
        """sent_func_def : DEF ID LPAREN RPAREN LBRACE sent_list RBRACE"""
        functions[p[2]] = ''
        p[0] = ['def', p[2], p[6]]
        for sent in p[6]:
            z_code.pop()
        z_code.append(p[0])

    # Assign definitions
    def p_sent_assign_expr(p):
        """sent_assign : ID ASSIGN expr_type SEMI
                       | ID ASSIGN expr_arithm SEMI
                       | ID ASSIGN logic_list SEMI
                       | ID ASSIGN expr_list SEMI"""
        p[0] = ['assign', p[1], p[3]]
        z_code_vars[p[1]] = ''
        z_code.append(p[0])

    def p_sent_assign_func(p):
        """sent_assign : ID ASSIGN sent_func SEMI"""
        z_code.pop()
        p[0] = ['assign', p[1], p[3]]
        z_code_vars[p[1]] = ''
        z_code.append(p[0])

    # Function call expression
    def p_expr_funcs(p):
        """sent_func : ID LPAREN list RPAREN"""
        try:
            check = functions[p[1]]
            p[0] = ['func', p[1], p[3]]
            z_code.append(p[0])
        except LookupError:
            raise Exception('Undefined function "{function}" line {line}'.format(function=p[1],
                                                                                 line=p.lineno(1)))

    # List expressions
    def p_list_var(p):
        """list : list COMMA ID
                | list COMMA sent_func
                | sent_func
                | ID"""
        if len(p) == 2:
            if isinstance(p[1], str):
                try:
                    check = z_code_vars[p[1]]
                    p[0] = [['var', p[1]]]
                except LookupError:
                    raise Exception('Undefined variable "{variable}" line {line}'.format(variable=p[1],
                                                                                         line=p.lineno(1)))

            elif isinstance(p[1], list):
                try:
                    check = functions[p[1][1]]
                    p[0] = [p[1]]
                    z_code.pop()
                except LookupError:
                    raise Exception('Undefined function "{function}" line {line}'.format(function=p[1][1],
                                                                                         line=p.lineno(1)))

        else:
            p[0] = p[1]
            if isinstance(p[3], str):
                try:
                    check = z_code_vars[p[3]]
                    p[0].append(['var', p[3]])
                except LookupError:
                    raise Exception('Undefined variable "{variable}" line {line}'.format(variable=p[3],
                                                                                         line=p.lineno(1)))

            elif isinstance(p[3], list):
                try:
                    check = functions[p[3][1]]
                    p[0].append([p[3]])
                    z_code.pop()
                except LookupError:
                    raise Exception('Undefined function "{function}" line {line}'.format(function=p[3][1],
                                                                                         line=p.lineno(1)))

    def p_list_value(p):
        """list : list COMMA expr_type
                | expr_type
                | empty"""
        if len(p) == 2:
            if p[1] is None:
                p[0] = []
            else:
                p[0] = [['value', p[1]]]
        else:
            p[0] = p[1]
            p[0].append(['value', p[3]])

    def p_list_expression(p):
        """list : list COMMA expr_arithm
                | list COMMA logic_list
                | expr_arithm
                | logic_list"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[3])

    # Flow control expressions

    # For
    def p_sent_for_flow_int(p):
        """sent : FOR LPAREN for_valid_expr COMMA for_valid_expr COMMA for_valid_iter RPAREN LBRACE sent_list RBRACE
                | FOR LPAREN ID IN ID RPAREN LBRACE sent_list RBRACE"""
        if len(p) == 10:
            p[0] = ['for', p[3], p[5], p[8]]
            z_code_vars[p[3]] = ''
            for i in range(0, len(p[8])):
                z_code.pop()
            z_code.append(p[0])
        else:
            p[0] = ['for', p[3], p[5], p[7], p[10]]
            for i in range(0, len(p[10])):
                z_code.pop()
            z_code.append(p[0])

    def p_for_valid_expressions_num(p):
        """for_valid_expr : expr_num
                          | expr_arithm"""
        p[0] = p[1]

    def p_for_valid_iterators(p):
        """for_valid_iter : PLUS
                          | PLUSPLUS
                          | MINUS
                          | MINUSMINUS"""
        p[0] = p[1]

    # If / else
    def p_sent_if_flow(p):
        """sent : IF LPAREN logic_list RPAREN LBRACE sent_list RBRACE
                | IF LPAREN logic_list RPAREN LBRACE sent_list RBRACE elif_sent
                | IF LPAREN logic_list RPAREN LBRACE sent_list RBRACE ELSE LBRACE sent_list RBRACE
                | IF LPAREN logic_list RPAREN LBRACE sent_list RBRACE elif_sent ELSE LBRACE sent_list RBRACE"""
        if len(p) == 8:  # Only if
            p[0] = ['if', p[3], p[6]]
            for i in range(0, len(p[6])):
                z_code.pop()
            z_code.append(p[0])
        elif len(p) == 9:  # If + elif
            p[0] = ['if', p[3], p[6], p[8]]
            for i in range(0, len(p[6])):
                z_code.pop()
            z_code.append(p[0])
        elif len(p) == 12:  # If + else
            p[0] = ['if', p[3], p[6], [['else'] + [p[10]]]]
            for i in range(0, len(p[6])):
                z_code.pop()
            for i in range(0, len(p[10])):
                z_code.pop()
            z_code.append(p[0])
        elif len(p) == 13:  # If + elif + else
            if p[8]:
                p[0] = ['if', p[3], p[6], p[8], [['else'] + [p[11]]]]
            else:
                p[0] = ['if', p[3], p[6], [['else'] + [p[11]]]]
            for i in range(0, len(p[6])):
                z_code.pop()
            for i in range(0, len(p[11])):
                z_code.pop()
            z_code.append(p[0])

    # Elif
    def p_sent_elif_flow(p):
        """elif_sent : ELIF LPAREN logic_list RPAREN LBRACE sent_list RBRACE elif_sent
                     | empty"""
        if len(p) > 2:
            for i in range(0, len(p[6])):
                z_code.pop()
            if p[8]:
                p[0] = [['elif', p[3], p[6]], p[8][0]]
            else:
                p[0] = [['elif', p[3], p[6]]]

    # While
    def p_sent_while_flow(p):
        """sent : WHILE LPAREN logic_list RPAREN LBRACE sent_list RBRACE"""
        p[0] = ['while', p[3], p[6]]
        for i in range(0, len(p[6])):
            z_code.pop()
        z_code.append(p[0])

    # Logic list
    def p_group_logic_list(p):
        """logic_list : LPAREN logic_list RPAREN"""
        p[0] = p[2]

    def p_logic_list(p):
        """logic_list : logic_list AND logic_list
                      | logic_list OR logic_list
                      | expr_bool"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            if p[2] == 'and':
                p[0] = ['boolean', p[1], p[3], 'and']
            elif p[2] == 'or':
                p[0] = ['boolean', p[1], p[3], 'or']

    # Boolean expressions
    def p_expr_logical(p):
        """expr_bool : expr_bool EQ expr_bool
                     | expr_bool LT expr_bool
                     | expr_bool LET expr_bool
                     | expr_bool GT expr_bool
                     | expr_bool GET expr_bool
                     | expr_bool DIFF expr_bool
                     | NOT expr_bool"""
        if p[2] == '==':
            p[0] = ['boolean', p[1], p[3], '==']
        elif p[2] == '<':
            p[0] = ['boolean', p[1], p[3], '<']
        elif p[2] == '<=':
            p[0] = ['boolean', p[1], p[3], '<=']
        elif p[2] == '>':
            p[0] = ['boolean', p[1], p[3], '>']
        elif p[2] == '>=':
            p[0] = ['boolean', p[1], p[3], '>=']
        elif p[2] == '!=':
            p[0] = ['boolean', p[1], p[3], '!=']
        else:
            p[0] = ['boolean', p[1], p[1], 'not']

    def p_logic_valid_var(p):
        """expr_bool : sent_func"""
        try:
            check = functions[p[1][1]]
            z_code.pop()
            p[0] = p[1]
        except LookupError:
            raise Exception('Undefined function "{function}" line {line}'.format(function=p[1][1],
                                                                                 line=p.lineno(1)))

    def p_logic_valid_type(p):
        """expr_bool : expr_type
                     | expr_arithm"""
        p[0] = p[1]

    # Arithmethic expressions
    def p_group_expr_arithmethic(p):
        """expr_arithm : LPAREN expr_arithm RPAREN"""
        p[0] = p[2]

    def p_expr_aritmethic(p):
        """expr_arithm : expr_arithm PLUS expr_arithm
                       | expr_arithm MINUS expr_arithm
                       | expr_arithm MULTIPLY expr_arithm
                       | expr_arithm DIVIDE expr_arithm
                       | MINUS expr_arithm"""
        if p[2] == '+':
            p[0] = ['arithm', p[1], p[3], '+']
        elif p[2] == '-':
            p[0] = ['arithm', p[1], p[3], '-']
        elif p[2] == '*':
            p[0] = ['arithm', p[1], p[3], '*']
        elif p[2] == '/':
            p[0] = ['arithm', p[1], p[3], '/']
        elif p[1] == '-':
            p[0] = ['arithm', p[2], -1, '*']

    def p_arithm_valid_var(p):
        """expr_arithm : ID
                       | sent_func"""
        if isinstance(p[1], str):
            try:
                check = z_code_vars[p[1]]
                p[0] = ['var', p[1]]
            except LookupError:
                raise Exception('Undefined variable "{variable}" line {line}'.format(variable=p[1],
                                                                                     line=p.lineno(1)))

        elif isinstance(p[1], list):
            try:
                check = functions[p[1][1]]
                z_code.pop()
                p[0] = p[1]
            except LookupError:
                raise Exception('Undefined function "{function}" line {line}'.format(function=p[1][1],
                                                                                     line=p.lineno(1)))

    def p_arithm_valid_num(p):
        """expr_arithm : expr_type"""
        p[0] = p[1]

    # Type definitions
    def p_sent_index_list(p):
        """sent_func : sent_index_list"""
        p[0] = p[1]

    def p_index_list_var(p):
        """sent_index_list : sent_index_list LBRACKET ID RBRACKET
                           | ID LBRACKET ID RBRACKET"""
        if not isinstance(p[1], list):
            try:
                check = z_code_vars[p[1]]
            except LookupError:
                raise Exception('Undefined list "{list}" line {line}'.format(list=p[1],
                                                                             line=p.lineno(1)))

            try:
                check = z_code_vars[p[3]]
            except LookupError:
                raise Exception('Undefined variable "{variable}" line {line}'.format(variable=p[3],
                                                                                     line=p.lineno(1)))

            p[0] = ['func', 'get_element_list', [['var', p[1]], ['var', p[3]]]]
            z_code.append(p[0])
        else:
            try:
                check = z_code_vars[p[3]]
            except LookupError:
                raise Exception('Undefined variable "{variable}" line {line}'.format(variable=p[3],
                                                                                     line=p.lineno(1)))

            p[0] = ['func', 'get_element_list', [p[1], ['var', p[3]]]]

    def p_index_list_value(p):
        """sent_index_list : sent_index_list LBRACKET INTEGER RBRACKET
                           | ID LBRACKET INTEGER RBRACKET"""
        if not isinstance(p[1], list):
            try:
                check = z_code_vars[p[1]]
                p[0] = ['func', 'get_element_list', [['var', p[1]], p[3]]]
                z_code.append(p[0])
            except LookupError:
                raise Exception('Undefined list "{list}" line {line}'.format(list=p[1],
                                                                             line=p.lineno(1)))

        else:
            p[0] = ['func', 'get_element_list', [p[1], p[3]]]

    def p_expr_list(p):
        """expr_list : LBRACKET expr_inside_list RBRACKET"""
        p[0] = p[2]

    def p_list_expr_inside_list(p):
        """expr_inside_list : expr_inside_list COMMA expr_type
                            | expr_inside_list COMMA expr_bool
                            | expr_type
                            | expr_bool
                            | empty"""
        if len(p) == 2:
            if p[1] is None:
                p[0] = []
            else:
                p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_expr_type(p):
        """expr_type : expr_num
                     | expr_string"""
        p[0] = p[1]

    def p_expr_bool_true(p):
        """expr_bool : TRUE"""
        p[0] = True

    def p_expr_bool_false(p):
        """expr_bool : FALSE"""
        p[0] = False

    def p_expr_number(p):
        """expr_num : FLOAT
                    | INTEGER"""
        p[0] = p[1]

    def p_expr_string(p):
        """expr_string : STRING"""
        p[0] = p[1]

    # Empty rule
    def p_empty(p):
        """empty :"""
        p[0] = None

    # Error rule for syntax errors
    def p_error(p):
        if p is not None:
            raise Exception('Illegal token: "{token}" at line: {line}'.format(token=p.value,
                                                                              line=p.lineno))

        else:
            raise Exception('General error: error at the end of the script.\n'
                            'Probably one structure is not built properly.')

    # Build the parser
    try:
        parser = yacc.yacc(debug=1)
    except Exception as e:
        raise Exception(e)
    if not interactive:
        data = ''
        with open(script, 'r') as s:
            for line in s:
                data += line
                if not line: continue
        try:
            parser.parse(data)
        except EOFError:
            raise Exception('General error parsing {script}'.format(script=script))
        return z_code, z_code_vars
    else:
        while True:
            try:
                s = raw_input('input(sentence) > ')
            except NotImplementedError:
                s = input('input(sentence) > ')
            if not s:
                continue
            result = parser.parse(s)
            print(result)


# Interactive mode
if __name__ == "__main__":
    NBZParser('interactive', True)
