import sys, re
from scanner import Scanner

# Provides order of precedence for each set of operators
PRECEDENCE = {
    "||": 1,
    "&&": 2,
    "==": 3, "!=": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6
}

class ParseTreeNode:
    def __init__(self, label, line=None):
        self.label = label
        self.line = line
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def print_tree(self, depth=0):
        indentation = "\t" * depth

        if self.line is not None:
            print(f"{self.line} \t {indentation}{self.label}")
        else:
            print(f"\t {indentation}{self.label}")

        for child in self.children:
            child.print_tree(depth + 1)

# Initialize Parser class to keep track of tokens list, source lines, current list position, and any error tokens
class Parser:
    def __init__(self, tokens, source_lines):
        self.tokens = tokens
        self.source_lines = source_lines
        self.position = 0
        self.error_token = None
        self.root = ParseTreeNode("Program:")

    # Begin parsing the program declaration by declaration until the end is reached
    def parse_program(self):
        while self.current_token() is not None:
            declaration = self.parse_declaration()
            if declaration is not None:
                self.root.add_child(declaration)
        print("Parsing completed successfully.")
        return self.root

    # Distinguish between function and variable declarations
    def parse_declaration(self):
        # Define valid declaration types and gather current token
        valid_types = {"T_Void", "T_Int", "T_Double", "T_String", "T_Bool"}
        token = self.current_token()

        # Check if the token exists and is a valid declaration type
        if token is None or token.type not in valid_types:
            self.syntax_error()

        line = token.line

        # Consume token
        self.advance_token()

        # Check identifier to match correctly then consume it
        identifier = self.current_token()

        if identifier is not None and identifier.type == "T_IDENTIFIER":
            name_token = self.advance_token()

            if self.current_token() is not None and self.current_token().value == "(":
                declaration = ParseTreeNode("FnDecl:", line)
                declaration.add_child(ParseTreeNode(f"(return type) Type: {token.value}"))
                declaration.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

                self.parse_function(declaration)

            else:
                declaration = ParseTreeNode("VarDecl:", line)
                declaration.add_child(ParseTreeNode(f"Type: {token.value}"))
                declaration.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

                while self.current_token() is not None and self.current_token().value == ",":
                    self.advance_token()

                    name_token = self.match_token("T_IDENTIFIER")
                    if name_token is None:
                        self.syntax_error()

                    declaration.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

                self.expect_value(";")
        else:
            self.syntax_error()

        return declaration

    # Parse function declaration
    def parse_function(self, declaration):
        # Consume opening parenthesis
        self.advance_token()

        # Parse parameters
        if self.current_token() is not None and self.current_token().value != ")":
            while True:
                type_token = self.current_token()

                # Check for valid parameter type
                if type_token is None or type_token.type not in {
                    "T_Int", "T_Double", "T_String", "T_Bool"
                }:
                    self.syntax_error()

                self.advance_token()

                # Check for parameter identifier
                name_token = self.match_token("T_IDENTIFIER")

                if name_token is None:
                    self.syntax_error()

                # Create parameter node
                parameter = ParseTreeNode("(formals) VarDecl:")
                parameter.add_child(ParseTreeNode(f"Type: {type_token.value}"))
                parameter.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

                declaration.add_child(parameter)

                # Check for another parameter
                if self.current_token() is None or self.current_token().value != ",":
                    break

                self.advance_token()

        # Check for closing parenthesis
        if self.current_token() is None or self.current_token().value != ")":
            self.syntax_error()

        self.advance_token()

        # Parse function body
        body = self.parse_block()
        body.label = "(body) StmtBlock:"
        declaration.add_child(body)

    # Parse function body enclosed in curly braces
    def parse_block(self):
        # Create the statement block node
        block = ParseTreeNode("StmtBlock:")

        # Check for opening brace, then consume it
        if self.current_token() is None or self.current_token().value != "{":
            self.syntax_error()
        self.advance_token()

        # Parse local variable declarations
        while self.current_token() is not None and self.current_token().type in {
            "T_Int", "T_Double", "T_String", "T_Bool"
        }:
            declaration = self.parse_variable_declaration()
            block.add_child(declaration)

        # Parse statements until closing brace is reached
        while self.current_token() is not None and self.current_token().value != "}":
            statement = self.parse_statement()
            if statement is not None:
                block.add_child(statement)

        # Check for missing closing brace, then consume it
        if self.current_token() is None:
            self.syntax_error()
        self.advance_token()

        return block

    # Parse local variable declarations
    def parse_variable_declaration(self):
        # Consume type token found in parse_block
        type_token = self.current_token()
        self.advance_token()

        # Create the variable declaration node
        declaration = ParseTreeNode("VarDecl:", type_token.line)
        declaration.add_child(ParseTreeNode(f"Type: {type_token.value}"))

        # Identify one or multiple variables
        while True:
            # Check for correct identifier type
            name_token = self.match_token("T_IDENTIFIER")

            if name_token is None:
                self.syntax_error()

            declaration.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

            # Check for array declaration
            if self.current_token() is not None and self.current_token().value == "[":
                self.advance_token()

                # Require integer inside array brackets and closing bracket
                if not self.match_token("T_IntConstant"):
                    self.syntax_error()
                self.expect_value("]")

            # Check for another variable indicated by a comma
            if self.current_token() is None or self.current_token().value != ",":
                break
            self.advance_token()

        # Check for closing semicolon
        self.expect_value(";")

        return declaration

    # Parse different kinds of statements
    def parse_statement(self):
        # Find current token to determine what kind of statement it is
        token = self.current_token()

        # Statement expected, but no token
        if token is None:
            self.syntax_error()

        # Parse block statement based on opening curly brace
        if token.value == "{":
            return self.parse_block()

        # Parse If statement, indicated by token type
        if token.type == "T_If":
            return self.parse_if()

        # Parse While statement, indicated by token type
        if token.type == "T_While":
            return self.parse_while()

        # Parse For statement, indicated by token type
        if token.type == "T_For":
            return self.parse_for()

        # Consume break and continue statements, indicated by token type
        if token.type in {"T_Break", "T_Continue"}:
            if token.type == "T_Break":
                statement = ParseTreeNode("BreakStmt:", token.line)
            else:
                statement = ParseTreeNode("ContinueStmt:", token.line)

            self.advance_token()
            self.expect_value(";")

            return statement

        # Parse return statements, indicated by token type
        if token.type == "T_Return":
            # Create the return statement node
            statement = ParseTreeNode("ReturnStmt:", token.line)

            # Consume return keyword
            self.advance_token()

            # Parse return expression
            if self.current_token() is not None and self.current_token().value != ";":
                expression = self.parse_expression()
                if expression is not None:
                    statement.add_child(expression)

            # Consume return semicolon
            self.expect_value(";")
            return statement

        # Parse print statements, indicated by token type
        if token.type == "T_Print":
            # Create the print statement node
            statement = ParseTreeNode("PrintStmt:", token.line)

            # Consume the print keyword
            self.advance_token()
            arguments = self.parse_call_arguments()
            statement.add_child(arguments)
            self.expect_value(";")

            return statement

        # Parse identifier statements, indicated by token type
        if token.type == "T_IDENTIFIER":
            # Consume keyword
            name_token = self.advance_token()

            # Parse function call
            if self.current_token() is not None and self.current_token().value == "(":
                self.parse_call_arguments()
                self.expect_value(";")
                return

            # Create the assignment expression node
            statement = ParseTreeNode("AssignExpr:", token.line)

            # Create the field access node
            field_access = ParseTreeNode("FieldAccess:")
            field_access.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))

            # Check for array
            if self.current_token() is not None and self.current_token().value == "[":
                self.advance_token()
                self.parse_expression()
                self.expect_value("]")

            statement.add_child(field_access)

            # Check for assignment operator, then consume it
            if self.current_token() is None or self.current_token().value not in {"=", "+", "-"}:
                self.syntax_error()
            operator = self.advance_token().value

            # Check for compound operation
            if operator in {"+", "-"}:
                if self.current_token() is None or self.current_token().value != "=":
                    self.syntax_error()

                self.advance_token()
                operator += "="

            # Add the assignment operator node
            statement.add_child(ParseTreeNode(f"Operator: {operator}"))

            # Parse rest of expression
            expression = self.parse_expression()
            if expression is not None:
                statement.add_child(expression)
            self.expect_value(";")
            return statement

        self.syntax_error()

    # Parse If statements
    def parse_if(self):
        token = self.current_token()

        # Create the if statement node
        statement = ParseTreeNode("IfStmt:", token.line)

        # Consume keyword
        self.advance_token()

        # Require opening and closing parenthesis, and parse expression inside
        self.expect_value("(")
        condition = self.parse_expression()
        if condition is not None:
            statement.add_child(condition)
        self.expect_value(")")

        # Parse body
        if self.current_token() is not None and self.current_token().value == "{":
            body = self.parse_block()
        else:
            body = ParseTreeNode("StmtBlock:")
            body.add_child(self.parse_statement())
        statement.add_child(body)

        # Check for else statement and parse it
        if self.current_token() is not None and self.current_token().type == "T_Else":
            self.advance_token()

            if self.current_token() is not None and self.current_token().value == "{":
                else_body = self.parse_block()
            else:
                else_body = ParseTreeNode("StmtBlock:")
                else_body.add_child(self.parse_statement())

            statement.add_child(else_body)

        return statement

    # Parse While statements
    def parse_while(self):
        token = self.current_token()

        # Create the while statement node
        statement = ParseTreeNode("WhileStmt:", token.line)

        # Consume keyword
        self.advance_token()

        # Check for opening and closing parenthesis, and parse expression inside
        self.expect_value("(")
        condition = self.parse_expression()
        if condition is not None:
            statement.add_child(condition)
        self.expect_value(")")

        # Parse function body
        if self.current_token() is not None and self.current_token().value == "{":
            body = self.parse_block()
        else:
            body = ParseTreeNode("StmtBlock:")
            body.add_child(self.parse_statement())

        statement.add_child(body)

        return statement

    # Parse For statements
    def parse_for(self):
        token = self.current_token()

        # Create the for statement node
        statement = ParseTreeNode("ForStmt:", token.line)

        # Consume keyword and opening parenthesis
        self.advance_token()
        self.expect_value("(")

        # Check for identifier
        name_token = self.match_token("T_IDENTIFIER")
        if name_token is None:
            self.syntax_error()

        # Create assignment expression
        assignment = ParseTreeNode("AssignExpr:", name_token.line)

        field_access = ParseTreeNode("FieldAccess:")
        field_access.add_child(ParseTreeNode(f"Identifier: {name_token.value}", name_token.line))
        assignment.add_child(field_access)

        # Require equals sign and comma for proper statement declaration
        self.expect_value("=")
        assignment.add_child(ParseTreeNode("Operator: ="))

        expression = self.parse_expression()
        if expression is not None:
            assignment.add_child(expression)
        statement.add_child(assignment)

        self.expect_value(";")
        condition = self.parse_expression()
        if condition is not None:
            statement.add_child(condition)

        self.expect_value(";")
        name_token = self.match_token("T_IDENTIFIER")
        if name_token is None:
            self.syntax_error()

        update = ParseTreeNode("AssignExpr:", name_token.line)

        field_access = ParseTreeNode("FieldAccess:")
        field_access.add_child((ParseTreeNode(f"Identifier: {name_token.value}", name_token.line)))
        update.add_child(field_access)

        if self.current_token() is None or self.current_token().value not in {"=", "+", "-"}:
            self.syntax_error()

        operator = self.advance_token().value

        if operator in {"+", "-"}:
            if self.current_token() is None or self.current_token().value != "=":
                self.syntax_error()
            self.advance_token()
            operator += "="

        update.add_child(ParseTreeNode(f"Operator: {operator}"))

        expression = self.parse_expression()
        if expression is not None:
            update.add_child(expression)

        statement.add_child(update)

        self.expect_value(")")

        # Parse function body
        body = self.parse_block()
        statement.add_child(body)

        return statement

    # Parse expression statements
    def parse_expression(self, min_precedence=1):
        # Parse the first operand
        left = self.parse_unary()

        # Parse one or more operators
        while self.current_token() is not None:
            # Match operator with precedence value
            operator_token = self.current_token()
            operator = operator_token.value
            precedence = PRECEDENCE.get(operator, 0)

            # Decide if precedence meets current precedence level
            if precedence < min_precedence:
                break

            # Consume operator and use recursion for parsing next level of precedence
            self.advance_token()
            right = self.parse_expression(precedence + 1)

            # Find expression type
            if operator in {"&&", "||"}:
                label = "LogicalExpr:"
            elif operator in {"==", "!="}:
                label = "EqualityExpr:"
            elif operator in {"<", "<=", ">", ">="}:
                label = "RelationalExpr:"
            else:
                label = "ArithmeticExpr:"

            # Create the expression node
            expression = ParseTreeNode(label, operator_token.line)

            # Add left side
            if left is not None:
                expression.add_child(left)

            # Add operator
            expression.add_child(ParseTreeNode(f"Operator: {operator}"))

            # Add right side
            if right is not None:
                expression.add_child(right)

            left = expression

        return left

    # Parse unary operators
    def parse_unary(self):
        token = self.current_token()

        # Check for operators in front of operand to consume and recursively parse, otherwise parse primary expression
        if token is not None and token.value in {"-", "!"}:
            self.advance_token()
            operand = self.parse_unary()

            # Create the unary expression node
            expression = ParseTreeNode("UnaryExpr:", token.line)
            expression.add_child(ParseTreeNode(f"Operator: {token.value}"))

            if operand is not None:
                expression.add_child(operand)

            return expression
        else:
            return self.parse_primary()

    # Parse primary expressions
    def parse_primary(self):
        # Consume current token
        token = self.current_token()

        if token is None:
            self.syntax_error()

        # Handle expressions within parenthesis
        if token.value == "(":
            self.advance_token()
            expression = self.parse_expression()
            self.expect_value(")")
            return expression

        # Handle constant values
        if token.type in {"T_IntConstant", "T_BoolConstant", "T_StringConstant"}:
            self.advance_token()
            constant = ParseTreeNode(f"Constant: {token.value}", token.line)
            return constant

        # Handle identifiers and print statements
        if token.type in {"T_IDENTIFIER", "T_Print"}:
            self.advance_token()

            # Check for array
            if self.current_token() is not None and self.current_token().value == "[":
                field_access = ParseTreeNode("FieldAccess:", token.line)
                field_access.add_child(ParseTreeNode(f"Identifier: {token.value}", token.line))

                self.advance_token()
                index = self.parse_expression()
                field_access.add_child(index)
                self.expect_value("]")

                return field_access

            # Handle function calls
            if self.current_token() is not None and self.current_token().value == "(":
                call = ParseTreeNode(f"Call: {token.value}", token.line)
                arguments = self.parse_call_arguments()
                call.add_child(arguments)
                return call

            field_access = ParseTreeNode("FieldAccess:", token.line)
            field_access.add_child(ParseTreeNode(f"Identifier: {token.value}", token.line))

            return field_access

        self.syntax_error()

    # Parse argument list of function calls
    def parse_call_arguments(self):
        # Create the argument list node
        arguments = ParseTreeNode("(args)")

        # Consume opening parenthesis
        self.expect_value("(")

        # Check if arguments exist
        if self.current_token() is not None and self.current_token().value != ")":
            # Parse first argument
            expression = self.parse_expression()

            if expression is not None:
                arguments.add_child(expression)

            # Parse additional arguments
            while self.current_token() is not None and self.current_token().value == ",":
                self.advance_token()
                expression = self.parse_expression()

                if expression is not None:
                    arguments.add_child(expression)

        # Consume closing parenthesis
        self.expect_value(")")

        return arguments

    # Check token value type, then consume it
    def expect_value(self, expected_value):
        token = self.current_token()

        if token is None or token.value != expected_value:
            self.syntax_error()

        return self.advance_token()

    # Check source lines for malformed numbers
    def find_malformed_number(self, line_number):
        # Retrieve source lines and search
        line = self.source_lines[line_number - 1]
        match = re.search(r"\b\d+(?:\.\d+){2,}\b", line)

        # Return the starting column and length of the final numeric segment
        if match:
            parts = match.group().split(".")
            start_column = match.start() + len(".".join(parts[:-1])) + 1
            return start_column, len(parts[-1])

        return None

    # Return the token at the current position
    def current_token(self):
        # Check if current position is within token list before returning the token
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        # Return None if current position is beyond the token list
        return None

    # Move forward by one token and return the consumed token
    def advance_token(self):
        token = self.current_token()

        if token is not None:
            self.position += 1

        return token

    # Consume a token only if it matches its expected type
    def match_token(self, expected_type):
        token = self.current_token()

        if token is not None and token.type == expected_type:
            self.advance_token()
            return token

        return None

    # Show error messages
    def report_syntax_error(self):
        # Error token
        token = self.error_token or self.current_token()

        if token is None:
            # No error position located
            if not self.tokens:
                print("*** syntax error")
                return

            # Determine location
            token = self.tokens[-1]
            line_number = token.line
            column = token.end_column + 1
            width = 1
        # Use error token
        else:
            line_number = token.line
            column = token.start_column
            width = token.end_column - token.start_column + 1

        # Check for malformed number
        malformed_number = self.find_malformed_number(line_number)

        if malformed_number:
            column, width = malformed_number

        # Find source line
        source_line = self.source_lines[line_number - 1].rstrip("\r\n")

        # Format and print error message
        print(f"*** Error line {line_number}.")
        print(source_line)
        print(" " * column + "^" * width)
        print("*** syntax error")

    # Trigger syntax error
    def syntax_error(self):
        self.error_token = self.current_token()
        raise SyntaxError("Syntax error")

def main():
    if len(sys.argv) != 2:
        print("Example usage: python parser.py inputfile.decaf")
        return

    filename = sys.argv[1]

    scanner = Scanner(filename)
    scanner.scan_file()

    with open(filename, "r") as file:
        source_lines = file.readlines()

    parser = Parser(scanner.tokens, source_lines)

    try:
        parser.parse_program()
        parser.root.print_tree()
    except SyntaxError:
        parser.report_syntax_error()

if __name__ == "__main__":
    main()