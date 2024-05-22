#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import gzip
import io
import json
import logging
import zipfile
from dataclasses import InitVar, dataclass
from typing import Any, Iterable, Mapping, MutableMapping, Iterator, NamedTuple, List
from collections import defaultdict
from time import sleep

import pendulum
import requests
from airbyte_cdk.sources.declarative.decoders.decoder import Decoder
from airbyte_cdk.sources.declarative.decoders.json_decoder import JsonDecoder
from airbyte_cdk.sources.declarative.extractors.record_extractor import RecordExtractor
from airbyte_cdk.sources.declarative.schema.json_file_schema_loader import JsonFileSchemaLoader
from airbyte_cdk.sources.declarative.types import Config, Record

logger = logging.getLogger("airbyte")

class MixpanelExportExtractor(RecordExtractor):
    """
    Create records from complex response structure
    Issue: https://github.com/airbytehq/airbyte/issues/23145
    """
    """Export API return response in JSONL format but each line is a valid JSON object
    Raw item example:
        {
            "event": "Viewed E-commerce Page",
            "properties": {
                "time": 1623860880,
                "distinct_id": "1d694fd9-31a5-4b99-9eef-ae63112063ed",
                "$browser": "Chrome",                                           -> will be renamed to "browser"
                "$browser_version": "91.0.4472.101",
                "$current_url": "https://unblockdata.com/solutions/e-commerce/",
                "$insert_id": "c5eed127-c747-59c8-a5ed-d766f48e39a4",
                "$mp_api_endpoint": "api.mixpanel.com",
                "mp_lib": "Segment: analytics-wordpress",
                "mp_processing_time_ms": 1623886083321,
                "noninteraction": true
            }
        }
    """
    decoder: Decoder = JsonDecoder(parameters={})

    def _get_schema_root_properties(self):
        schema_loader = JsonFileSchemaLoader(config=self.config, parameters={"name": self.name})
        schema = schema_loader.get_json_schema()
        return schema["properties"]

    def extract_records(self, response: requests.Response) -> List[Record]:
        items = []
#        logger.info(response)
        response_body = self.decoder.decode(response)
        for record in response_body['results']:
#            logger.info(record)
            # transform record into flat dict structure

            record_id = record['id']
            for property_name, history_list in record['propertiesWithHistory'].items():
                    for history in history_list:
                        item = {
                            "id": str(record_id),
                            "property": str(property_name),
                            **history
                        }
                        items.append(item)
        return items
