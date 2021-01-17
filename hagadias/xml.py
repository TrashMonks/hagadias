import sys
# Force pure Python XML parser by nullifying the import
# in ElementTree that would normally shadow XMLParser with
# the C version. This lets us get line number info.
sys.modules['_elementtree'] = None
already_imported = 'xml.etree' in sys.modules
from xml.etree import ElementTree  # noqa E402
from xml.etree.ElementTree import Element  # noqa E402
if already_imported:
    import importlib  # noqa E402
    importlib.reload(ElementTree)
