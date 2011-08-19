@init@
typedef $type;
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
