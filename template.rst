Certificate Of Authenticity
===========================

:header:
    As of {{ owner_timestamp }}, {{ owner }} is the owner.

    .. class:: verify

    To verify current owner, please visit {{ verify_owner_url }}


:footer:

    .. role:: logofont
    .. raw unicode character mapping to the logo is included below!

    Authenticated by :logofont:``


{{ title }}
-----------

:Edition\:: {{ edition_number }}/{{ num_editions }}
:Created by\:: {{ artist_name }}
:Owner\:: {{ owner }}

--------------------------------------------------------------------------------

ARTWORK DETAILS
...............

:Artwork ID\:: {{bitcoin_id}}
:File\:: {{ filename }} ({{ filesize }})

--------------------------------------------------------------------------------

PROVENANCE/OWNERSHIP HISTORY
............................

{% for timestamp, action in ownership_history %}
* {{ timestamp }} - {{ action }}
{% endfor %}

--------------------------------------------------------------------------------

CRYPTOGRAPHIC STAMP
...................

.. container:: crypto

    Use the summary and signature below to authenticate this certificate:
    {{ check_stamp_url }}

    :Summary\:: {{ crypto_message }}
    :Signature\:: {{ crypto_signature }}
