// Author: Eric Leblond <eric@regit.org>
// Desc: Search for usage of a given attribute for a 'type' structure
// Confidence: 100%
// Arguments: type, attribute
// Revision: 1
@init@
$type *p;
$type ps;
position p1;
@@

(
p@p1->$attribute
|
ps@p1.$attribute
)
