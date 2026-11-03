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

# Initialize Parser class to keep track of tokens list, source lines, current list position, and any error tokens
class Parser:
    def __init__(self, tokens, source_lines):
        self.tokens = tokens
        self.source_lines = source_lines
        self.position = 0
        self.error_token = None

    # Begin parsing the program declaration by declaration until the end is reached
    def parse_program(self):
        while self.current_token() is not None:
            self.parse_declaration()
        print("Parsing completed successfully.")

    # Distinguish between function and variable declarations
    def parse_declaration(self):
        # Define valid declaration types and gather current token
        valid_types = {"T_Void", "T_Int", "T_Double", "T_String", "T_Bool"}
        token = self.current_token()

        # Check if the token exists and is a valid declaration type
        if token is None or token.type not in valid_types:
            self.syntax_error()

        # Consume token
        token_type = self.advance_token()

        # Check identifier to match correctly then consume it
        identifier = self.current_token()
        if identifier is None or identifier.type != "T_IDENTIFIER":
            self.syntax_error()
        identifier = self.advance_token()

        # Parse a function declaration if the next character is (
        if self.current_token() is not None and self.current_token().value == "(":
            self.parse_function()
        # Parse a variable declaration
        else:
            # Token type cannot be void
            if token_type.type == "T_Void":
                self.syntax_error()

            # Parse multiple variable definitions
            while self.current_token() is not None and self.current_token().value == ",":
                self.advance_token()

                if not self.match_token("T_IDENTIFIER"):
                    self.syntax_error()

            # Check for closing semicolon
            if self.current_token() is None or self.current_token().value != ";":
                self.syntax_error()

            # Consume semicolon and finish parsing the variable declaration
            self.advance_token()

    # Parse function declaration
    def parse_function(self):
        # Consume opening parenthesis
        self.advance_token()

        # Check for parameters
        if self.current_token() is not None and self.current_token().value != ")":
            # Begin parsing one or more parameters
            while True:
                token = self.current_token()

                # Check for valid token type, then consume it
                if token is None or token.type not in {
                    "T_Int", "T_Double", "T_String", "T_Bool"
                }:
                    self.syntax_error()

                self.advance_token()

                # Check for parameter identifier name
                if not self.match_token("T_IDENTIFIER"):
                    self.syntax_error()

                # Check for comma, indicating another parameter, else break from the loop
                if self.current_token() is None or self.current_token().value != ",":
                    break

                # Consume comma
                self.advance_token()

        # Check for closing parenthesis, then consume it
        if self.current_token() is None or self.current_token().value != ")":
            self.syntax_error()
        self.advance_token()

        # Parse function body
        self.parse_block()

    # Parse function body enclosed in curly braces
    def parse_block(self):
        # Check for opening brace, then consume it
        if self.current_token() is None or self.current_token().value != "{":
            self.syntax_error()
        self.advance_token()

        # Parse local variable declarations
        while self.current_token() is not None and self.current_token().type in {
            "T_Int", "T_Double", "T_String", "T_Bool"
        }:
            self.parse_variable_declaration()

        # Parse statements until closing brace is reached
        while self.current_token() is not None and self.current_token().value != "}":
            self.parse_statement()

        # Check for missing closing brace, then consume it
        if self.current_token() is None:
            self.syntax_error()
        self.advance_token()

    # Parse local variable declarations
    def parse_variable_declaration(self):
        # Consume type token found in parse_block
        self.advance_token()

        # Identify one or multiple variables
        while True:
            # Check for correct identifier type
            if not self.match_token("T_IDENTIFIER"):
                self.syntax_error()

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

    # Parse different kinds of statements
    def parse_statement(self):
        # Find current token to determine what kind of statement it is
        token = self.current_token()

        # Statement expected, but no token
        if token is None:
            self.syntax_error()

        # Parse block statement based on opening curly brace
        if token.value == "{":
            self.parse_block()
            return

        # Parse If statement, indicated by token type
        if token.type == "T_If":
            self.parse_if()
            return

        # Parse While statement, indicated by token type
        if token.type == "T_While":
            self.parse_while()
            return

        # Parse For statement, indicated by token type
        if token.type == "T_For":
            self.parse_for()
            return

        # Consume break and continue statements, indicated by token type
        if token.type in {"T_Break", "T_Continue"}:
            self.advance_token()
            self.expect_value(";")
            return

        # Parse return statements, indicated by token type
        if token.type == "T_Return":
            # Consume return keyword
            self.advance_token()

            # Parse return expression
            if self.current_token() is not None and self.current_token().value != ";":
                self.parse_expression()

            # Consume return semicolon
            self.expect_value(";")
            return

        # Parse identifier and print statements, indicated by token type
        if token.type in {"T_IDENTIFIER", "T_Print"}:
            # Consume keyword
            self.advance_token()

            # Parse function call
            if self.current_token() is not None and self.current_token().value == "(":
                self.parse_call_arguments()
                self.expect_value(";")
                return

            # Check for array
            if self.current_token() is not None and self.current_token().value == "[":
                self.advance_token()
                self.parse_expression()
                self.expect_value("]")

            # Check for assignment operator, then consume it
            if self.current_token() is None or self.current_token().value not in {"=", "+", "-"}:
                self.syntax_error()
            operator = self.advance_token().value

            # Check for compound operation
            if operator in {"+", "-"}:
                if self.current_token() is None or self.current_token().value != "=":
                    self.syntax_error()

                self.advance_token()

            # Parse rest of expression
            self.parse_expression()
            self.expect_value(";")
            return

        self.syntax_error()

    # Parse If statements
    def parse_if(self):
        # Consume keyword
        self.advance_token()

        # Require opening and closing parenthesis, and parse expression inside
        self.expect_value("(")
        self.parse_expression()
        self.expect_value(")")

        # Parse body
        self.parse_block()

        # Check for else statement and parse it
        if self.current_token() is not None and self.current_token().type == "T_Else":
            self.advance_token()
            self.parse_block()

    # Parse While statements
    def parse_while(self):
        # Consume keyword
        self.advance_token()

        # Check for opening and closing parenthesis, and parse expression inside
        self.expect_value("(")
        self.parse_expression()
        self.expect_value(")")

        # Parse function body
        self.parse_block()

    # Parse For statements
    def parse_for(self):
        # Consume keyword
        self.advance_token()

        # Check for identifier
        if not self.match_token("T_IDENTIFIER"):
            self.syntax_error()

        # Require equals sign and comma for proper statement declaration
        self.expect_value("=")
        self.parse_expression()

        self.expect_value(",")
        self.parse_expression()

        # Parse function body
        self.parse_block()

    # Parse expression statements
    def parse_expression(self, min_precedence=1):
        # Parse the first operand
        self.parse_unary()

        # Parse one or more operators
        while self.current_token() is not None:
            # Match operator with precedence value
            operator = self.current_token().value
            precedence = PRECEDENCE.get(operator, 0)

            # Decide if precedence meets current precedence level
            if precedence < min_precedence:
                break

            # Consume operator and use recursion for parsing next level of precedence
            self.advance_token()
            self.parse_expression(precedence + 1)

    # Parse unary operators
    def parse_unary(self):
        token = self.current_token()

        # Check for operators in front of operand to consume and recursively parse, otherwise parse primary expression
        if token is not None and token.value in {"-", "!"}:
            self.advance_token()
            self.parse_unary()
        else:
            self.parse_primary()

    # Parse primary expressions
    def parse_primary(self):
        # Consume current token
        token = self.current_token()

        if token is None:
            self.syntax_error()

        # Handle expressions within parenthesis
        if token.value == "(":
            self.advance_token()
            self.parse_expression()
            self.expect_value(")")
            return

        # Handle constant values
        if token.type in {"T_IntConstant", "T_BoolConstant", "T_StringConstant"}:
            self.advance_token()
            return

        # Handle identifiers and print statements
        if token.type in {"T_IDENTIFIER", "T_Print"}:
            self.advance_token()

            # Check for array
            if self.current_token() is not None and self.current_token().value == "[":
                self.advance_token()
                self.parse_expression()
                self.expect_value("]")
                return

            # Handle function calls
            if self.current_token() is not None and self.current_token().value == "(":
                self.parse_call_arguments()

            return

        self.syntax_error()

    # Parse argument list of function calls
    def parse_call_arguments(self):
        self.expect_value("(")

        # Check if arguments exist
        if self.current_token() is not None and self.current_token().value != ")":
            # Parse first argument
            self.parse_expression()

            # Parse additional arguments
            while self.current_token() is not None and self.current_token().value == ",":
                self.advance_token()
                self.parse_expression()

        self.expect_value(")")

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
    except SyntaxError:
        parser.report_syntax_error()

if __name__ == "__main__":
    main()