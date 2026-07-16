# AI Gateway Canonical JSON V1

Author attribution: **DarekDGB**

Profile identifier: `ai_gateway_canonical_json_v1`

Status: V4.9-D3A byte-profile and conformance lock

## Purpose

This contract defines the exact bytes used by current Adamantine AI Gateway
canonical SHA-256 evidence hashes. It replaces implementation-defined
"canonical JSON" wording with a closed, language-neutral algorithm.

The profile freezes existing valid Gateway bytes. It does not add or remove an
artifact field, change an existing digest, bump package version `1.0.0`, or
grant any authority.

## Supported value model

The byte algorithm operates on values built only from:

- JSON null;
- exact booleans;
- mathematical integers;
- strings containing valid Unicode scalar values;
- arrays; and
- objects with unique string keys.

Floats, decimal fractions, exponent-form numbers, NaN, infinities, byte
strings, tuples, sets, arbitrary host objects, cycles, and surrogate code
points are outside the byte profile and fail closed.

The V4.9-D2 policy-bound producer additionally requires exact built-in host
types and the governed limits below. Its serialization helper receives already
validated structured values and is not a raw-wire parser. A consumer that
receives raw D2/V2 JSON must apply the wire rules and limits below before it can
claim governed conformance.

Legacy V1 paths use the same frozen serializer expression, but V4.9-D3A does
not silently retrofit D2 exact-host-type or integer-width limits onto those
paths.

## Closed byte algorithm

### Literals and integers

- null is the four ASCII bytes `null`;
- false is `false` and true is `true`;
- zero is exactly `0`;
- a positive integer is its minimal base-10 ASCII digit sequence;
- a negative integer is `-` followed by that minimal digit sequence; and
- canonical output has no plus sign, leading zero, decimal point, or exponent.

Raw JSON integer `-0` represents the same mathematical integer as `0` and
therefore canonicalizes to `0`.

### Strings

A string begins and ends with ASCII quotation mark U+0022. For each Unicode
scalar value, in order:

| Scalar | Canonical output |
|---|---|
| U+0022 quotation mark | `\"` |
| U+005C reverse solidus | `\\` |
| U+0008 | `\b` |
| U+0009 | `\t` |
| U+000A | `\n` |
| U+000C | `\f` |
| U+000D | `\r` |
| Other U+0000 through U+001F | `\u` plus exactly four lowercase hex digits |
| Every other valid scalar | Raw UTF-8 encoding |

Examples of the lowercase rule are U+001B -> `\u001b` and U+001F ->
`\u001f`.

The solidus `/`, U+007F, U+0080 through U+009F, U+2028, U+2029, BMP scalars,
and astral scalars remain raw UTF-8. No Unicode normalization is applied.
NFC and NFD spellings therefore remain distinct.

Lone high or low surrogates are not Unicode scalar values and fail closed.

### Arrays

- emit `[`;
- emit each element recursively in original order, separated by `,`;
- emit `]`; and
- do not add whitespace.

Array order is identity-bearing.

### Objects

- every key must be a valid string;
- keys are sorted lexicographically by Unicode scalar-value sequence;
- when one key is a prefix of another, the shorter key sorts first;
- emit `{`;
- for each sorted key, emit its canonical string, `:`, and the canonical value;
- separate fields with `,`;
- emit `}`; and
- do not add whitespace.

The normative order is Unicode scalar-value sequence. An implementation may
use a shortcut only after proving that it produces the same order for every
supported key. UTF-16 code-unit, locale, grapheme, and normalized-text orders
must not be substituted.

### Whole output

The result is exactly one UTF-8 byte sequence with no BOM, leading whitespace,
trailing whitespace, or trailing newline.

## V4.9-D2 governed limits

The policy-bound producer enforces these limits before trusting a value:

| Limit | Maximum |
|---|---:|
| Container depth, root at depth zero | 10 |
| Keys in one object | 1,000 |
| Items in one array | 1,000 |
| String or object-key length | 10,000 Unicode scalar values |
| Absolute integer width | 4,096 bits |
| Snapshot nodes | 20,000 |
| Cumulative string/key UTF-8 and integer-text preflight bytes | 1,048,576 |
| Canonical snapshot bytes | 1,048,576 |
| Canonical binding artifact bytes | 4,096 |

Resource accounting is closed as follows:

- every value has a depth: the root is depth zero and each array element or
  object value is its parent's depth plus one;
- object keys do not add depth;
- every scalar or container occurrence, including the root, is one snapshot
  node;
- object keys are not snapshot nodes;
- a repeated host-container alias is traversed and counted at each occurrence,
  while an active container cycle is rejected;
- absolute integer width is `bit_length(abs(value))`, with zero width equal to
  zero and a negative integer measured without its sign;
