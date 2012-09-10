// Author: Eric Leblond <eric@regit.org>
// Desc: Search for function having a struct 'type' as argument
// Confidence: 94%
// Arguments: type, function
// Revision: 4
@init@
$type *p;
$type np;
position p1;
type t;
identifier sfunc $cocci_regexp_equal "$attribute";
@@

(
sfunc((t)p@p1, ...)
|
sfunc(..., (t)p@p1, ...)
|
sfunc(..., (t)p@p1)
|
sfunc((t)np@p1, ...)
|
sfunc(..., (t)np@p1, ...)
|
sfunc(..., (t)np@p1)
)
