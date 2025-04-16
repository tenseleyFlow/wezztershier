## wezztershier decoration grammar

\<decorator_line>  ::= "-- @ui:" \<annotation>  
\<annotation>      ::= \<ui_type> [ "(" \<param_list> ")" ] { \<trailing_param> }  
\<ui_type>         ::= \<identifier>  
\<param_list>      ::= \<param> { "," <param> }  
\<trailing_param>  ::= \<identifier> "=" (\<number> | \<string> | \<identifier>) [ "," ]  
\<param>           ::= \<identifier> "=" (\<number> | \<string> | \<identifier>)  
\<identifier>      ::= letter { letter | digit | "_" }  
\<number>          ::= digit { digit } [ "." digit { digit } ]  
\<string>          ::= "\"" { any character except "\"" } "\""  
