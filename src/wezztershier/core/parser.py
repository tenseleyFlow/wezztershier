# :::
# :::: WEXLER :: the parser extraordinaire ::::
# ::::: ::::::::::::::::::::::::::::::::::: :::::
#
# Recursive descent parser for wezztershier decorations.
# Because regex is for quitters and we're here to 
# parse-evere through anything!
#
# :::
# :::: GRAMMAR :: the rules of engagement ::::
# :::::::::::::::::::::::::::::::::::::::::::::::
#
# <decorator_line>  ::= "-- @ui:" <annotation>
# <annotation>      ::= <ui_type> [ "(" <param_list> ")" ] { <trailing_param> }
# <ui_type>         ::= <identifier>
# <param_list>      ::= <param> { "," <param> }
# <trailing_param>  ::= <identifier> "=" <value> [ "," ]
# <param>           ::= <identifier> "=" <value>
# <value>           ::= <number> | <string> | <identifier> | <boolean> | <list> | <dict>
# <list>            ::= "[" [ <value> { "," <value> } ] "]"
# <dict>            ::= "{" [ <pair> { "," <pair> } ] "}"
# <pair>            ::= <identifier> ":" <value>
# <boolean>         ::= "true" | "false"
# <identifier>      ::= letter { letter | digit | "_" }
# <number>          ::= digit { digit } [ "." digit { digit } ]
# <string>          ::= "\"" { any character except unescaped "\"" } "\""
#
# :::
# :::: EXAMPLE DECORATIONS ::::
# ::::::::::::::::::::::::::::::::
#
#   -- @ui: slider(min=0, max=1, step=0.01) type=float
#   -- @ui: select(options="Dark, Light, Auto") type=string  
#   -- @ui: numerical(min=8, max=72) type=int
#   -- @ui: color_picker(format="hex", alpha=true) type=color
#   -- @ui: range_slider(min=0, max=50, linked=true) type=padding
#   -- @ui: font_picker(monospace_only=true, size_range=[8, 72]) type=font
#   -- @ui: key_binding(modifiers=["cmd", "shift"]) type=keybind
#   -- @ui: multi_select(options=["resize", "title", "close"], defaults={resize: true}) type=flags
#
# :::
# :::: TODOs ::::
# :::::::::::::::::
#
#   TODO: support for nested dicts/lists (currently single level)
#   TODO: better error messages with line numbers  
#   TODO: a REPL for testing decorations? parse-REPL? 
#
# :::
# :::: DONE ::::
# ::::::::::::::::
#
#     - Support for escape sequences in strings
#     - List and dict parsing
#     - Boolean literals
#     - Complex parameter structures
#
# Author: @espadonne (mfw)
# ::::

import re
import logging
from typing import Dict, List, Tuple, Optional, Any, TypedDict
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)

# :::
# :::: CONSTANTS :: decoration markers ::::
# :::::::::::::::::::::::::::::::::::::::::::
DECORATOR_PREFIX = "-- @ui:"
TUNER_START_MARKER = "-- <<TUNER-START>>"
TUNER_END_MARKER = "-- <<TUNER-END>>"

# Default parameter type when unspecified
DEFAULT_PARAM_TYPE = "float"


# :::
# :::: TOKEN TYPES :: the parse-ticles ::::
# :::::::::::::::::::::::::::::::::::::::::::
class TokenType(Enum):
    COMMA = auto()
    EQUAL = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()  # For list support
    RBRACKET = auto()
    LBRACE = auto()    # For dict support
    RBRACE = auto()
    COLON = auto()     # For dict key:value
    STRING = auto()
    NUMBER = auto()
    IDENT = auto()
    BOOLEAN = auto()   # true/false support
    SKIP = auto()
    EOF = auto()


# :::
# :::: TOKEN :: a unit of parse-ing ::::
# ::::::::::::::::::::::::::::::::::::::::::
@dataclass
class Token:
    typ: TokenType
    val: str
    pos: int = 0


# :::
# :::: ENTRY :: parsed configuration entry ::::
# ::::::::::::::::::::::::::::::::::::::::::::::::
class ConfigEntry(TypedDict):
    key: str
    value: str
    ui_type: str
    params: Dict[str, Any]
    decorator: str


