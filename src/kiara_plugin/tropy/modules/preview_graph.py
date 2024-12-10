# -*- coding: utf-8 -*-
from operator import itemgetter

from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara_plugin.tropy.defaults import ALLOWED_GRAPH_TYPE_STRINGS

KIARA_METADATA = {
    "authors": [
        {"name": "Caitlin Burge", "email": "caitlin.burge@uni.lu"},
    ],
    "description": "Kiara modules for: network_analysis",
}


class Preview_Network_Info(KiaraModule):

    """Preview for information on all graph types. Gives: Nodes, Edges, isolates, components, and self-loops"""

    _module_type_name = "preview.network_info"

    def create_inputs_schema(self):
        return {
            "edges": {
                "type": "table",
                "doc": "A table that contains the edges data.",
                "optional": False,
            },
        }

    def create_outputs_schema(self):
        return {
            "preview": {
                "type": "string",
                "doc": "Information for possible network graphs.",
            },
        }

    def process(self, inputs: ValueMap, outputs: ValueMap):

        import networkx as nx
        from kiara_plugin.tropy.models import NetworkGraph

        edges = inputs.get_value_obj("edges")
        graph_types = ALLOWED_GRAPH_TYPE_STRINGS

        def test_graph(graph):
            kiara_graph = NetworkGraph.create_from_tables(
                graph_type=graph,
                edges_table=edges,
                )
            G = kiara_graph.as_networkx_graph()
            return G
        
        for item in graph_types:
            globals()[item] = test_graph(item)

        info = (
            'Number of Nodes: ' + str(UNDIRECTED.number_of_nodes()) + '\n \n' 
            + 'Number of Edges by Graph Type:' + '\n'
            + '     Undirected Graph: ' + str(UNDIRECTED.number_of_edges()) + '\n'
            + '     Directed Graph: ' + str(DIRECTED.number_of_edges()) + '\n'
            + '     Undirected Multiraph: ' + str(UNDIRECTED_MULTI.number_of_edges()) + '\n'
            + '     Directed Multiraph: ' + str(DIRECTED_MULTI.number_of_edges()) + '\n \n'
            + 'Number of Self-Loops: ' + str(nx.number_of_selfloops(UNDIRECTED)) + '\n \n'
            + 'Number of Isolates: ' + str(nx.number_of_isolates(UNDIRECTED)) + '\n \n'
            + 'Number of Components: ' + str(nx.number_connected_components(UNDIRECTED))
            )

        outputs.set_values(preview=info)