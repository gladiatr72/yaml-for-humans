#!/usr/bin/env python3
"""
Generate brain/index.xml from existing pattern files.

NEW ARCHITECTURE (v1.4):
- Pattern files in brain/patterns/*.xml are the source of truth
- Support files in brain/support/*.xml are the source of truth
- This script reads patterns and generates brain/index.xml with routing
- Metadata from doc/claude-test-brain.xml is merged into index
"""

import os
from pathlib import Path
from lxml import etree


def load_metadata_from_monolith():
    """Load metadata and intent-pattern-map from metadata file."""
    source_path = "brain/metadata.xml"

    if not Path(source_path).exists():
        print(f"⚠ Warning: {source_path} not found, using defaults")
        return None, None

    print(f"Loading metadata from {source_path}...")
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    tree = etree.parse(source_path, parser)
    root = tree.getroot()

    # Extract metadata
    meta = root.find(".//meta")

    # Extract intent-pattern-map
    intent_map = root.find(".//intent-pattern-map")

    print(f"✓ Loaded metadata and intent-pattern-map")
    return meta, intent_map


def discover_pattern_files():
    """Discover all pattern files in brain/patterns/."""
    patterns_dir = Path("brain/patterns")

    if not patterns_dir.exists():
        print("✗ brain/patterns/ directory not found")
        return []

    pattern_files = sorted(patterns_dir.glob("*.xml"))
    print(f"\n✓ Found {len(pattern_files)} pattern files")

    # Extract pattern IDs from filenames
    patterns = []
    for filepath in pattern_files:
        pattern_id = filepath.stem
        patterns.append({
            'id': pattern_id,
            'filename': filepath.name,
            'path': filepath
        })

    return patterns


def discover_support_files():
    """Discover all support files in brain/support/."""
    support_dir = Path("brain/support")

    if not support_dir.exists():
        print("✗ brain/support/ directory not found")
        return []

    support_files = sorted(support_dir.glob("*.xml"))
    print(f"✓ Found {len(support_files)} support files")

    return [f.name for f in support_files]


def generate_index(patterns, support_files, meta, intent_map):
    """Generate brain/index.xml from patterns and metadata."""

    print("\nGenerating brain/index.xml...")

    index_root = etree.Element("brain-index")

    # Add metadata (from monolith if available, else create default)
    if meta is not None:
        # Copy metadata from monolith
        index_meta = etree.SubElement(index_root, "meta")

        # Copy version, but override source and generated-by
        version_elem = meta.find("version")
        if version_elem is not None:
            etree.SubElement(index_meta, "version").text = version_elem.text

        etree.SubElement(index_meta, "source").text = "brain/patterns/*.xml + brain/support/*.xml"
        etree.SubElement(index_meta, "generated-by").text = "brain/update_index.py"
        etree.SubElement(index_meta, "structure").text = "Metadata-only monolith + extracted patterns"

        # Copy other metadata fields
        for field in ["codebase", "test-framework", "last-updated", "architecture"]:
            elem = meta.find(field)
            if elem is not None:
                new_elem = etree.SubElement(index_meta, field)
                new_elem.text = elem.text
    else:
        # Create default metadata
        meta_elem = etree.SubElement(index_root, "meta")
        etree.SubElement(meta_elem, "version").text = "1.4"
        etree.SubElement(meta_elem, "source").text = "brain/patterns/*.xml + brain/support/*.xml"
        etree.SubElement(meta_elem, "generated-by").text = "brain/update_index.py"
        etree.SubElement(meta_elem, "structure").text = "Patterns-first architecture"

    # Add statistics
    stats = etree.SubElement(index_root, "statistics")
    etree.SubElement(stats, "pattern-files").text = str(len(patterns))
    etree.SubElement(stats, "support-files").text = str(len(support_files))
    etree.SubElement(stats, "total-files").text = str(len(patterns) + len(support_files) + 1)

    # Add routing (intent-pattern-map from monolith)
    if intent_map is not None:
        routing = etree.SubElement(index_root, "routing")
        # Deep copy the intent-pattern-map
        routing.append(etree.fromstring(etree.tostring(intent_map)))
    else:
        print("⚠ Warning: No intent-pattern-map found in monolith")

    # Add file manifest
    manifest = etree.SubElement(index_root, "file-manifest")

    # Patterns section
    patterns_section = etree.SubElement(manifest, "patterns")
    etree.SubElement(patterns_section, "directory").text = "brain/patterns/"
    for pattern in patterns:
        file_elem = etree.SubElement(patterns_section, "file")
        file_elem.set("id", pattern['id'])
        file_elem.text = pattern['filename']

    # Support section
    support_section = etree.SubElement(manifest, "support")
    etree.SubElement(support_section, "directory").text = "brain/support/"
    for filename in support_files:
        etree.SubElement(support_section, "file").text = filename

    # Write index (no XML declaration for consistency with other brain files)
    tree = etree.ElementTree(index_root)
    tree.write(
        "brain/index.xml",
        encoding="UTF-8",
        xml_declaration=False,
        pretty_print=True
    )
    print("✓ brain/index.xml generated")


