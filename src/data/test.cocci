// Author: Eric Leblond <eric@regit.org>
// Desc: Search where a given attribute of 'type' structure is used in test.
// Confidence: 60%
// Arguments: type, attribute
// Revision: 1
@init@
$type *p;
$type ps;
expression E;
position p1;
@@

(
p@p1->$attribute == E
|
p@p1->$attribute != E
|
p@p1->$attribute & E
|
p@p1->$attribute < E
|
p@p1->$attribute <= E
|
p@p1->$attribute > E
|
p@p1->$attribute >= E
|
E == p@p1->$attribute
|
E != p@p1->$attribute
|
E & p@p1->$attribute
|
E < p@p1->$attribute
|
E <= p@p1->$attribute
|
E > p@p1->$attribute
|
E >= p@p1->$attribute
|
ps@p1.$attribute == E
|
ps@p1.$attribute != E
|
ps@p1.$attribute & E
|
ps@p1.$attribute < E
|
ps@p1.$attribute <= E
|
ps@p1.$attribute > E
|
ps@p1.$attribute >= E
|
E == ps@p1.$attribute
|
E != ps@p1.$attribute
|
E & ps@p1.$attribute
|
E < ps@p1.$attribute
|
E <= ps@p1.$attribute
|
E > ps@p1.$attribute
|
E >= ps@p1.$attribute
)
