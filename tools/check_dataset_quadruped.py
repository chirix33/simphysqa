"""Compatibility entry point for the fixed-clock refinement study.

Usage: python tools/check_dataset_quadruped.py --output <new-directory>
The old every-integration-step controller comparison is superseded.
"""
from study_dataset_quadruped import main

if __name__ == "__main__":
    main()