# :::
# :::: TOKEN PATTERNS :: regex recipes ::::
# :::::::::::::::::::::::::::::::::::::::::::
# 
# NOTE: @espadonne (mfw) ordering matters!
#       especially STRING before IDENT
# ::::
TOKEN_PATTERNS = [
    (TokenType.COMMA,    r"^,"),
    (TokenType.EQUAL,    r"^="),
    (TokenType.COLON,    r"^:"),
    (TokenType.LPAREN,   r"^\("),
    (TokenType.RPAREN,   r"^\)"),
    (TokenType.LBRACKET, r"^\["),
    (TokenType.RBRACKET, r"^\]"),
    (TokenType.LBRACE,   r"^\{"),
    (TokenType.RBRACE,   r"^\}"),
    (TokenType.SKIP,     r"^[ \t]+"),
    (TokenType.STRING,   r'^"((?:[^"\\]|\\.)*)"'),  # Support escape sequences!
    (TokenType.NUMBER,   r"^\d+\.?\d*"),
    (TokenType.BOOLEAN,  r"^(true|false)\b"),  # Boolean literals
    (TokenType.IDENT,    r"^[A-Za-z_][A-Za-z0-9_]*"),
]


# :::
# :::: PARSE ERROR :: when things go parse-shaped ::::
# :::::::::::::::::::::::::::::::::::::::::::::::::::::
class ParseError(Exception):
    def __init__(self, message: str, position: Optional[int] = None):
        self.position = position
        super().__init__(f"Parse error at position {position}: {message}" if position else message)


# :::
# converts decoration text into tokens.
# tokenization: the process of turning a string
# into parse-able chunks. Like cheese, but digital.
#
# returns list of tokens or raises ParseError
# ::::
def tokenize_annotation(annotation_text: str) -> List[Token]:
    tokens: List[Token] = []
    pos = 0
    
    # :::
    # :::: NOTE: @espadonne (mfw)
    # :::::     we parse through the string char by char,
    # :::::     trying each pattern until one sticks.
    # :::::     like throwing spaghetti at the wall,
    # :::::     but with more determinism.
    # ::::
    while pos < len(annotation_text):
        matched = False
        
        for token_type, pattern in TOKEN_PATTERNS:
            regex_match = re.match(pattern, annotation_text[pos:])
            
            if regex_match:
                # Skip whitespace tokens - they're the parse-ley of parsing
                if token_type != TokenType.SKIP:
                    if token_type == TokenType.STRING and regex_match.lastindex:
                        # Extract string content without quotes
                        token_val = regex_match.group(1)
                        # Process escape sequences
                        token_val = token_val.replace('\\"', '"').replace('\\\\', '\\')
                    elif token_type == TokenType.BOOLEAN:
                        # Keep the boolean as string for now
                        token_val = regex_match.group(0)
                    else:
                        token_val = regex_match.group(0)
                    
                    tokens.append(Token(
                        typ=token_type,
                        val=token_val,
                        pos=pos
                    ))
                    
                    logger.debug(f"Token: {token_type.name}='{token_val}' at {pos}")
                
                pos += regex_match.end()
                matched = True
                break
        
        if not matched:
            # We've hit an un-parse-able character!
            raise ParseError(
                f"Unexpected character '{annotation_text[pos]}' in: {annotation_text[pos:]}",
                pos
            )
    
    return tokens


# :::
# given a decorated line starting with "-- @ui:",
# parse it into a tuple of (ui_type, params).
#
# This is the main entry point for single-line parsing.
# We're not just parsing, we're parse-ing with purpose!
# ::::
def parse_decorator_line(decorator_line: str) -> Tuple[str, Dict[str, Any]]:
    if not decorator_line.startswith(DECORATOR_PREFIX):
        raise ParseError(f"Decorator must start with '{DECORATOR_PREFIX}'")
    
    # Strip the prefix and any surrounding whitespace
    annotation_text = decorator_line[len(DECORATOR_PREFIX):].strip()
    
    if not annotation_text:
        raise ParseError("Empty decorator annotation")
    
    try:
        tokens = tokenize_annotation(annotation_text)
        parser = Wexler(tokens)
        ui_type, params = parser.parse_ui_annotation()
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     defaulting to float if type not specified
        # :::::     because floats are the butter of the parsing world
        # ::::
        if 'type' not in params:
            params['type'] = DEFAULT_PARAM_TYPE
        
        logger.debug(f"Parsed decorator: ui_type={ui_type}, params={params}")
        return ui_type, params
        
    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse decorator: {e}")


