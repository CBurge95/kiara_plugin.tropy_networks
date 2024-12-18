import os

from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara_plugin.tropy.models import NetworkGraph
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
                "doc": "The network graph to be exported."
                },
            "file_type": {
                "type": "string",
                "type_config": {"allowed_strings": ALLOWED_EXPORT_TYPES_STRINGS},
                "doc": "The file type to be exported to."
            },
            "file_name": {
                "type": "string",
                "doc": "Name for the new file."
            },
            "file_path": {
                "type": "string",
                "doc" : "File path for the new file.",
                "optional": True
            }
        }
    
    def create_outputs_schema(self):
        return {
            "information": {
                "type": "string",
                "doc": "path for new file"
            }  
        }

    def process(self, inputs: ValueMap, outputs: ValueMap):

        import networkx as nx

        edges = inputs.get_value_obj("network_graph")
        file_type = inputs.get_value_data('file_type')
        name = inputs.get_value_data('file_name')
        path_name = inputs.get_value_data('file_path')

        network_data: NetworkGraph = edges.data

        if path_name != None:
            file_path = str(path_name + name)
        else:
            file_path = os.path.join(os.path.abspath(''), name)

        G = network_data.as_networkx_graph()

        if file_type == "graphml":
            nx.write_graphml(G, str(file_path + '.graphml'))

        if file_type == "gml":
            nx.write_gml(G, str(file_path + '.gml'), stringizer=str)

        if file_type == "gexf":
            nx.write_gexf(G, str(file_path + '.gexf'))

        if file_type == "adj_list":
            nx.write_adjlist(G, str(file_path + '.adjlist'))
        
        if file_type == "multi_adj_list":
            nx.write_multiline_adjlist(G, str(file_path +'.adjlist'))

        if file_type == "pajek":
            nx.write_pajek(G, str(file_path + '.pajek'))

        if file_type == "network_text":
            nx.write_network_text(G, str(file_path + '.txt'))

        

        outputs.set_value("information", file_path)