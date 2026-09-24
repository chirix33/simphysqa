"""Compatibility entry point for the current four-domain read-only review.

Historical five-domain evidence remains in docs/reviews/artifacts/PDS. This
command does not overwrite those artifacts or regenerate deferred manifests.
"""
from review_four_domain_release import main

if __name__ == "__main__":
    main()
