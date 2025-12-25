import sys
import re
import math


class ConfigSyntaxError(Exception):
    pass


class ConfigParser:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.constants = {}

    def _error(self, message):
        line = self.text.count('\n', 0, self.pos) + 1
        last_newline = self.text.rfind('\n', 0, self.pos)
        col = self.pos - last_newline
        raise ConfigSyntaxError(f"Error at line {line}, col {col}: {message}")

    def _skip_whitespace_and_comments(self):
        while self.pos < self.length:
            char = self.text[self.pos]

            if char.isspace():
                self.pos += 1
                continue

            if char == '\\':
                end_line = self.text.find('\n', self.pos)
                if end_line == -1:
                    self.pos = self.length
                else:
                    self.pos = end_line + 1
                continue

            break

    def _match(self, pattern):
        self._skip_whitespace_and_comments()
        match = re.match(pattern, self.text[self.pos:])
        if match:
            self.pos += len(match.group(0))
            return match.group(0)
        return None

    def _expect(self, pattern, error_msg):
        res = self._match(pattern)
        if not res:
            self._error(error_msg)
        return res

    def parse(self):
        main_structure = None
        while True:
            self._skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            if self.text[self.pos:].startswith('const '):
                self._match(r'const')
                name = self._expect(r'[A-Z]+', "Expected constant name (uppercase letters)")
                self._expect(r'=', "Expected '=' after constant name")
                value = self._parse_value()
                self.constants[name] = value
            else:
                if main_structure is not None:
                    self._error("Multiple main structures defined or content after main structure")
                main_structure = self._parse_dict()

        if main_structure is None:
            return {}
        return main_structure

    def _parse_value(self):
        self._skip_whitespace_and_comments()

        octal_match = self._match(r'0[oO][0-7]+')
        if octal_match:
            try:
                return int(octal_match, 8)
            except ValueError:
                self._error("Invalid octal number")

        if self.pos < self.length and self.text[self.pos] == '[':
            return self._parse_dict()

        if self.text[self.pos:].startswith('$('):
            return self._parse_expression()

        name_match = self._match(r'[A-Z]+')
        if name_match:
            if name_match in self.constants:
                return self.constants[name_match]
            else:
                self._error(f"Undefined constant: {name_match}")

        self._error("Expected value (Number, Dictionary, or Expression)")

    def _parse_dict(self):
        self._expect(r'\[', "Expected '['")
        res_dict = {}

        while True:
            self._skip_whitespace_and_comments()
            if self.text[self.pos:].startswith(']'):
                self._match(r'\]')
                break

            key = self._expect(r'[A-Z]+', "Expected key (uppercase letters)")
            self._expect(r'=>', "Expected '=>'")
            value = self._parse_value()
            res_dict[key] = value

            self._skip_whitespace_and_comments()
            if self._match(r','):
                continue
            elif self.text[self.pos] == ']':
                continue
            else:
                self._error("Expected ',' or ']' in dictionary")

        return res_dict

    def _parse_expression(self):
        self._expect(r'\$\(', "Expected '$('")

        expr_start = self.pos
        paren_balance = 1
        while self.pos < self.length and paren_balance > 0:
            char = self.text[self.pos]
            if char == '(':
                paren_balance += 1
            elif char == ')':
                paren_balance -= 1
            self.pos += 1

        if paren_balance != 0:
            self._error("Unbalanced parentheses in expression")

        raw_expr = self.text[expr_start: self.pos - 1]

        allowed_names = self.constants.copy()
        allowed_names['abs'] = abs

        try:
            if not re.match(r'^[A-Z0-9\s\+\-\*\/\(\)oabs]+$', raw_expr):
                pass

            result = eval(raw_expr, {"__builtins__": {}}, allowed_names)
            return result
        except Exception as e:
            self._error(f"Expression evaluation error: {e}")


def to_toml(data):
    """Простой сериализатор в TOML."""
    output = []

    def serialize(obj, key_prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not isinstance(v, dict):
                    output.append(f"{k} = {v}")

            for k, v in obj.items():
                if isinstance(v, dict):
                    new_prefix = f"{key_prefix}.{k}" if key_prefix else k
                    output.append(f"\n[{new_prefix}]")
                    serialize(v, new_prefix)
        else:
            output.append(str(obj))

    serialize(data)
    return "\n".join(output)


try:
    input_text = sys.stdin.read()
    parser = ConfigParser(input_text)
    result = parser.parse()
    print(to_toml(result))
except ConfigSyntaxError as e:
    sys.stderr.write(str(e) + "\n")
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"Unexpected error: {e}\n")
    sys.exit(1)