- the preflight byte budget adds UTF-8 bytes for every string value and object
  key plus minimal decimal ASCII bytes, including a minus sign, for every
  integer occurrence; and
- booleans, null, structural punctuation, quotation marks, and escape expansion
  do not enter the preflight byte budget, while all of them do enter the final
  canonical-byte limit.

The 4,096-byte binding limit is an additional artifact-specific cap. It does
not replace the 1,048,576-byte snapshot and general governed-value cap.

The 10,000 limit is a Unicode scalar-value count. It is not UTF-8 byte length,
UTF-16 code-unit length, a grapheme count, or display width. Python uses
`len(value)` after surrogate rejection. A future Rust implementation must use
the equivalent of `value.chars().count()`, not `value.len()`.

The scalar limit and UTF-8 byte limit are independent and both apply.

These are D2 producer and D2/V2 consumer security limits, not additional byte
encodings. For example, the closed integer algorithm defines bytes for a
4,097-bit integer, while the D2 governed boundary rejects that integer before
it can become trusted policy-bound evidence.

## Strict raw-wire parser

The earliest parser for untrusted raw D2/V2 JSON must:

- decode strict UTF-8 and reject a BOM;
- consume exactly one JSON value;
- reject duplicate keys at every nesting level after JSON escape decoding;
- therefore treat `"a"` and `"\u0061"` as the same duplicate key;
- reject float grammar, NaN, and infinities;
- reject malformed escapes and lone surrogates;
- reject trailing data; and
- enforce the governed bounds before evidence is accepted.

An already decoded mapping cannot prove that the wire input had no duplicate
keys. Python `json.loads` and Rust `serde_json` default last-key-wins behavior
are not conforming unless a duplicate-detecting layer runs first.

## Hash binding

Current Gateway structured digests are:

```text
lowercase_hex(SHA-256(canonical_bytes))
```

There is no byte prefix or per-artifact domain tag in this V1 profile. Receipt,
handoff, output, envelope, and policy hashes are separated by closed artifact
shapes and named fields. Retrofitting a prefix would change existing hashes;
any future domain-tag design requires a new versioned profile and contract.

## Conformance evidence

For golden, equivalence, and injective vectors, the checked-in fixture stores
expected canonical bytes as literal lowercase hex and expected SHA-256 values
as literal lowercase hex. Tests must not regenerate those expected values with
the production serializer. Large exact-boundary vectors instead store
deterministic construction parameters, the exact expected byte length, and a
literal expected SHA-256; production and independent bytes are compared before
that hash is checked.

The fixture contains:

- accepted golden vectors;
- rejected raw-wire vectors;
- expected-equivalence pairs;
- distinct-input injectivity pairs with byte inequality as the witness; and
- exact accepted/rejected resource boundaries.

Frozen fixture SHA-256: `b14b240cd3f0bd5c9c8e7a55698a92609bcbf5ebb19dfe913514dad8802b4733`

The top-level `required_vector_ids` object is the portable completeness
inventory. It has exactly these five keys and no others:

```text
golden_vectors
equivalence_pairs
injective_pairs
rejected_wire_vectors
boundary_vectors
```

Each inventory value is an ordered array of unique, non-empty case-ID strings.
For every section, that array must equal the section's actual case-ID sequence
exactly. Missing, unexpected, duplicate, truncated, or reordered inventory or
case IDs fail conformance.

The inventory is not self-authenticating. A consumer must pin and verify the
complete fixture SHA-256 from an independently controlled contract or trusted
configuration before trusting it. The fixture must not contain a self-hash.
Python tests retain a separately written literal ID floor; future non-Python
consumers must retain their own external fixture-hash commitment.

`tools/check_ai_gateway_canonical_json_v1.py` is an independent standard-library
checker. It imports no Gateway module, does not call the production hash helper,
and does not use `json.dumps` for serialization. It separates the closed byte
algorithm from D2 governed-limit enforcement and compares bytes before hashes.

Seeded differential fuzzing compares production bytes with the independent
encoder before hashing. Every mismatch must fail CI. A minimized mismatch must
be promoted into the permanent literal fixture before the defect is closed.

## Cross-language claim boundary

V4.9-D3A proves the current Python producer against an independent Python
implementation. It does not claim Rust or SDK conformance.

Before any Rust compatibility claim, an independent Rust strict parser and
encoder must consume the same fixture, pass every accepted, rejected,
equivalence, injectivity, and boundary case, and pass pinned-seed Python-to-Rust
byte differential fuzzing. Default serializer parity is not sufficient.

## Security and authority limits

Canonical bytes provide deterministic content identity only. They do not
provide authentication, provenance, freshness, replay protection, proof of
honest execution, signing authority, broadcast authority, approval, override,
bypass, rescue, or execution authority.

AdamantineOS remains the independent final policy and execution boundary.

---

**MIT - DarekDGB**
