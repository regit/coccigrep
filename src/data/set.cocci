// Author: Eric Leblond <eric@regit.org>
// Desc: Search where a given attribute of structure 'type' is set
// Confidence: 80%
// Arguments: type, attribute
// Revision: 2
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
p@p1->$attribut++
|
p@p1->$attribut--
|
ps@p1.$attribut |= E
|
ps@p1.$attribut = E
|
ps@p1.$attribut += E
|
ps@p1.$attribut -= E
|
ps@p1.$attribut++
|
ps@p1.$attribut--
)
