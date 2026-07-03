from dataclasses import dataclass
from typing import Optional


@dataclass
class SyntaxColors:
    """SQL syntax highlighting colors."""
    keyword: str
    builtin: str
    string: str
    comment: str
    number: str
    function: str


@dataclass
class UIColors:
    """Application UI colors."""
    background: str
    foreground: str
    accent: str
    accent_alt: str
    border: str
    hover: str
    selection: str
    link: str


@dataclass
class ThemeDefinition:
    """Complete theme definition."""
    name: str
    syntax: SyntaxColors
    ui: UIColors


LIGHT_DEFAULT = ThemeDefinition(
    name="Light (Default)",
    syntax=SyntaxColors(
        keyword="#0066CC",
        builtin="#666666",
        string="#CC0000",
        comment="#669966",
        number="#CC6600",
        function="#9B6432",
    ),
    ui=UIColors(
        background="#FFFFFF",
        foreground="#2C3E50",
        accent="#0066CC",
        accent_alt="#0052A3",
        border="#D0D0D0",
        hover="#F5F5F5",
        selection="#DCEEF8",
        link="#0066CC",
    ),
)

LIGHT_SOLARIZED = ThemeDefinition(
    name="Light (Solarized)",
    syntax=SyntaxColors(
        keyword="#268BD2",
        builtin="#859900",
        string="#2AA198",
        comment="#93A1A1",
        number="#D33682",
        function="#B58900",
    ),
    ui=UIColors(
        background="#FDF6E3",
        foreground="#586E75",
        accent="#268BD2",
        accent_alt="#1F5FA8",
        border="#EAE2D0",
        hover="#EFE8DD",
        selection="#E3DB5E",
        link="#268BD2",
    ),
)

LIGHT_ONE = ThemeDefinition(
    name="Light (One Light)",
    syntax=SyntaxColors(
        keyword="#A626A4",
        builtin="#4078F2",
        string="#50A14F",
        comment="#A0A1A7",
        number="#986801",
        function="#E45649",
    ),
    ui=UIColors(
        background="#FAFAFA",
        foreground="#383A42",
        accent="#4078F2",
        accent_alt="#2E5FDE",
        border="#E7E8EC",
        hover="#F3F3F3",
        selection="#DCE7F5",
        link="#4078F2",
    ),
)

DARK_DARCULA = ThemeDefinition(
    name="Dark (Darcula)",
    syntax=SyntaxColors(
        keyword="#CC7832",
        builtin="#9876AA",
        string="#6A8759",
        comment="#808080",
        number="#6897BB",
        function="#FFC66D",
    ),
    ui=UIColors(
        background="#2B2B2B",
        foreground="#A9B7C6",
        accent="#264F78",
        accent_alt="#3B5998",
        border="#323232",
        hover="#3E3E3E",
        selection="#214283",
        link="#589DF6",
    ),
)

DARK_DRACULA = ThemeDefinition(
    name="Dark (Dracula)",
    syntax=SyntaxColors(
        keyword="#FF79C6",
        builtin="#8BE9FD",
        string="#F1FA8C",
        comment="#6272A4",
        number="#BD93F9",
        function="#50FA7B",
    ),
    ui=UIColors(
        background="#282A36",
        foreground="#F8F8F2",
        accent="#6272A4",
        accent_alt="#44475A",
        border="#44475A",
        hover="#3E3F4B",
        selection="#44475A",
        link="#8BE9FD",
    ),
)

DARK_NORD = ThemeDefinition(
    name="Dark (Nord)",
    syntax=SyntaxColors(
        keyword="#81A1C1",
        builtin="#A3BE8C",
        string="#A3BE8C",
        comment="#616E88",
        number="#B48EAD",
        function="#88C0D0",
    ),
    ui=UIColors(
        background="#2E3440",
        foreground="#ECEFF4",
        accent="#88C0D0",
        accent_alt="#5E81AC",
        border="#3B4252",
        hover="#434C5E",
        selection="#434C5E",
        link="#81A1C1",
    ),
)

THEMES_MAP = {
    "Light (Default)": LIGHT_DEFAULT,
    "Light (Solarized)": LIGHT_SOLARIZED,
    "Light (One Light)": LIGHT_ONE,
    "Dark (Darcula)": DARK_DARCULA,
    "Dark (Dracula)": DARK_DRACULA,
    "Dark (Nord)": DARK_NORD,
}


def get_theme(name: str) -> Optional[ThemeDefinition]:
    """Get theme by name."""
    return THEMES_MAP.get(name)


def list_themes() -> list[str]:
    """List all available theme names."""
    return list(THEMES_MAP.keys())
