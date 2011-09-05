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
