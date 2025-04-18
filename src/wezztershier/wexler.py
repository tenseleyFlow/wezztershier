# :::
# :::: WEXLER :: parsing for wezztershier decorations ::::
# ::::: :::::::::::::::::::::::::::::::::::::::::::::: :::::
#
# :::
# :::: GRAMMAR ::::
# :::::::::::::::::::
#
# <decorator_line>  ::= "-- @ui:" <annotation>
# <annotation>      ::= <ui_type> [ "(" <param_list> ")" ] { <trailing_param> }
# <ui_type>         ::= <identifier>
# <param_list>      ::= <param> { "," <param> }
# <trailing_param>  ::= <identifier> "=" (<number> | <string> | <identifier>) [ "," ]
# <param>           ::= <identifier> "=" (<number> | <string> | <identifier>)
# <identifier>      ::= letter { letter | digit | "_" }
# <number>          ::= digit { digit } [ "." digit { digit } ]
# <string>          ::= "\"" { any character except "\"" } "\""
#
# :::
# :::: TODOs ::::
# :::::::::::::::::
#
#	  TODOne: parsing has overlapping functionality
#   TODO: better error handling for the tuning block grab
#
# Author: @espadonne (mfw)
# ::::
import re

# :::
# :::: NOTE: @espadonne (mfw) some notes:
# :::::     NUMBERS are integers/floats
# :::::     STRINGS are double-quoted, & not greedy
TOKEN_REGEX = [
    ("COMMA",    r"^,"),
    ("EQUAL",    r"^="),
    ("LPAREN",   r"^\("),
    ("RPAREN",   r"^\)"),
    ("SKIP",     r"^[ \t]+"),
    ("STRING",   r'^"(.*?)"'),
    ("NUMBER",   r"^\d+\.?\d*"),
    ("IDENT",    r"^[A-Za-z_][A-Za-z0-9_]*"),
]


# :::
# converts everything following the
# decoration prefix in an input string into tokens.
#
# returns that list of tokens
# ::::
def tokenize_annotation(in_str):
    tokens = []
    pos = 0

    while pos < len(in_str):
        matched = False

        for typ, pattern in TOKEN_REGEX:
            m = re.match(pattern, in_str[pos:])

            if m:
                if typ != "SKIP":
                    if typ == "STRING" and m.lastindex and m.lastindex >= 1:
                        token_val = m.group(1)
                    else:
                        token_val = m.group(0)

                    tokens.append({"typ": typ, "val": token_val})

                pos += m.end()
                matched = True
                break

        if not matched:
            raise Exception(f"Unexpected token at position {pos} in: {in_str[pos:]}")

    return tokens


# :::
# given a decorated line,
# (ie, one starting with "-- @ui:"), 
# parse it into a tuple:
#               (ui_type, params)
#
# NOTE: defaults to float type param
# ::::
def parse_decorator_line(decorator_line):
    prefix = "-- @ui:"

    if not decorator_line.startswith(prefix):
        raise Exception("Decorator line does not start with proper prefix")

    annotation_text = decorator_line[len(prefix):].strip()
    tokens = tokenize_annotation(annotation_text)
    parser = Wexler(tokens)
    ui_type, params = parser.parse_ui_annotation()

    if 'type' not in params:
        params['type'] = 'float'

    return ui_type, params


# :::
# scans the configuration content
# for decorations in a tuned section,
# ie, a block wrapped by:
#     "-- <<TUNER-START>>" and "-- <<TUNER-END>>".
#
# returns a list of entries:
#   {
#     'key': <config key>,
#     'value': <config value as a string>,
#     'ui_type': <parsed ui type>,
#     'params': <dictionary of parameters>,
#     'decorator': <original decorator line>
#   }
# ::::
def parse_annotations(config_content):
    end_marker = "-- <<TUNER-END>>"
    start_marker = "-- <<TUNER-START>>"
    end_index = config_content.find(end_marker)
    start_index = config_content.find(start_marker)

    if start_index == -1 or end_index == -1:
        return []

    block = config_content[start_index + len(start_marker): end_index].strip()
    lines = block.splitlines()
    entries = []

    i = 0
    while i < len(lines):
        local_line = lines[i].strip()

        if local_line.startswith("-- @ui:"):
            decorator_line = local_line

            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1

            if i < len(lines):
                config_line = lines[i].strip()
                m = re.match(r'^(config\.[\w_]+)\s*=\s*(.+)$', config_line)

                if m:
                    key = m.group(1)
                    value_str = m.group(2).strip()
                    ui_type, params = parse_decorator_line(decorator_line)
                    entry = {
                        'key': key,
                        'value': value_str,
                        'ui_type': ui_type,
                        'params': params,
                        'decorator': decorator_line,
                    }

                    entries.append(entry)
        i += 1

    return entries


