# -*- coding: utf-8 -*-

"""This module contains the metadata (and other) models that are used in the ``kiara_plugin.tropy`` package.

Those models are convenience wrappers that make it easier for *kiara* to find, create, manage and version metadata -- but also
other type of models -- that is attached to data, as well as *kiara* modules.

Metadata models must be a sub-class of [kiara.metadata.MetadataModel][kiara.metadata.MetadataModel]. Other models usually
sub-class a pydantic BaseModel or implement custom base classes.
"""

import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Iterable,
    Literal,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field

from kiara.exceptions import KiaraException
from kiara.models.values.value import Value
from kiara.models.values.value_metadata import ValueMetadata
from kiara.utils import log_message
from kiara_plugin.tabular.models.table import KiaraTable
from kiara_plugin.tabular.models.tables import KiaraTables
from kiara_plugin.tropy.defaults import (
    DEFAULT_NODE_ID_COLUMN_NAME,
    DEFAULT_SOURCE_COLUMN_NAME,
    DEFAULT_TARGET_COLUMN_NAME,
    EDGES_TABLE_NAME,
    NODES_TABLE_NAME,
    GraphType,
)

if TYPE_CHECKING:
    import networkx as nx
    import pyarrow as pa


NETWORKX_GRAPH_TYPE = TypeVar("NETWORKX_GRAPH_TYPE", bound="nx.Graph")