# :::
# scans the configuration content for decorations
# in the tuner section between the magic markers.
#
# Returns a list of ConfigEntry dictionaries.
# It's like archaeology, but for config files!
# ::::
def parse_annotations(config_content: str) -> List[ConfigEntry]:
    start_index = config_content.find(TUNER_START_MARKER)
    end_index = config_content.find(TUNER_END_MARKER)
    
    if start_index == -1 or end_index == -1:
        logger.warning("No tuner section found in config")
        return []
    
    # Extract the tuner block (the parse-able paradise)
    tuner_block = config_content[
        start_index + len(TUNER_START_MARKER): 
        end_index
    ].strip()
    
    lines = tuner_block.splitlines()
    entries: List[ConfigEntry] = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith(DECORATOR_PREFIX):
            decorator_line = line
            
            # Skip any empty lines after decorator
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            # :::
            # :::: NOTE: @espadonne (mfw)
            # :::::     Skip table initialization lines
            # :::::     and find the actual value assignment
            # ::::
            # Skip table initialization lines like "config.colors = config.colors or {}"
            while i < len(lines):
                config_line = lines[i].strip()
                # Check if this is a table init line
                if re.match(r'^config\.[\w_\.]+ = config\.[\w_\.]+ or \{\}$', config_line):
                    i += 1
                    continue
                else:
                    break
            
            # Next non-empty, non-init line should be the config assignment
            if i < len(lines):
                config_line = lines[i].strip()
                
                # :::
                # :::: NOTE: @espadonne (mfw)
                # :::::     Enhanced regex for nested table paths
                # :::::     Now handles config.colors.tab_bar.background etc
                # ::::
                match = re.match(r'^(config(?:\.[\w_]+)+)\s*=\s*(.+)$', config_line)
                
                if match:
                    key = match.group(1)
                    value_str = match.group(2).strip()
                    
                    try:
                        ui_type, params = parse_decorator_line(decorator_line)
                        
                        entry = ConfigEntry(
                            key=key,
                            value=value_str,
                            ui_type=ui_type,
                            params=params,
                            decorator=decorator_line,
                        )
                        
                        entries.append(entry)
                        logger.debug(f"Found entry: {key} -> {ui_type}")
                        
                    except ParseError as e:
                        logger.error(f"Failed to parse decorator on line {i}: {e}")
                else:
                    logger.warning(f"Invalid config line format: {config_line}")
        
        i += 1
    
    logger.info(f"Parsed {len(entries)} config entries")
    return entries


