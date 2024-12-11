# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Mapping, Union

from pydantic import Field

import collections
import pyarrow as pa

from kiara.exceptions import KiaraProcessingException
from kiara.models.values.value import Value, ValueMap
from kiara.modules import KiaraModule, ValueMapSchema
from kiara.modules.included_core_modules.create_from import (
    CreateFromModule,
    CreateFromModuleConfig,
)
from kiara_plugin.tropy.defaults import (
    DEFAULT_SOURCE_COLUMN_NAME,
    DEFAULT_TARGET_COLUMN_NAME,
    GraphType
)
from kiara_plugin.tropy.models import NetworkGraph

if TYPE_CHECKING:
    from kiara.models.filesystem import (
        KiaraFile,
    )
    from kiara_plugin.tabular.models import KiaraTable

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
                graph_type=GraphType("undirected"),
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        UNDIRECTED = UNDIRECTED.as_networkx_graph()

        DIRECTED = NetworkGraph.create_from_tables(
                graph_type=GraphType("directed"),
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        DIRECTED = DIRECTED.as_networkx_graph()

        UNDIRECTED_MULTI = NetworkGraph.create_from_tables(
                graph_type=GraphType("undirected_multi"),
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        UNDIRECTED_MULTI = UNDIRECTED_MULTI.as_networkx_graph()

        DIRECTED_MULTI = NetworkGraph.create_from_tables(
                graph_type=GraphType("directed_multi"),
                edges_table=edges,
                source_column_name=source_column,
                target_column_name=target_column
                )
        DIRECTED_MULTI = DIRECTED_MULTI.as_networkx_graph()

        info = (
            'Number of Nodes: ' + str(UNDIRECTED.number_of_nodes()) + '\n \n' 
            + 'Number of Edges by Graph Type:' + '\n'
            + '     Undirected Graph:       ' + str(UNDIRECTED.number_of_edges()) + '\n'
            + '     Directed Graph:         ' + str(DIRECTED.number_of_edges()) + '\n'
            + '     Undirected Multigraph:  ' + str(UNDIRECTED_MULTI.number_of_edges()) + '\n'
            + '     Directed Multigraph:    ' + str(DIRECTED_MULTI.number_of_edges()) + '\n \n'
            + 'Number of Self-Loops:    ' + str(nx.number_of_selfloops(UNDIRECTED)) + '\n \n'
            + 'Number of Isolates:      ' + str(nx.number_of_isolates(UNDIRECTED)) + '\n \n'
            + 'Number of Components:    ' + str(nx.number_connected_components(UNDIRECTED))
            )
        
        if DIRECTED.number_of_edges() > UNDIRECTED.number_of_edges():
            info = (info + '\n \nYou have more edges in a directed graph than in an undirected graph. \nThis means you have reciprocal edges between at least one pair of nodes. If this doesn\'t sound correct for your datatype, please recheck your data.')

        if DIRECTED_MULTI.number_of_edges() > DIRECTED.number_of_edges():
            info = (info + '\n \nYou have more edges in a multi graph than in an directed or undirected graph. \nThis means you have parallel edges between at least one pair of nodes. For more options on how to handle parallel edges, see the \'assemble.network_graph\' module. If this doesn\'t sound correct for your datatype, please recheck your data.')

        outputs.set_values(preview=info)