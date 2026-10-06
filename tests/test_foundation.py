"""Saved-artifact registry and package contract checks; no scientific executions."""
from copy import deepcopy
from pathlib import Path
import os
import tempfile
import tomllib
import unittest
from simphysqa.io import ROOT, canonical, read
from simphysqa.foundation import inventory, markdown


class PackagingContractTests(unittest.TestCase):
    def test_runtime_schemas_are_shipped(self):
        config=tomllib.loads((ROOT/'pyproject.toml').read_text())
        patterns=config['tool']['setuptools']['package-data']['simphysqa']
        included={p.name for pattern in patterns for p in (ROOT/'src/simphysqa').glob(pattern)}
        required={p.name for p in (ROOT/'src/simphysqa').glob('*.schema.json')}
        self.assertIn('clarification.schema.json',required)
        self.assertFalse(required-included,'a supported family would lack its validation schema')


class FoundationSavedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value=os.environ.get('SIMPHYSQA_FOUNDATION_ARTIFACTS')
        if not value:raise unittest.SkipTest('set SIMPHYSQA_FOUNDATION_ARTIFACTS to existing accepted external exports')
        cls.artifacts=Path(value)
        cls.index=inventory(cls.artifacts)

    def test_authoritative_snapshot_and_identity(self):
        self.assertEqual(canonical(self.index),canonical(read(ROOT/'docs/simphysqa/development-index.json')))
        self.assertEqual(self.index['counts']['prepared_initial_requests'],504)
        self.assertEqual({i['split'] for i in self.index['items']},{'train'})
        self.assertTrue(all(i['group_id'] in self.index['formal_exclusions']['excluded_groups'] for i in self.index['items']))

    def test_allocation_changes_fail_without_touching_exports(self):
        config=deepcopy(read(ROOT/'configs/simphysqa/development_artifacts.json'))
        config['expected_conditions']=8
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json';path.write_bytes(canonical(config))
            with self.assertRaisesRegex(ValueError,'condition allocation'):inventory(self.artifacts,path)

    def test_relative_root_produces_same_clickable_index(self):
        relative=Path(os.path.relpath(self.artifacts,Path.cwd()))
        self.assertEqual(markdown(self.index,relative),markdown(self.index,self.artifacts.resolve()))
