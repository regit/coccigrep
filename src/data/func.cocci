// Author: Eric Leblond <eric@regit.org>
// Desc: Search for function having a struct 'type' as argument
// Confidence: 94%
// Arguments: type, function
// Revision: 3
@init@
$type *p;
$type np;
position p1;
type t;
@@

(
$attribute((t)p@p1, ...)
|
$attribute(..., (t)p@p1, ...)
|
$attribute(..., (t)p@p1)
|
$attribute((t)np@p1, ...)
|
$attribute(..., (t)np@p1, ...)
|
$attribute(..., (t)np@p1)
)
