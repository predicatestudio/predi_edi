from predi.api import load
from predi.tests import SAMPLE_DIR
from predi.transactions import load_mapping
from predi.transactions.mapping.x12 import X12_Mapper

from .samples.maps.amz_850.amz_850 import amz850_map


def test_load_mapping():
    json_map = load_mapping(SAMPLE_DIR / "maps" / "amz_850" / "amz_850_map.json")

    for json_attr, python_attr in zip(json_map, amz850_map):
        assert json_attr == python_attr


def test_X12_Mapper():
    mapper = X12_Mapper(amz850_map)
    x12_file = SAMPLE_DIR / "transactions" / "x12" / "850" / "amz_ex.edi"
    assert mapper.parse_data(load(x12_file.open()))