def validate_output():
    """Validate generated index.xml."""
    print("\nValidating brain/index.xml...")

    try:
        tree = etree.parse("brain/index.xml")
        print("✓ brain/index.xml is well-formed XML")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def print_summary(patterns, support_files):
    """Print summary statistics."""
    print("\n" + "="*70)
    print("INDEX GENERATION COMPLETE")
    print("="*70)

    print(f"\nPattern files:  {len(patterns)} files in brain/patterns/")
    print(f"Support files:  {len(support_files)} files in brain/support/")
    print(f"Index file:     1 file (brain/index.xml)")
    print(f"Total:          {len(patterns) + len(support_files) + 1} files")

    # Calculate sizes
    patterns_dir = Path("brain/patterns")
    support_dir = Path("brain/support")

    pattern_size = sum(f.stat().st_size for f in patterns_dir.glob("*.xml"))
    support_size = sum(f.stat().st_size for f in support_dir.glob("*.xml"))
    index_size = Path("brain/index.xml").stat().st_size
    metadata_size = Path("brain/metadata.xml").stat().st_size if Path("brain/metadata.xml").exists() else 0

    total_size = pattern_size + support_size + index_size + metadata_size

    print(f"\nSizes:")
    print(f"  Patterns:     {pattern_size/1024:.1f} KB")
    print(f"  Support:      {support_size/1024:.1f} KB")
    print(f"  Index:        {index_size/1024:.1f} KB")
    print(f"  Metadata:     {metadata_size/1024:.1f} KB (brain/metadata.xml)")
    print(f"  Total:        {total_size/1024:.1f} KB")

    print("\n✓ Patterns are the source of truth")
    print("  Edit pattern files in brain/patterns/ directly")
    print("  Run 'uv run python brain/update_index.py' to regenerate index")


def main():
    """Main workflow."""
    print("Brain Index Generator - v1.4")
    print("="*70)
    print("Architecture: Patterns-first (no extraction from monolith)")
    print()

    # Step 1: Load metadata from trimmed monolith
    meta, intent_map = load_metadata_from_monolith()

    # Step 2: Discover pattern files
    patterns = discover_pattern_files()
    if not patterns:
        print("✗ No pattern files found - aborting")
        return 1

    # Step 3: Discover support files
    support_files = discover_support_files()

    # Step 4: Generate index
    generate_index(patterns, support_files, meta, intent_map)

    # Step 5: Validate
    valid = validate_output()

    # Step 6: Print summary
    print_summary(patterns, support_files)

    if valid:
        print("\n✓ Index generation successful")
        return 0
    else:
        print("\n✗ Index generation failed validation")
        return 1


if __name__ == "__main__":
    exit(main())