# :::
# simple (but not so simple)
# parser for wezztershier decorations
#
# Author: @espadonne (mfw)
# ::::
class Wexler:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        else:
            return None

    def consume(self, expct_typ):
        token = self.current()

        if not token or token["typ"] != expct_typ:
            raise Exception(f"Expected token type {expct_typ} but \
                                got {token and token['typ'] or 'EOF'}")

        self.pos += 1
        return token

    # :::
    # not used currently, but
    # will be useful if expanding grammar
    #
    # ::::
    def match(self, expected_type):
        token = self.current()

        if token and token["typ"] == expected_type:
            self.pos += 1
            return True

        return False

    # :::
    # parses a single parameter of the form:
    #         IDENT "=" (NUMBER | STRING | IDENT)
    #
    # returns a tuple (key, value).
    # ::::
    def parse_single_param(self):
        key = self.consume("IDENT")["val"]
        self.consume("EQUAL")
        token = self.current()

        if token["typ"] == "NUMBER":
            value = float(self.consume("NUMBER")["val"])
        elif token["typ"] == "STRING":
            value = self.consume("STRING")["val"]
        elif token["typ"] == "IDENT":
            value = self.consume("IDENT")["val"]
        else:
            raise Exception(f"Unexpected token type: {token['typ']}")

        return key, value

    # :::
    # parses an annotation of the form:
    #       <ui_type> [ "(" <param_list> ")" ] { <trailing_param> }

    # returns a tuple: (ui_type, params_dict)
    #
    # ::::
    def parse_ui_annotation(self):
        ui_type = self.consume("IDENT")["val"]
        params = {}

        if self.current() and self.current()["typ"] == "LPAREN":
            self.consume("LPAREN")
            params = self.parse_param_list()
            self.consume("RPAREN")

        # parse any trailing para-
        # -meters outside the parentheses.
        while self.current() and self.current()["typ"] == "IDENT":
            key, value = self.parse_single_param()
            params[key] = value

            # Allow an optional comma
            # for a trailing parameter.
            if self.current() and self.current()["typ"] == "COMMA":
                self.consume("COMMA")
            else:
                break

        return ui_type, params

    # :::
    # parses a comma-separated list of parameters:
    #         <param_list> ::= <param> { "," <param> }
    #
    # where a parameter is in the form: 
    #         IDENT "=" (NUMBER | STRING | IDENT)
    #
    # ::::
    def parse_param_list(self):
        params = {}

        while True:
            key, value = self.parse_single_param()
            params[key] = value
            if not (self.current() and self.current()["typ"] == "COMMA"):
                break
            self.consume("COMMA")
        return params

# :::
# :::: NOTE: @espadonne (mfw) old
# def parse_config(self, config_content):
#     start_marker = "-- <<TUNER-START>>"
#     end_marker = "-- <<TUNER-END>>"
#     start_index = config_content.find(start_marker)
#     end_index = config_content.find(end_marker)
#     if start_index != -1 and end_index != -1:
#         tuner_block = config_content[start_index:end_index]
#         for line in tuner_block.splitlines():
#             if "config.font_size" in line:
#                 self.font_size_value = float(line.split("=")[1].strip())
#             elif "config.window_background_opacity" in line:
#                 self.opacity_value = float(line.split("=")[1].strip())
#             elif "config.macos_window_background_blur" in line:
#                 self.blur_value = float(line.split("=")[1].strip())
#             elif "config.color_scheme" in line:
#                 scheme_val = line.split("=")[1].strip()
#                 scheme_val = scheme_val.strip("\"'")
#                 self.selected_theme = scheme_val
#     else:
#         self.font_size_value = 12
#         self.opacity_value = 0.85
#         self.blur_value = 40
#         self.selected_theme = None
