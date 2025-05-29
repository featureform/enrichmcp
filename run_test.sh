#!/bin/bash
# Run the failing test specifically
echo "=== Running test_relationships_in_annotations ==="
.venv/bin/python -m pytest tests/test_core.py::test_relationships_in_annotations -v

test_exit_code=$?

echo -e "\n=== Summary ==="
echo "Tests: $([ $test_exit_code -eq 0 ] && echo 'PASSED' || echo 'FAILED')"

# Return overall status
if [ $test_exit_code -eq 0 ]; then
  echo "Test passed successfully!"
  exit 0
else
  echo "Test failed."
  exit 1
fi
