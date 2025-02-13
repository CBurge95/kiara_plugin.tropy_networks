# -*- coding: utf-8 -*-
from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara.exceptions import KiaraProcessingException

KIARA_METADATA = {
    "authors": [
        {"name": "Caitlin Burge", "email": "caitlin.burge@uni.lu"},
    ],
    "description": "Kiara modules for: network_analysis",
}


class AveragePath(KiaraModule):
    """Finds and returns the average path of the component entered. If there are more than one component present, this will return an error message."""

    _module_type_name = "calculate.average_path"

    def create_inputs_schema(self):
        return {
            "network_component": {
                "type": "network_graph",
                "doc": "The network component being queried.",
            }
        }

    def create_outputs_schema(self):
        return {
            "path": {
                "type": "string",
                "doc": "The length of the average shortest path length for the component.",
            },
        }
    
    def process(self, inputs: ValueMap, outputs: ValueMap):

        import networkx as nx
        from kiara_plugin.tropy.models import NetworkGraph

        edges = inputs.get_value_obj("network_component")

        network_data: NetworkGraph = edges.data

        G = network_data.as_networkx_graph()
        if len(nx.connected_components(G.to_undirected())) > 1:
            raise KiaraProcessingException(
                    f"Graph contains more than one component. Please choose either the largest component or a graph with only one component."
            )
        
        if nx.is_weighted(G, weight='weight') == True:
            weights = True
        else:
            weights = False
        
        path = nx.average_shortest_path_length(G.to_undirected(), weighted=weights)

        outputs.set_values(path=path)
