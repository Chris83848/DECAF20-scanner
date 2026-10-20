import sys

# All DECAF20 keyword identifiers
KEYWORDS = {
    "void": "T_Void",
    "int": "T_Int",
    "double": "T_Double",
    "string": "T_String",
    "bool": "T_Bool",
    "Print": "T_Print",
    "return": "T_Return",
    "break": "T_Break",
    "continue": "T_Continue",
    "if": "T_If",
    "else": "T_Else",
    "while": "T_While",
    "for": "T_For",
    "true": "T_BoolConstant",
    "false": "T_BoolConstant",
    "null": "T_Null"
}

# All DECAF20 single characters
SPECIAL_CHARS = {
    "(": "'('",
    ")": "')'",
    "{": "'{'",
    "}": "'}'",
    "[": "'['",
    "]": "']'",
    "+": "'+'",
    "-": "'-'",
    "*": "'*'",
    "/": "'/'",
    "=": "'='",
    "<": "'<'",
    ">": "'>'",
    "?": "'?'",
    "!": "'!'",
    "|": "'|'",
    "&": "'&'",
    "%": "'%'",
    ",": "','",
    ":": "':'",
    ";": "';'"
}

# Special operators that use two characters
TWO_CHAR_OPERATORS = {
    "<=": "T_LessEqual",
    ">=": "T_GreaterEqual",
    "&&": "T_LogicalAnd",
    "||": "T_LogicalOr",
    "==": "T_LogicalEqual",
    "!=": "T_NotEqual"
}

# Holds an instance of each token, containing its value, data type, line number, and start/end columns
class Token:
    def __init__(self, value, type, line, start_column, end_column):
        self.value = value
        self.type = type
        self.line = line
        self.start_column = start_column
        self.end_column = end_column

    # Neatly prints out each token attribute, including the value at the end for booleans, integers, and strings
    def print_token(self):
        if self.type in {"T_BoolConstant", "T_IntConstant", "T_StringConstant"}:
            token_type = f"{self.type} (value= {self.value})"
        else:
            token_type = self.type

        print(f"{self.value}     line {self.line} Cols  {self.start_column + 1} - {self.end_column + 1}  is  {token_type}")

# Holds all methods for scanning any given DECAF20 file
class Scanner:

    def __init__(self, filename):
        self.filename = filename
        self.tokens = []

    # Scans given file line-by-line
    def scan_file(self):
        with open(self.filename, "r") as file:
            for line_number, line in enumerate(file, start=1):
                self.scan_line(line, line_number)

    # Scan current file line
    def scan_line(self, line, line_number):
        column_number = 0

        # Step through line character-by-character
        while column_number < len(line):

            # Skip over empty spaces
            if line[column_number].isspace():
                column_number += 1
                continue

            # Quotation marks indicate string to be scanned
            if line[column_number] == '"':
                column_number = self.scan_string(line, line_number, column_number)
                continue

            # Digit indicates number to be scanned
            if line[column_number].isdigit():
                column_number = self.scan_int(line, line_number, column_number)
                continue

            # Letter indicates identifier to be scanned
            if line[column_number].isalpha():
                column_number = self.scan_identifier(line, line_number, column_number)
                continue

            # Check for potential two character operators
            if column_number + 1 < len(line):
                two_char_operator = line[column_number: column_number + 2]

                # Add potential two character operator to tokens
                if two_char_operator in TWO_CHAR_OPERATORS:
                    token_type = TWO_CHAR_OPERATORS[two_char_operator]

                    self.tokens.append(Token(two_char_operator, token_type, line_number, column_number, column_number + 1))

                    column_number += 2
                    continue

                # Skip rest of line scanning if comment line found
                elif two_char_operator == "//":
                    break

            # Check for extraneous characters and add to tokens
            if line[column_number] in SPECIAL_CHARS:
                char = line[column_number]

                self.tokens.append(Token(char, SPECIAL_CHARS[char], line_number, column_number, column_number))

                column_number += 1
                continue

            column_number += 1

    # Dedicated string scanning method to find start/end columns and string value to add to tokens list
    def scan_string(self, line, line_number, column_number):
        # Save string start column
        start_column = column_number

        # Iterate until end quotations is found or end of line is reached
        while column_number + 1 < len(line):
            column_number += 1
            if line[column_number] == '"':
                break

        # Save string end column and slice string value
        end_column = column_number
        value = line[start_column:end_column + 1]

        # Save as token to tokens list
        self.tokens.append(Token(value, "T_StringConstant", line_number, start_column, end_column))

        # Increment column number and return back to where line scanner left off
        column_number += 1
        return column_number

    # Dedicated integer scanning method to find start/end columns and integer value to add to tokens list
    def scan_int(self, line, line_number, column_number):
        # Save integer start column
        start_column = column_number

        # Iterate to end of number or line
        while column_number + 1 < len(line):
            column_number += 1
            if not line[column_number].isdigit():
                break

        # Save integer end column and slice integer value
        end_column = column_number - 1
        value = line[start_column:end_column + 1]

        # Save as token to tokens list
        self.tokens.append(Token(value, "T_IntConstant", line_number, start_column, end_column))

        # Return to where line scanner left off
        return column_number

    # Dedicated identifier scanning method to find start/end columns and identifier value to add to tokens list
    def scan_identifier(self, line, line_number, column_number):
        # Save identifier start column
        start_column = column_number

        # Iterate to end of identifier, when current character is not a letter, digit, or underscore
        while column_number + 1 < len(line):
            column_number += 1
            if not line[column_number].isalpha() and not line[column_number].isdigit() and not line[column_number] == "_":
                break

        # Save identifier end column and slice identifier value
        end_column = column_number - 1
        value = line[start_column:end_column + 1]

        # If identifier value is a DECAF20 keyword, save its type as that, otherwise it is an identifier
        if value in KEYWORDS:
            token_type = KEYWORDS[value]
        else:
            token_type = "T_IDENTIFIER"

        # Save as token and add to tokens list
        self.tokens.append(Token(value, token_type, line_number, start_column, end_column))

        # Return to where line scanner left off
        return column_number

    # Print all saved tokens in token list by calling their class print functions
    def print_tokens(self):
        for token in self.tokens:
            token.print_token()

def main():
    if len(sys.argv) != 2:
        print("Example usage: python scanner.py inputfile.decaf")
        return

    filename = sys.argv[1]

    scanner = Scanner(filename)
    scanner.scan_file()
    scanner.print_tokens()

if __name__ == "__main__":
    main()