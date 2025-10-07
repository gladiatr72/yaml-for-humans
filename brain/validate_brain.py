#!/usr/bin/env python3
"""
Validate brain/ directory structure and consistency.

Checks:
1. All XML files are well-formed
2. index.xml manifest matches actual files
3. Pattern IDs in index match actual pattern files
4. Intent-pattern-map references valid patterns
5. Support file references are valid
"""

import sys
from pathlib import Path
from lxml import etree
from collections import defaultdict


class ValidationError(Exception):
    """Validation failed."""
    pass


class BrainValidator:
    def __init__(self, brain_dir: Path = Path("brain")):
        self.brain_dir = brain_dir
        self.errors = []
        self.warnings = []

    def error(self, msg: str):
        """Record an error."""
        self.errors.append(f"✗ ERROR: {msg}")

    def warning(self, msg: str):
        """Record a warning."""
        self.warnings.append(f"⚠ WARNING: {msg}")

    def info(self, msg: str):
        """Print info message."""
        print(f"ℹ {msg}")

    def success(self, msg: str):
        """Print success message."""
        print(f"✓ {msg}")

    def validate_xml_wellformed(self, filepath: Path) -> bool:
        """Check if XML file is well-formed."""
        try:
            etree.parse(str(filepath))
            return True
        except etree.XMLSyntaxError as e:
            self.error(f"{filepath.relative_to(self.brain_dir)}: {e}")
            return False

    def validate_all_xml_files(self):
        """Validate all XML files are well-formed."""
        self.info("Validating XML syntax...")

        xml_files = list(self.brain_dir.rglob("*.xml"))
        if not xml_files:
            self.error("No XML files found in brain/")
            return

        valid = 0
        for filepath in xml_files:
            if self.validate_xml_wellformed(filepath):
                valid += 1

        if valid == len(xml_files):
            self.success(f"All {len(xml_files)} XML files are well-formed")
        else:
            self.error(f"Only {valid}/{len(xml_files)} XML files are well-formed")

    def validate_index_exists(self) -> etree._ElementTree | None:
        """Validate index.xml exists and is readable."""
        self.info("Checking index.xml...")

        index_path = self.brain_dir / "index.xml"
        if not index_path.exists():
            self.error("index.xml not found")
            return None

        try:
            tree = etree.parse(str(index_path))
            self.success("index.xml exists and is valid")
            return tree
        except Exception as e:
            self.error(f"index.xml parse error: {e}")
            return None

    def validate_pattern_files(self, index_tree: etree._ElementTree):
        """Validate pattern files match index manifest."""
        self.info("Validating pattern files...")

        root = index_tree.getroot()

        # Get pattern IDs from index
        pattern_files = root.findall(".//file-manifest/patterns/file")
        index_patterns = {elem.get("id"): elem.text for elem in pattern_files}

        # Get actual pattern files
        patterns_dir = self.brain_dir / "patterns"
        if not patterns_dir.exists():
            self.error("brain/patterns/ directory not found")
            return

        actual_files = {f.stem: f.name for f in patterns_dir.glob("*.xml")}

        # Check index patterns exist as files
        for pattern_id, filename in index_patterns.items():
            if filename not in [f.name for f in patterns_dir.glob("*.xml")]:
                self.error(f"Pattern file {filename} listed in index but not found in brain/patterns/")

        # Check actual files are in index
        for stem, filename in actual_files.items():
            if stem not in index_patterns:
                self.warning(f"Pattern file {filename} exists but not listed in index.xml")

        if not self.errors:
            self.success(f"All {len(index_patterns)} pattern files validated")

    def validate_support_files(self, index_tree: etree._ElementTree):
        """Validate support files match index manifest."""
        self.info("Validating support files...")

        root = index_tree.getroot()

        # Get support files from index
        support_files = root.findall(".//file-manifest/support/file")
        index_support = {elem.text for elem in support_files}

        # Get actual support files
        support_dir = self.brain_dir / "support"
        if not support_dir.exists():
            self.error("brain/support/ directory not found")
            return

        actual_files = {f.name for f in support_dir.glob("*.xml")}

        # Check index support files exist
        for filename in index_support:
            if filename not in actual_files:
                self.error(f"Support file {filename} listed in index but not found in brain/support/")

        # Check actual files are in index
        for filename in actual_files:
            if filename not in index_support:
                self.warning(f"Support file {filename} exists but not listed in index.xml")

        if not self.errors:
            self.success(f"All {len(index_support)} support files validated")

    def validate_intent_pattern_map(self, index_tree: etree._ElementTree):
        """Validate intent-pattern-map references valid patterns."""
        self.info("Validating intent-pattern-map...")

        root = index_tree.getroot()

        # Get all valid pattern IDs
        pattern_files = root.findall(".//file-manifest/patterns/file")
        valid_pattern_ids = {elem.get("id") for elem in pattern_files}

        # Get pattern references from intent map
        intent_patterns = root.findall(".//intent-pattern-map/intent/pattern-id")

        referenced_ids = defaultdict(list)
        for elem in intent_patterns:
            pattern_id = elem.text
            # Get the intent query for better error messages
            intent = elem.getparent()
            query = intent.get("query", "unknown")
            referenced_ids[pattern_id].append(query)

            if pattern_id not in valid_pattern_ids:
                self.error(
                    f"Intent '{query}' references pattern-id '{pattern_id}' "
                    f"which doesn't exist in manifest"
                )

        # Check for unreferenced patterns (just a warning)
        unreferenced = valid_pattern_ids - set(referenced_ids.keys())
        for pattern_id in unreferenced:
            self.warning(f"Pattern '{pattern_id}' exists but not referenced in intent-pattern-map")

        if not self.errors:
            self.success(f"All {len(referenced_ids)} pattern references are valid")

    def validate_pattern_file_structure(self):
        """Validate individual pattern files have correct structure."""
        self.info("Validating pattern file structure...")

        patterns_dir = self.brain_dir / "patterns"
        if not patterns_dir.exists():
            return

        checked = 0
        for filepath in patterns_dir.glob("*.xml"):
            try:
                tree = etree.parse(str(filepath))
                root = tree.getroot()

                # Check root element
                if root.tag != "pattern-file":
                    self.error(f"{filepath.name}: root element should be 'pattern-file', got '{root.tag}'")
                    continue

                # Check for meta section
                meta = root.find("meta")
                if meta is None:
                    self.error(f"{filepath.name}: missing <meta> section")
                else:
                    # Check pattern-id matches filename
                    pattern_id = meta.find("pattern-id")
                    if pattern_id is not None and pattern_id.text:
                        expected_filename = f"{pattern_id.text}.xml"
                        if filepath.name != expected_filename:
                            self.error(
                                f"{filepath.name}: pattern-id '{pattern_id.text}' "
                                f"doesn't match filename (expected {expected_filename})"
                            )

                # Check for pattern element
                pattern = root.find("pattern")
                if pattern is None:
                    self.error(f"{filepath.name}: missing <pattern> element")

                checked += 1
            except Exception as e:
                self.error(f"{filepath.name}: {e}")

        if checked > 0 and not self.errors:
            self.success(f"All {checked} pattern files have correct structure")

    def validate_monolith_is_metadata_only(self):
        """Validate that brain/metadata.xml contains no pattern content."""
        self.info("Validating metadata file is metadata-only...")

        metadata_path = Path("brain/metadata.xml")
        if not metadata_path.exists():
            self.error("brain/metadata.xml not found (required metadata file)")
            return

        try:
            tree = etree.parse(str(metadata_path))
            root = tree.getroot()

            # Check for forbidden sections (pattern content)
            forbidden_sections = [
                "executable-patterns",
                "decision-trees",
                "anti-patterns",
                "debugging-guide",
                "quick-reference",
                "test-smell-detection"
            ]

            for section in forbidden_sections:
                elem = root.find(f".//{section}")
                if elem is not None:
                    self.error(
                        f"brain/metadata.xml contains <{section}> section - "
                        f"pattern content should only be in brain/patterns/ and brain/support/"
                    )

            if not self.errors:
                self.success("brain/metadata.xml is metadata-only (correct)")

        except Exception as e:
            self.error(f"Error validating monolith: {e}")

    def validate_statistics(self, index_tree: etree._ElementTree):
        """Validate statistics in index.xml match actual counts."""
        self.info("Validating statistics...")

        root = index_tree.getroot()
        stats = root.find(".//statistics")

        if stats is None:
            self.warning("No statistics section in index.xml")
            return

        # Get actual counts
        patterns_dir = self.brain_dir / "patterns"
        support_dir = self.brain_dir / "support"

        actual_pattern_count = len(list(patterns_dir.glob("*.xml"))) if patterns_dir.exists() else 0
        actual_support_count = len(list(support_dir.glob("*.xml"))) if support_dir.exists() else 0
        actual_total = actual_pattern_count + actual_support_count + 1  # +1 for index.xml

        # Get reported counts
        pattern_files_elem = stats.find("pattern-files")
        support_files_elem = stats.find("support-files")
        total_files_elem = stats.find("total-files")

        if pattern_files_elem is not None:
            reported_pattern = int(pattern_files_elem.text)
            if reported_pattern != actual_pattern_count:
                self.error(
                    f"Statistics mismatch: index reports {reported_pattern} pattern files, "
                    f"but found {actual_pattern_count}"
                )

        if support_files_elem is not None:
            reported_support = int(support_files_elem.text)
            if reported_support != actual_support_count:
                self.error(
                    f"Statistics mismatch: index reports {reported_support} support files, "
                    f"but found {actual_support_count}"
                )

        if total_files_elem is not None:
            reported_total = int(total_files_elem.text)
            if reported_total != actual_total:
                self.error(
                    f"Statistics mismatch: index reports {reported_total} total files, "
                    f"but found {actual_total}"
                )

        if not self.errors:
            self.success(f"Statistics are accurate: {actual_pattern_count} patterns, {actual_support_count} support files")

    def run(self) -> bool:
        """Run all validations."""
        print("="*70)
        print("Brain Validation")
        print("="*70)
        print()

        # 1. Validate all XML files are well-formed
        self.validate_all_xml_files()
        print()

        # 2. Validate index exists
        index_tree = self.validate_index_exists()
        if index_tree is None:
            self.print_results()
            return False
        print()

        # 3. Validate pattern files
        self.validate_pattern_files(index_tree)
        print()

        # 4. Validate support files
        self.validate_support_files(index_tree)
        print()

        # 5. Validate intent-pattern-map
        self.validate_intent_pattern_map(index_tree)
        print()

        # 6. Validate pattern file structure
        self.validate_pattern_file_structure()
        print()

        # 7. Validate statistics
        self.validate_statistics(index_tree)
        print()

        # 8. Validate monolith is metadata-only
        self.validate_monolith_is_metadata_only()
        print()

        # Print results
        return self.print_results()

    def print_results(self) -> bool:
        """Print validation results."""
        print("="*70)
        print("Validation Results")
        print("="*70)
        print()

        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  {error}")
            print()
            print(f"✗ Validation FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            return False
        else:
            if self.warnings:
                print(f"✓ Validation PASSED with {len(self.warnings)} warning(s)")
            else:
                print("✓ Validation PASSED: brain/ structure is valid")
            return True


def main():
    """Main entry point."""
    validator = BrainValidator()
    success = validator.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
