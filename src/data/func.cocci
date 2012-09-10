// Author: Eric Leblond <eric@regit.org>
// Desc: Search for function having a struct 'type' as argument
// Confidence: 91%
// Arguments: type, function
// Revision: 2
@init@
$type *p;
$type np;
position p1;
@@

(
$attribute(p@p1, ...)
|
$attribute(..., p@p1, ...)
|
$attribute(..., p@p1)
|
$attribute(np@p1, ...)
|
$attribute(..., np@p1, ...)
|
$attribute(..., np@p1)
)
