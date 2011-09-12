// Author: Eric Leblond <eric@regit.org>
// Desc: Search where a given attribute of structure 'type' is set
// Confidence: 70%
// Arguments: type, attribute
@init@
$type *p;
$type ps;
expression E;
position p1;
@@

(
p@p1->$attribut |= E
|
p@p1->$attribut = E
|
p@p1->$attribut += E
|
p@p1->$attribut -= E
|
ps@p1.$attribut |= E
|
ps@p1.$attribut = E
|
ps@p1.$attribut += E
|
ps@p1.$attribut -= E
)
