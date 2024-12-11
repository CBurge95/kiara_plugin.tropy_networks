# -*- coding: utf-8 -*-
from operator import itemgetter

from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara_plugin.tropy.defaults import (
    DEFAULT_SOURCE_COLUMN_NAME,
    DEFAULT_TARGET_COLUMN_NAME
)

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
            "source_column": {
                "type": "string",
                "doc": "The name of the source column name in the edges table.",
                "optional": False,
                "default": DEFAULT_SOURCE_COLUMN_NAME,
            },
            "target_column": {
                "type": "string",
                "doc": "The name of the target column name in the edges table.",
                "optional": False,
                "default": DEFAULT_TARGET_COLUMN_NAME,
            }
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
        source_column = inputs.get_value_data("source_column")
        target_column = inputs.get_value_data("target_column")
    
        UNDIRECTED = NetworkGraph.create_from_tables(
                graph_type="undirected",
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        UNDIRECTED = kiara_graph.as_networkx_graph()

        DIRECTED = NetworkGraph.create_from_tables(
                graph_type="directed",
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        DIRECTED = kiara_graph.as_networkx_graph()

        UNDIRECTED_MULTI = NetworkGraph.create_from_tables(
                graph_type="undirected_multi",
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        UNDIRECTED_MULTI = kiara_graph.as_networkx_graph()

        DIRECTED_MULTI = NetworkGraph.create_from_tables(
                graph_type="directed_multi",
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        DIRECTED_MULTI = kiara_graph.as_networkx_graph()

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
        
        if DIRECTED.number_of_edges() > UNDIRECTED.number_of_edges():
            info = (info + '\n \n You have reciprocal edges')

        if DIRECTED_MULTI.number_of_edges() > DIRECTED.number_of_edges():
            info = (info + '\n \n You have parallel edges')

        outputs.set_values(preview=info)