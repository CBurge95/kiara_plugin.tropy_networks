import os

from kiara.api import KiaraModule
from kiara.models.values.value import ValueMap
from kiara_plugin.tropy.models import NetworkGraph
from kiara_plugin.tropy.defaults import (
    ALLOWED_EXPORT_TYPES_STRINGS,
    DEFAULT_SOURCE_COLUMN_NAME,
    DEFAULT_TARGET_COLUMN_NAME,
    GraphType
)

KIARA_METADATA = {
    "authors": [
        {"name": "Lena Jaskov", "email": "helena.jaskov@uni.lu"},
        {"name": "Caitlin Burge", "email": "caitlinburge@hotmail.co.uk"}
    ],
    "description": "Kiara modules for: network_analysis",
}

class Import_Networks(KiaraModule):
    """Offers options for importing network graph formats into kiara for use with kiara network analysis modules, using networkx. 
    Currently available formats are:
    - graphml ('graphml')
    - gml ('gml')
    - gexf ('gexf')
    - adjaceny list ('adj_list')
    - multiline adjacency list ('multi_adj_list')
    - pajek ('pajek')
    """
    
    _module_type_name = 'import.network_graph'

    def create_inputs_schema(self):
        return {
            "path": {
                "type": "string",
                "doc": "The path to the local file.",
                "optional": False,
            },
            "file_type": {
                "type": "string",
                "type_config": {"allowed_strings": ALLOWED_EXPORT_TYPES_STRINGS},
                "doc": "The file type being imported."
            },
            "label":{
                "type": "string",
                "doc": "The node attribute that holds the 'label' information. Set this input to 'id' when there is no 'label' attribute. (GML file only)",
                "optional": True,
                "default": "label",
            }
        }
    
    def create_outputs_schema(self):
        return {
            "network_graph": {
                "type": "network_graph",
                "doc": "The kiara network graph."
            }
        }
    
    def process(self, inputs: ValueMap, outputs: ValueMap):        
        import networkx as nx
        import pandas as pd
        import pyarrow as pa

        file_path = inputs.get_value_data('path')
        file_type = inputs.get_value_data('file_type')
        label = inputs.get_value_data('label')

        if file_type == "graphml":
            G = nx.read_graphml(file_path)

        if file_type == "gml":
            if label is None:
                G = nx.read_gml(file_path)
            else:
                G = nx.read_gml(file_path, label=label)

        if file_type == "gexf":
            G = nx.read_gexf(file_path)

        if file_type == "adj_list":
            G = nx.read_adjlist(file_path)
        
        if file_type == "multi_adj_list":
            G = nx.read_multiline_adjlist(file_path)

        if file_type == "pajek":
            G = nx.read_pajek(file_path)  

        if isinstance(G, nx.MultiDiGraph):
            graph_type = GraphType.DIRECTED_MULTI
        elif isinstance(G, nx.MultiGraph):
            graph_type = GraphType.UNDIRECTED_MULTI
        elif isinstance(G, nx.DiGraph):
            graph_type = GraphType.DIRECTED
        elif isinstance(G, nx.Graph):
            graph_type = GraphType.UNDIRECTED

        edges_table = nx.to_pandas_edgelist(G)
        edges_table: KiaraTable = edges_table



        edge_table_data = [[item[0] for item in G.edges()], [item[1] for item in G.edges()]]
        data_arrays = [pa.array(col) for col in edge_table_data]
        edge_table_cols = ['Source', 'Target']
        edge_table = pa.Table.from_arrays(data_arrays, names=edge_table_cols)

        network_graph = NetworkGraph.create_from_tables(
            graph_type=graph_type,
            edges_table=edges_table
        )
        
        outputs.set_values("network_graph",network_graph)