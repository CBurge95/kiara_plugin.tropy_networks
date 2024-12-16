import os

from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara_plugin.tropy.models import NetworkGraph
from kiara.modules.included_core_modules.export_as import DataExportModule
from kiara_plugin.tropy.defaults import ALLOWED_EXPORT_TYPES_STRINGS

KIARA_METADATA = {
    "authors": [
        {"name": "Caitlin Burge", "email": "caitlin.burge@uni.lu"},
    ],
    "description": "Kiara modules for: network_analysis",
}

class Export_Networks(KiaraModule):
    """Offers options for exporting a kiara network graph into other formats for use outside of kiara. 
    Currently available formats are:
    - graphml
    - gml
    - gexf
    - adjaceny list
    - multiline adjacency list
    - pajek
    - network text
    """

    _module_type_name = "export.network_graph"

    def create_inputs_schema(self):
        return {
            "network_graph": {
                "type": "network_graph",
                "doc": "The network graph to be exported."},
            "file_type": {
                "type": "string",
                "type_config": {"allowed_strings": ALLOWED_EXPORT_TYPES_STRINGS},
                "doc": "The file type to be exported to."
            },
            "file_name": {
                "type": "string",
                "doc": "Name for the new file."
            }
        }

    def process(self, inputs: ValueMap, outputs: ValueMap):

        import networkx as nx

        edges = inputs.get_value_obj("network_graph")
        file_type = inputs.get_value_data('file_type')
        name = inputs.get_value_data('file_name')

        network_data: NetworkGraph = edges.data

        G = network_data.as_networkx_graph()

        if file_type == "graphml":
            nx.write_graphml(G, str(name + '.graphml'))

        if file_type == "gml":
            nx.write_gml(G, str(name + '.gml'))

        if file_type == "gexf":
            nx.write_gexf(G, str(name + '.gexf'))

        if file_type == "adj_list":
            nx.write_adjlist(G, str(name + '.adjlist'))
        
        if file_type == "multi_adj_list":
            nx.write_multiline_adjlist(G, '.adjlist')

        if file_type == "pajek":
            nx.write_pajek(G, str(name + '.net'))

        if file_type == "network_text":
            nx.write_network_text(G, str(name + '.txt'))