class NetworkGraph(KiaraTables):
    """A wrapper class to access and query network graph data."""

    _kiara_model_id: ClassVar = "instance.network_graph"

    @classmethod
    def create_from_kiara_tables(
        cls,
        graph_type: GraphType,
        tables: KiaraTables,
        source_column_name: str = DEFAULT_SOURCE_COLUMN_NAME,
        target_column_name: str = DEFAULT_TARGET_COLUMN_NAME,
        node_id_column_name: str = DEFAULT_NODE_ID_COLUMN_NAME,
    ) -> "NetworkGraph":
        if EDGES_TABLE_NAME not in tables.tables.keys():
            raise KiaraException(
                f"Can't import network data: no '{EDGES_TABLE_NAME}' table found"
            )

        if NODES_TABLE_NAME not in tables.tables.keys():
            nodes_table: Union[KiaraTable, None] = None
        else:
            nodes_table = tables.tables[NODES_TABLE_NAME]

        return cls.create_from_tables(
            graph_type=graph_type,
            edges_table=tables.tables[EDGES_TABLE_NAME],
            nodes_table=nodes_table,
            source_column_name=source_column_name,
            target_column_name=target_column_name,
            node_id_column_name=node_id_column_name,
        )

    @classmethod
    def create_from_tables(
        cls,
        graph_type: GraphType,
        edges_table: Any,
        nodes_table: Union[Any, None] = None,
        source_column_name: str = DEFAULT_SOURCE_COLUMN_NAME,
        target_column_name: str = DEFAULT_TARGET_COLUMN_NAME,
        node_id_column_name: str = DEFAULT_NODE_ID_COLUMN_NAME,
    ) -> "NetworkGraph":

        edges_table = KiaraTable.create_table(edges_table)
        nodes_table = KiaraTable.create_table(nodes_table) if nodes_table else None

        edges_columns = edges_table.column_names
        if source_column_name not in edges_columns:
            raise Exception(
                f"Invalid 'network_data' value: 'edges' table does not contain a '{source_column_name}' column. Available columns: {', '.join(edges_columns)}."
            )
        if target_column_name not in edges_columns:
            raise Exception(
                f"Invalid 'network_data' value: 'edges' table does not contain a '{target_column_name}' column. Available columns: {', '.join(edges_columns)}."
            )

        if not nodes_table:
            import duckdb

            edges: pa.Table = edges_table.arrow_table  # noqa

            sql_query = f"""
            SELECT DISTINCT combined.{node_id_column_name}
            FROM (
                 SELECT {source_column_name} AS {node_id_column_name} FROM edges
                 UNION
                 SELECT {target_column_name} AS {node_id_column_name} FROM edges
            ) AS combined
            ORDER BY combined.{node_id_column_name}
            """

            con = duckdb.connect()
            result = con.execute(sql_query)
            nodes_table_arrow = result.arrow()
            nodes_table = KiaraTable.create_table(nodes_table_arrow)
        else:
            nodes_columns = nodes_table.column_names
            if node_id_column_name not in nodes_columns:
                raise Exception(
                    f"Invalid 'network_data' value: 'nodes' table does not contain a '{node_id_column_name}' column. Available columns: {', '.join(nodes_columns)}."
                )

        graph = NetworkGraph(
            graph_type=graph_type.value,
            source_column_name=source_column_name,
            target_column_name=target_column_name,
            node_id_column_name=node_id_column_name,
            tables={EDGES_TABLE_NAME: edges_table, NODES_TABLE_NAME: nodes_table},
        )

        return graph

    @classmethod
    def create_from_networkx_graph(
        cls,
        graph: NETWORKX_GRAPH_TYPE,
        source_column_name: str = DEFAULT_SOURCE_COLUMN_NAME,
        target_column_name: str = DEFAULT_TARGET_COLUMN_NAME,
        node_id_column_name: str = DEFAULT_NODE_ID_COLUMN_NAME,
    ) -> "NetworkGraph":
        """Create a `NetworkGraph` instance from a networkx Graph object."""

        import networkx as nx
        import pandas as pd

        if isinstance(graph, nx.MultiDiGraph):
            graph_type = GraphType.DIRECTED_MULTI
        elif isinstance(graph, nx.MultiGraph):
            graph_type = GraphType.UNDIRECTED_MULTI
        elif isinstance(graph, nx.DiGraph):
            graph_type = GraphType.DIRECTED
        elif isinstance(graph, nx.Graph):
            graph_type = GraphType.UNDIRECTED
        else:
            raise KiaraException(f"Invalid graph type: {type(graph)}")

        temp_source = str(uuid.uuid4())
        temp_target = str(uuid.uuid4())

        edges_df = nx.to_pandas_edgelist(graph, source=temp_source, target=temp_target)
        if source_column_name in edges_df.columns:
            # remove the column
            log_message(
                "graph.create.drop_column",
                column=source_column_name,
                reason="Source column name specified by user.",
            )
            edges_df = edges_df.drop(source_column_name, axis=1)
            edges_df = edges_df.rename(columns={temp_source: source_column_name})
        if target_column_name in edges_df.columns:
            # remove the column
            log_message(
                "graph.create.drop_column",
                column=target_column_name,
                reason="Target column name specified by user.",
            )
            edges_df = edges_df.drop(target_column_name, axis=1)
            edges_df = edges_df.rename(columns={temp_target: target_column_name})
        edges_table = KiaraTable.create_table(edges_df)

        node_dict = {
            k: v if v else {"_x_placeholder_x_": "__dummy__"}
            for k, v in graph.nodes(data=True)
        }

        nodes_data = pd.DataFrame.from_dict(node_dict, orient="index")
        nodes_data = nodes_data.reset_index()

        if "_x_placeholder_x_" in nodes_data.columns:
            nodes_data = nodes_data.drop("_x_placeholder_x_", axis=1)

        if node_id_column_name in nodes_data.columns:
            # remove index column if it exists
            nodes_data = nodes_data.drop("index", axis=1)
        else:
            nodes_data = nodes_data.rename(columns={"index": node_id_column_name})

        nodes_table = KiaraTable.create_table(nodes_data)

        return cls.create_from_tables(
            graph_type=graph_type,
            edges_table=edges_table,
            nodes_table=nodes_table,
            source_column_name=source_column_name,
            target_column_name=target_column_name,
            node_id_column_name=node_id_column_name,
        )

    source_column_name: str = Field(
        description="The name of the column in the edges table that contains the source node id."
    )
    target_column_name: str = Field(
        description="The name of the column in the edges table that contains the target node id."
    )
    node_id_column_name: str = Field(
        description="The name of the column in the nodes table that contains the node id."
    )
    graph_type: Literal[
        "directed", "undirected", "directed_multi", "undirected_multi"
    ] = Field(
        description="The type of the graph (directed, undirected, directed_multi, undirected_multi)."
    )

    @property
    def edges(self) -> "KiaraTable":
        """Return the edges table."""

        return self.tables[EDGES_TABLE_NAME]

    @property
    def nodes(self) -> "KiaraTable":
        """Return the nodes table."""

        return self.tables[NODES_TABLE_NAME]

    @property
    def num_nodes(self):
        """Return the number of nodes in the network data."""

        return self.nodes.num_rows

    @property
    def num_edges(self):
        """Return the number of edges in the network data."""

        return self.edges.num_rows

    def query(self, sql_query: str) -> "pa.Table":
        """Query the edges and nodes tables using SQL.

        The table names to use in the query are 'edges' and 'nodes'.
        """

        import duckdb

        con = duckdb.connect()
        edges = self.edges.arrow_table  # noqa
        nodes = self.nodes.arrow_table  # noqa

        result = con.execute(sql_query)
        return result.arrow()

    def as_networkx_graph(
        self,
    ) -> Union["nx.Graph", "nx.DiGraph", "nx.MultiGraph", "nx.MultiDiGraph"]:
        """Return the network data as a networkx graph object."""

        import networkx as nx

        if self.graph_type == GraphType.DIRECTED.value:
            graph_type = nx.DiGraph
        elif self.graph_type == GraphType.UNDIRECTED.value:
            graph_type = nx.Graph
        elif self.graph_type == GraphType.DIRECTED_MULTI.value:
            graph_type = nx.MultiDiGraph
        elif self.graph_type == GraphType.UNDIRECTED_MULTI.value:
            graph_type = nx.MultiGraph
        else:
            raise KiaraException("Invalid graph type: {self.graph_type}")

        graph = graph_type()

        # this is all fairly wateful in terms of memory, but since we are using networkx for everything
        # now, it probably doesn't matter much

        # Add nodes
        nodes_df = self.nodes.arrow_table.to_pandas()
        for idx, row in nodes_df.iterrows():
            graph.add_node(row[self.node_id_column_name], **row.to_dict())

        # Add edges
        edges_df = self.edges.arrow_table.to_pandas()
        for idx, row in edges_df.iterrows():
            graph.add_edge(
                row[self.source_column_name],
                row[self.target_column_name],
                **row.to_dict(),
            )

        return graph


class GraphProperties(BaseModel):
    """Properties of graph data, if interpreted as a specific graph type."""

    number_of_edges: int = Field(description="The number of edges.")
    parallel_edges: int = Field(
        description="The number of parallel edges (if 'multi' graph type).", default=0
    )


class NetworkGraphProperties(ValueMetadata):
    """Network data stats."""

    _metadata_key: ClassVar[str] = "network_graph"

    number_of_nodes: int = Field(description="Number of nodes in the network graph.")
    number_of_edges: int = Field(description="Number of edges in the network graph.")

    @classmethod
    def retrieve_supported_data_types(cls) -> Iterable[str]:
        return ["network_graph"]

    @classmethod
    def create_value_metadata(cls, value: Value) -> "NetworkGraphProperties":

        network_graph: NetworkGraph = value.data

        graph = network_graph.as_networkx_graph()
        num_rows = graph.number_of_nodes()
        num_edges = len(graph.edges())

        result = cls(
            number_of_nodes=num_rows,
            number_of_edges=num_edges,
        )
        return result
