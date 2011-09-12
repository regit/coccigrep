// Author: Eric Leblond <eric@regit.org>
// Desc: Search for function having a struct 'type' as argument
// Confidence: 90%
// Arguments: type, function
// Revision: 1
@init@
$type *p;
position p1;
@@

(
$attribut(p@p1, ...)
|
$attribut(..., p@p1, ...)
|
$attribut(..., p@p1)
)