# :::
# :::: WEXLER :: the recursive descent parser ::::
# ::::: ::::::::::::::::::::::::::::::::::::::: :::::
#
# Named after... well, it just sounds like a parser's name.
# This magnificent beast chomps through tokens like
# pac-man through dots, building up our decoration AST.
#
# It's not just parsing, it's parse-onal!
#
# Author: @espadonne (mfw)
# ::::
class Wexler:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        logger.debug(f"Wexler initialized with {len(tokens)} tokens")
    
    # :::
    # get current token without consuming it.
    # like window shopping for tokens!
    # ::::
    def current(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    # :::
    # consume a token of expected type.
    # om nom nom, delicious tokens!
    # ::::
    def consume(self, expected_type: TokenType) -> Token:
        token = self.current()
        
        if not token:
            raise ParseError("Unexpected end of input", self.pos)
        
        if token.typ != expected_type:
            raise ParseError(
                f"Expected {expected_type.name} but got {token.typ.name}",
                token.pos
            )
        
        self.pos += 1
        logger.debug(f"Consumed {token.typ.name}: '{token.val}'")
        return token
    
    # :::
    # check if current token matches type
    # without consuming. Parse-king ahead!
    # ::::
    def peek(self, token_type: TokenType) -> bool:
        token = self.current()
        return token is not None and token.typ == token_type
    
    # :::
    # parses a single parameter of the form:
    #     IDENT "=" <value>
    #
    # where <value> can be NUMBER, STRING, IDENT, BOOLEAN, list, or dict
    # returns tuple (key, value) - the parse-fect pair!
    # ::::
    def parse_single_param(self) -> Tuple[str, Any]:
        key_token = self.consume(TokenType.IDENT)
        key = key_token.val
        
        self.consume(TokenType.EQUAL)
        
        # Parse the value - could be anything!
        value = self.parse_value()
        
        logger.debug(f"Parsed param: {key}={value}")
        return key, value
    
    # :::
    # parse any value type.
    # the swiss army knife of parsing!
    # ::::
    def parse_value(self) -> Any:
        """Parse a value which can be number, string, bool, list, or dict"""
        token = self.current()
        if not token:
            raise ParseError("Expected value", self.pos)
        
        if token.typ == TokenType.NUMBER:
            value_token = self.consume(TokenType.NUMBER)
            return float(value_token.val)
        elif token.typ == TokenType.STRING:
            value_token = self.consume(TokenType.STRING)
            return value_token.val
        elif token.typ == TokenType.BOOLEAN:
            value_token = self.consume(TokenType.BOOLEAN)
            return value_token.val.lower() == 'true'
        elif token.typ == TokenType.IDENT:
            value_token = self.consume(TokenType.IDENT)
            return value_token.val
        elif token.typ == TokenType.LBRACKET:
            return self.parse_list()
        elif token.typ == TokenType.LBRACE:
            return self.parse_dict()
        else:
            raise ParseError(
                f"Unexpected token type for value: {token.typ.name}",
                token.pos
            )
    
    # :::
    # parse a list: [value, value, ...]
    # lists are the parse-ty mix of values!
    # ::::
    def parse_list(self) -> List[Any]:
        """Parse a list of values"""
        self.consume(TokenType.LBRACKET)
        values = []
        
        # Empty list?
        if self.peek(TokenType.RBRACKET):
            self.consume(TokenType.RBRACKET)
            return values
        
        # Parse first value
        values.append(self.parse_value())
        
        # Parse remaining values
        while self.peek(TokenType.COMMA):
            self.consume(TokenType.COMMA)
            
            # Allow trailing comma
            if self.peek(TokenType.RBRACKET):
                break
                
            values.append(self.parse_value())
        
        self.consume(TokenType.RBRACKET)
        return values
    
    # :::
    # parse a dict: {key: value, key: value, ...}
    # dictionaries: where keys and values parse-ty together!
    # ::::
    def parse_dict(self) -> Dict[str, Any]:
        """Parse a dictionary of key:value pairs"""
        self.consume(TokenType.LBRACE)
        result = {}
        
        # Empty dict?
        if self.peek(TokenType.RBRACE):
            self.consume(TokenType.RBRACE)
            return result
        
        # Parse first pair
        key = self.consume(TokenType.IDENT).val
        self.consume(TokenType.COLON)
        result[key] = self.parse_value()
        
        # Parse remaining pairs
        while self.peek(TokenType.COMMA):
            self.consume(TokenType.COMMA)
            
            # Allow trailing comma
            if self.peek(TokenType.RBRACE):
                break
            
            key = self.consume(TokenType.IDENT).val
            self.consume(TokenType.COLON)
            result[key] = self.parse_value()
        
        self.consume(TokenType.RBRACE)
        return result
    
    # :::
    # parses a comma-separated list of parameters.
    # It's like a parse-ty with parameters as guests!
    # ::::
    def parse_param_list(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        
        # Parse first parameter (there must be at least one)
        if not self.peek(TokenType.IDENT):
            return params  # Empty param list is valid
        
        key, value = self.parse_single_param()
        params[key] = value
        
        # Parse remaining parameters
        while self.peek(TokenType.COMMA):
            self.consume(TokenType.COMMA)
            
            # Check if there's actually another param
            # (trailing commas are for parse-ners)
            if not self.peek(TokenType.IDENT):
                break
            
            key, value = self.parse_single_param()
            params[key] = value
        
        return params
    
    # :::
    # parses the full annotation:
    #     <ui_type> [ "(" <param_list> ")" ] { <trailing_param> }
    #
    # This is the main course of our parse-feast!
    # ::::
    def parse_ui_annotation(self) -> Tuple[str, Dict[str, Any]]:
        # First, get the UI type
        ui_type_token = self.consume(TokenType.IDENT)
        ui_type = ui_type_token.val
        params: Dict[str, Any] = {}
        
        # Check for parenthesized parameters
        if self.peek(TokenType.LPAREN):
            self.consume(TokenType.LPAREN)
            params = self.parse_param_list()
            self.consume(TokenType.RPAREN)
        
        # :::
        # :::: NOTE: @espadonne (mfw)
        # :::::     trailing parameters outside parentheses
        # :::::     because sometimes params like to parse-ty
        # :::::     outside the parentheses
        # ::::
        while self.current() and self.peek(TokenType.IDENT):
            # Make sure this is actually a param (has '=' after it)
            # by parse-king ahead
            saved_pos = self.pos
            try:
                key, value = self.parse_single_param()
                params[key] = value
                
                # Allow optional trailing comma because we're parse-ive
                if self.peek(TokenType.COMMA):
                    self.consume(TokenType.COMMA)
                
            except ParseError:
                # Not a parameter, restore position
                self.pos = saved_pos
                break
        
        # Make sure we've consumed everything
        if self.current() is not None:
            token = self.current()
            raise ParseError(
                f"Unexpected token after annotation: {token.typ.name}",
                token.pos
            )
        
        logger.debug(f"Parsed annotation: {ui_type} with {len(params)} params")
        return ui_type, params