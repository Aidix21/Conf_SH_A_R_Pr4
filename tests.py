import unittest
import subprocess
import sys

SCRIPT_NAME = "main.py"


class TestConfigTool(unittest.TestCase):

    def run_tool(self, input_text):
        process = subprocess.Popen(
            [sys.executable, SCRIPT_NAME],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=input_text)
        return stdout.strip(), stderr.strip(), process.returncode

    def test_basic_octal(self):
        input_data = "[ VAL => 0o10 ]"
        stdout, stderr, code = self.run_tool(input_data)
        self.assertEqual(code, 0)
        self.assertIn("VAL = 8", stdout)

    def test_nested_dict(self):
        input_data = "[ SECTION => [ SUB => 0o7 ] ]"
        stdout, _, code = self.run_tool(input_data)
        self.assertEqual(code, 0)
        self.assertIn("[SECTION]", stdout)
        self.assertIn("SUB = 7", stdout)

    def test_comments(self):
        input_data = "\\ Comment\n[ KEY => 0o1 ] \\ End"
        stdout, _, code = self.run_tool(input_data)
        self.assertEqual(code, 0)
        self.assertIn("KEY = 1", stdout)

    def test_constants_calculation(self):
        input_data = """
        const A = 0o10
        const B = 0o2
        [ SUM => $(A + B) ]
        """
        stdout, _, code = self.run_tool(input_data)
        self.assertEqual(code, 0)
        self.assertIn("SUM = 10", stdout)  # 8 + 2

    def test_abs_function(self):
        input_data = """
        const NEG = 0o12 
        [ RES => $(abs(NEG)) ]
        """

        stdout, _, code = self.run_tool(input_data)
        self.assertEqual(code, 0)
        self.assertIn("RES = 10", stdout)

    def test_syntax_error(self):
        input_data = "[ KEY = 0o1 ]"
        stdout, stderr, code = self.run_tool(input_data)
        self.assertNotEqual(code, 0)
        self.assertIn("Error", stderr)


if __name__ == '__main__':
    unittest.main()
    
