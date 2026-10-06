# SPQ01a bidirectional association decisions

Parent 05a546623a6f71758efeb78001dcf296568e7ef3 on simphysqa-naacl.
The user's follow-up authorizes a derived exported representation, not a physical
source migration or new annotation generation.

1. Build both directions from a single canonical SPQ01a state link. Retain exact
   relationship, link ID, target IDs and evidence; no new matching semantics.
2. Add compact indexes only at the public export boundary. Source QA wrappers and
   references stay exact; the copied organizer JSONL is byte-for-byte unchanged.
3. Store intervening associations separately with ordered endpoint IDs and gap-only
   relationship labels. Never attach them as additional active endpoint events.
4. Version the projection/schema independently at simphysqa-associations/1.0.1;
   keep language contract 2.0.0. Existing APIs remain compatible by making the new
   association_version explicit; the new CLI applies it consistently to all exports.
5. Include the export version in packet identity and public/schema manifests.
   Changed packet IDs distinguish export versions while QA identities stay stable.
6. Validate exact source recovery and canonical agreement in addition to mirror
   consistency; agreement between two forged directions alone is insufficient.

No model/simulation call, budget change, formal sample or new QA family is needed.
