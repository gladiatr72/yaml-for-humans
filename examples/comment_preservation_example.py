#!/usr/bin/env python3
"""
Example demonstrating comment preservation in yaml-for-humans.

This example shows how comments can be preserved when loading and dumping YAML,
following the rule that comments are associated with the next non-comment, non-blank line.
"""

from yaml_for_humans import load_with_formatting, dumps

def main():
    print("=== Comment Preservation Example ===\n")

    # Example YAML with comments
    original_yaml = """# Configuration file for our application
apiVersion: v1
kind: ConfigMap

# Metadata section
metadata:
  name: my-config
  namespace: default

# Application data
data:
  # Database configuration
  database_url: postgresql://localhost:5432/myapp
  database_timeout: 30

  # Cache settings
  cache_enabled: true
  cache_ttl: 3600

  # Feature flags
  feature_x_enabled: false  # Experimental feature
  feature_y_enabled: true"""

    print("Original YAML:")
    print(original_yaml)
    print("\n" + "="*50 + "\n")

    # Load YAML with formatting metadata
    print("Loading YAML with formatting preservation...")
    data = load_with_formatting(original_yaml)

    # Modify the data
    print("Modifying data (adding new feature flag)...")
    data['data']['feature_z_enabled'] = True

    # Dump with comment preservation
    print("Dumping with comment preservation:")
    preserved_yaml = dumps(data, preserve_comments=True, preserve_empty_lines=True)
    print(preserved_yaml)

    print("=" * 50 + "\n")

    # Show difference without comment preservation
    print("Dumping WITHOUT comment preservation:")
    normal_yaml = dumps(data, preserve_comments=False, preserve_empty_lines=False)
    print(normal_yaml)

    print("=" * 50 + "\n")

    # Demonstrate comment association rule
    print("=== Comment Association Rule Demo ===\n")

    comment_demo_yaml = """# First comment
# Second comment

# Third comment after blank line
key1: value1

# Comment for key2
# Multiple lines of comments
key2: value2"""

    print("YAML with comments and blank lines:")
    print(comment_demo_yaml)
    print("\nAfter loading and dumping with comment preservation:")

    demo_data = load_with_formatting(comment_demo_yaml)
    demo_output = dumps(demo_data, preserve_comments=True, preserve_empty_lines=True)
    print(demo_output)

    # Show comment associations
    print("Comment associations detected:")
    print(f"key1 has {len(demo_data._get_key_comments('key1').comments_before)} comments before it")
    print(f"key2 has {len(demo_data._get_key_comments('key2').comments_before)} comments before it")

    for i, comment in enumerate(demo_data._get_key_comments('key1').comments_before):
        print(f"  key1 comment {i+1}: {comment}")

    for i, comment in enumerate(demo_data._get_key_comments('key2').comments_before):
        print(f"  key2 comment {i+1}: {comment}")


if __name__ == "__main__":
    main()