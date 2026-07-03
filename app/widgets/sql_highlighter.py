"""SQL syntax highlighter for source code display."""

from typing import Optional, Dict
from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt


class SqlSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL code."""

    def __init__(self, document: QTextDocument, colors: Optional[Dict[str, str]] = None):
        super().__init__(document)

        if colors is None:
            colors = {
                "keyword": "#0066CC",
                "builtin": "#666666",
                "string": "#CC0000",
                "comment": "#669966",
                "number": "#CC6600",
                "function": "#9B6432",
            }

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(colors["keyword"]))
        self.keyword_format.setFontWeight(QFont.Bold)

        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor(colors["builtin"]))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(colors["string"]))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(colors["comment"]))
        self.comment_format.setFontItalic(True)

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(colors["number"]))

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor(colors["function"]))
        self.function_format.setFontWeight(QFont.Bold)

        self.keywords = {
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE',
            'VIEW', 'INDEX', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'CONSTRAINT',
            'PRIMARY', 'FOREIGN', 'KEY', 'UNIQUE', 'CHECK', 'DEFAULT',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'ON',
            'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'DISTINCT',
            'AS', 'WITH', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'BEGIN',
            'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SET', 'DECLARE', 'RETURN',
            'IF', 'WHILE', 'FOR', 'LOOP', 'BREAK', 'CONTINUE', 'CURSOR',
            'CAST', 'CONVERT', 'DECLARE', 'EXEC', 'EXECUTE', 'GO', 'USE',
            'UNION', 'EXCEPT', 'INTERSECT', 'NULL', 'TRUE', 'FALSE',
            'INTO', 'VALUES', 'LIKE', 'BETWEEN', 'IS', 'COLLATE',
            'ALTER', 'ADD', 'MODIFY', 'RENAME', 'COLUMN', 'CONSTRAINT',
            'ENABLE', 'DISABLE', 'GRANT', 'REVOKE', 'TO', 'FROM',
            'SCHEMA', 'DATABASE', 'SERVER', 'ROLE', 'USER', 'LOGIN',
            'INNER', 'FULL', 'OVER', 'PARTITION', 'ASC', 'DESC'
        }

        self.builtins = {
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'CEIL', 'FLOOR',
            'ABS', 'SQRT', 'POWER', 'LOG', 'EXP', 'RAND', 'SUBSTRING',
            'LENGTH', 'LTRIM', 'RTRIM', 'UPPER', 'LOWER', 'REPLACE',
            'CONCAT', 'GETDATE', 'SYSDATETIME', 'DATEDIFF', 'DATEADD',
            'DAY', 'MONTH', 'YEAR', 'CURRENT_TIMESTAMP', 'CAST', 'CONVERT',
            'ISNULL', 'COALESCE', 'NULLIF', 'ROW_NUMBER', 'RANK', 'DENSE_RANK'
        }

    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text."""
        if not text.strip():
            return

        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
                continue

            if text[i] == '-' and i + 1 < len(text) and text[i + 1] == '-':
                end = len(text)
                self.setFormat(i, end - i, self.comment_format)
                return

            if text[i] == '/' and i + 1 < len(text) and text[i + 1] == '*':
                end = text.find('*/', i + 2)
                if end != -1:
                    end += 2
                else:
                    end = len(text)
                self.setFormat(i, end - i, self.comment_format)
                i = end
                continue

            if text[i] in ('"', "'"):
                quote = text[i]
                start = i
                i += 1
                while i < len(text):
                    if text[i] == quote:
                        if i + 1 < len(text) and text[i + 1] == quote:
                            i += 2
                        else:
                            i += 1
                            break
                    else:
                        i += 1
                self.setFormat(start, i - start, self.string_format)
                continue

            if text[i] == '[':
                start = i
                i += 1
                while i < len(text) and text[i] != ']':
                    i += 1
                if i < len(text):
                    i += 1
                self.setFormat(start, i - start, self.builtin_format)
                continue

            if text[i].isalpha() or text[i] == '_':
                start = i
                while i < len(text) and (text[i].isalnum() or text[i] == '_'):
                    i += 1
                word = text[start:i]
                word_upper = word.upper()

                if word_upper in self.keywords:
                    self.setFormat(start, i - start, self.keyword_format)
                elif word_upper in self.builtins:
                    self.setFormat(start, i - start, self.function_format)
                continue

            if text[i].isdigit():
                start = i
                while i < len(text) and (text[i].isdigit() or text[i] == '.'):
                    i += 1
                self.setFormat(start, i - start, self.number_format)
                continue

            i += 1

    def update_colors(self, colors: Dict[str, str]) -> None:
        """Update syntax colors and rehighlight document."""
        self.keyword_format.setForeground(QColor(colors["keyword"]))
        self.builtin_format.setForeground(QColor(colors["builtin"]))
        self.string_format.setForeground(QColor(colors["string"]))
        self.comment_format.setForeground(QColor(colors["comment"]))
        self.number_format.setForeground(QColor(colors["number"]))
        self.function_format.setForeground(QColor(colors["function"]))
        self.rehighlight()
