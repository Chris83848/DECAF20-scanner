import sys

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
    "true": "T_BoolConstant (value= true)",
    "false": "T_BoolConstant (value= false)",
    "null": "T_Null"
}

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

TWO_CHAR_OPERATORS = {
    "<=": "T_LessEqual",
    ">=": "T_GreaterEqual",
    "&&": "T_LogicalAnd",
    "||": "T_LogicalOr",
    "==": "T_LogicalEqual",
    "!=": "T_NotEqual"
}

class Token:
    def __init__(self, value, type, line, start_column, end_column):
        self.value = value
        self.type = type
        self.line = line
        self.start_column = start_column
        self.end_column = end_column

    # use if in braces to insert values like in example output
    def print_token(self):
        print(f"{self.value}     line {self.line} Cols  {self.start_column + 1} - {self.end_column + 1}  is  {self.type}")

class Scanner:

    def __init__(self, filename):
        self.filename = filename
        self.tokens = []

    def scan_file(self):
        with open(self.filename, "r") as file:
            for line_number, line in enumerate(file, start=1):
                self.scan_line(line, line_number)

    def scan_line(self, line, line_number):
        column_number = 0

        # switch statement potentially
        while column_number < len(line):

            if line[column_number].isspace():
                column_number += 1
                continue

            if line[column_number] == '"':
                column_number = self.scan_string(line, line_number, column_number)
                continue

            if line[column_number].isdigit():
                column_number = self.scan_int(line, line_number, column_number)
                continue

            if line[column_number].isalpha():
                column_number = self.scan_identifier(line, line_number, column_number)
                continue

            if column_number + 1 < len(line):
                two_char_operator = line[column_number: column_number + 2]

                if two_char_operator in TWO_CHAR_OPERATORS:
                    token_type = TWO_CHAR_OPERATORS[two_char_operator]

                    self.tokens.append(Token(two_char_operator, token_type, line_number, column_number, column_number + 1))

                    column_number += 2
                    continue
                elif two_char_operator == "//":
                    break

            if line[column_number] in SPECIAL_CHARS:
                char = line[column_number]

                self.tokens.append(Token(char, SPECIAL_CHARS[char], line_number, column_number, column_number))

                column_number += 1
                continue

            column_number += 1

    def scan_string(self, line, line_number, column_number):
        start_column = column_number
        while column_number + 1 < len(line):
            column_number += 1
            if line[column_number] == '"':
                break
        end_column = column_number
        value = line[start_column:end_column + 1]

        self.tokens.append(Token(value, "T_StringConstant", line_number, start_column, end_column))

        column_number += 1
        return column_number

    def scan_int(self, line, line_number, column_number):
        start_column = column_number
        while column_number + 1 < len(line):
            column_number += 1
            if not line[column_number].isdigit():
                break
        end_column = column_number - 1
        value = line[start_column:end_column + 1]

        self.tokens.append(Token(value, "T_IntConstant", line_number, start_column, end_column))

        return column_number

    def scan_identifier(self, line, line_number, column_number):
        start_column = column_number
        while column_number + 1 < len(line):
            column_number += 1
            if not line[column_number].isalpha() and not line[column_number].isdigit() and not line[column_number] == "_":
                break
        end_column = column_number - 1
        value = line[start_column:end_column + 1]
        if value in KEYWORDS:
            token_type = KEYWORDS[value]
        else:
            token_type = "T_IDENTIFIER"

        self.tokens.append(Token(value, token_type, line_number, start_column, end_column))

        return column_number

    def print_tokens(self):
        for token in self.tokens:
            token.print_token()


def main():
    if len(sys.argv) != 2:
        print("Usage: python scanner.py inputfile.decaf")
        return

    filename = sys.argv[1]

    scanner = Scanner(filename)
    scanner.scan_file()
    scanner.print_tokens()

if __name__ == "__main__":
    main()