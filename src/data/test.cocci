// Author: Eric Leblond <eric@regit.org>
// Desc: Search where a given attribut of 'type' structure is used in test.
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
p@p1->$attribut == E
|
p@p1->$attribut != E
|
p@p1->$attribut & E
|
p@p1->$attribut < E
|
p@p1->$attribut <= E
|
p@p1->$attribut > E
|
p@p1->$attribut >= E
|
E == p@p1->$attribut
|
E != p@p1->$attribut
|
E & p@p1->$attribut
|
E < p@p1->$attribut
|
E <= p@p1->$attribut
|
E > p@p1->$attribut
|
E >= p@p1->$attribut
|
ps@p1.$attribut == E
|
ps@p1.$attribut != E
|
ps@p1.$attribut & E
|
ps@p1.$attribut < E
|
ps@p1.$attribut <= E
|
ps@p1.$attribut > E
|
ps@p1.$attribut >= E
|
E == ps@p1.$attribut
|
E != ps@p1.$attribut
|
E & ps@p1.$attribut
|
E < ps@p1.$attribut
|
E <= ps@p1.$attribut
|
E > ps@p1.$attribut
|
E >= ps@p1.$attribut
)
