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


class CutPointsList(KiaraModule):
    """Finds and returns the largest component in a network. If there is only one component, this will return a warning message."""

    _module_type_name = "create.largest_component"

    def create_inputs_schema(self):
        return {
            "network_graph": {
                "type": "network_graph",
                "doc": "The network graph being queried.",
            }
        }

    def create_outputs_schema(self):
        return {
            "largest_component": {
                "type": "network_graph",
                "doc": "The largest connected component in the network.",
            },
        }

    def process(self, inputs: ValueMap, outputs: ValueMap):

        from kiara_plugin.tropy.models import NetworkGraph

        edges = inputs.get_value_obj("network_graph")

        import networkx as nx

        network_data: NetworkGraph = edges.data

        G = network_data.as_networkx_graph()
        Gcc = sorted(nx.connected_components(G.to_undirected()), key=len, reverse=True)
        largest = G.subgraph[Gcc[0]]
        if len(Gcc) == 1:
            raise KiaraProcessingException(
                    f"Graph only contains one component. Please use original network graph object as the largest component."
            )

        attribute_network = NetworkGraph.create_from_networkx_graph(
            largest,
            source_column_name=network_data.source_column_name,
            target_column_name=network_data.target_column_name,
            node_id_column_name=network_data.node_id_column_name)

        outputs.set_values(largest_component=attribute_network)
