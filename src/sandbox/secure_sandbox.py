import ast
import logging

logger = logging.getLogger(__name__)


class ASTSecurityValidator(ast.NodeVisitor):
    """Detect unauthorized imports in Python code."""

    def __init__(self):
        self.violations = []
        self.is_breakout = False

        self.disallowed_modules = {
            "os", "subprocess", "ctypes", "socket", "shutil",
            "urllib", "requests", "http", "ftplib", "telnetlib",
            "paramiko", "pty", "fcntl", "pwd", "grp", "sys"
        }

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split(".")[0]
            if module in self.disallowed_modules:
                self.violations.append(
                    f"Unauthorized import: {alias.name}"
                )
                self.is_breakout = True

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module.split(".")[0]
            if module in self.disallowed_modules:
                self.violations.append(
                    f"Unauthorized from-import: {node.module}"
                )
                self.is_breakout = True

        self.generic_visit(node)
