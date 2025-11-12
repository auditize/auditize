#!/usr/bin/env python3

"""
Sort the fields by disk usage in descending order outputted by the following command:
curl -X GET "http://localhost:9200/{index_name}/_disk_usage?run_expensive_tasks=true"
"""

import json
import sys


def get_fields_sorted_by_disk_usage(data: dict):
    index_name = (data.keys() - {"_shards"}).pop()
    sorted_fields = sorted(
        (
            (field_name, field_data)
            for field_name, field_data in data[index_name]["fields"].items()
            if not field_name.startswith("_")
        ),
        key=lambda x: x[1]["total_in_bytes"],
        reverse=True,
    )
    return {field_name: field_data for field_name, field_data in sorted_fields}


if __name__ == "__main__":
    data = json.load(sys.stdin)
    sorted_fields = get_fields_sorted_by_disk_usage(data)
    print(json.dumps(sorted_fields, indent=2))
