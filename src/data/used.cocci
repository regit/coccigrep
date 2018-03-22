// Author: Eric Leblond <eric@regit.org>
// Desc: Search all usage of 'type' structure
// Confidence: 90%
// Arguments: type
// Revision: 2
@init@
$type *p;
$type ps;
position p1;
@@

(
p@p1
|
ps@p1
)

@filter@
identifier mp !~ "=";
position init.p1;
@@

mp@p1
