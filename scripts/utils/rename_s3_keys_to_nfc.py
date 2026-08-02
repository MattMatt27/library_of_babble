"""
One-off: rename S3 objects under images/artists/ whose keys are not in NFC
Unicode form to their NFC equivalent.

Some artwork images were stored with NFD (decomposed) accents in the key
while the DB refers to them in NFC, so the URL 404s. This canonicalizes the
S3 side to NFC. Pair it with scripts/utils/normalize_artwork_unicode.py
(which does the same to the DB) so both sides match.

Idempotent and safe: copies old -> new then deletes old; skips a rename if
the NFC target already exists (no overwrite).

Usage (repo root, with venv). Credentials via the standard AWS chain, e.g.
AWS_PROFILE=library-of-babble, or the ECS task role in-container:
    .venv/bin/python -m scripts.utils.rename_s3_keys_to_nfc --bucket library-of-babble-static --dry-run
    .venv/bin/python -m scripts.utils.rename_s3_keys_to_nfc --bucket library-of-babble-static
"""
import argparse
import os
import sys
import unicodedata

import boto3

PREFIX = "images/artists/"


def list_keys(s3, bucket):
    keys = []
    token = None
    while True:
        kw = {"Bucket": bucket, "Prefix": PREFIX}
        if token:
            kw["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kw)
        keys.extend(o["Key"] for o in resp.get("Contents", []))
        if not resp.get("IsTruncated"):
            break
        token = resp["NextContinuationToken"]
    return keys


def run(bucket, dry_run=False):
    s3 = boto3.client("s3")
    keys = list_keys(s3, bucket)
    existing = set(keys)

    todo, collisions = [], []
    for k in keys:
        if unicodedata.is_normalized("NFC", k):
            continue
        nfc = unicodedata.normalize("NFC", k)
        if nfc in existing:
            collisions.append((k, nfc))
        else:
            todo.append((k, nfc))

    print(f"bucket: {bucket} | objects under {PREFIX}: {len(keys)}")
    print(f"not-NFC keys to rename: {len(todo)} | collisions skipped: {len(collisions)}")
    for old, new in collisions:
        print(f"  SKIP (target exists): {old}")

    for old, new in todo:
        if dry_run:
            print(f"  [dry-run] would rename:\n     {old}\n  -> {new}")
            continue
        s3.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": old},
            Key=new,
            MetadataDirective="COPY",
        )
        s3.delete_object(Bucket=bucket, Key=old)
        print(f"  renamed: {old} -> {new}")

    print(f"{'[dry-run] ' if dry_run else ''}done: {len(todo)} renamed, {len(collisions)} skipped")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=os.getenv("S3_BUCKET_NAME"),
                    help="S3 bucket (default: $S3_BUCKET_NAME)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.bucket:
        print("error: --bucket or $S3_BUCKET_NAME required", file=sys.stderr)
        sys.exit(2)
    run(args.bucket, dry_run=args.dry_run)
