// Author: Eric Leblond <eric@regit.org>
// Desc: Search for usage of a given attribute for a 'type' structure
// Confidence: 100%
// Arguments: type, attribut
// Revision: 1
@init@
$type *p;
$type ps;
position p1;
@@

(
p@p1->$attribut
|
ps@p1.$attribut
)
