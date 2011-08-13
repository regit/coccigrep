=========
coccigrep
=========

Introduction
============

coccigrep is a semantic grep for the C language based on coccinelle
(http://coccinelle.lip6.fr).
It can be used to find where a given structure is used in code files.

coccigrep depends on the spatch program which come with coccinelle.

Usage
=====

Run ''coccigrep.py -h'' for complete options.

Examples
========

To find where in a set of files the ''datalink'' attribute is used in the structure
named Packet, you can simply do ::

    $ coccigrep.py  -t Packet -a datalink  *c
    source-af-packet.c:300:     p->datalink = ptv->datalink;
    source-af-packet.c:758:     switch(p->datalink) {
    source-erf-dag.c:525:     p->datalink = LINKTYPE_ETHERNET;

If you want to be more precise and find where this attribute is set, you can use ::

    $ coccigrep.py  -t Packet -a datalink -o set  source*c
    source-af-packet.c:300:     p->datalink = ptv->datalink;
    source-erf-dag.c:525:     p->datalink = LINKTYPE_ETHERNET;
