"""Tests for dependency graph visualization."""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from app.db_accessor import DatabaseAccessor
from app.widgets.dependency_graph import (
    GraphNode, CycleDetector, GraphBuilder, DependencyGraphWidget
)


@pytest.fixture
def qapp():
    """Qt application fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_accessor():
    """Mock database accessor."""
    accessor = MagicMock(spec=DatabaseAccessor)
    return accessor


@pytest.fixture
def graph_builder(mock_accessor):
    """Graph builder fixture."""
    return GraphBuilder(mock_accessor, "TestDB")


class TestGraphNode:
    """Tests for GraphNode."""

    def test_graph_node_creation(self):
        """Test node creation."""
        node = GraphNode("dbo.sp_test", "sp_test", "dbo", "PROCEDURE")
        assert node.node_id == "dbo.sp_test"
        assert node.display_name == "dbo.sp_test"

    def test_unresolved_node(self):
        """Test unresolved node."""
        node = GraphNode("dbo.unknown", "unknown", "dbo", "PROCEDURE", is_unresolved=True)
        assert node.is_unresolved


class TestCycleDetector:
    """Tests for cycle detection."""

    def test_no_cycles(self):
        """Test graph with no cycles."""
        graph = {
            "a": ["b"],
            "b": ["c"],
            "c": []
        }
        detector = CycleDetector(graph)
        assert detector.get_cycle_nodes() == set()
        assert detector.get_cycle_edges() == set()

    def test_simple_cycle(self):
        """Test simple 2-node cycle."""
        graph = {
            "a": ["b"],
            "b": ["a"]
        }
        detector = CycleDetector(graph)
        cycle_nodes = detector.get_cycle_nodes()
        assert "a" in cycle_nodes
        assert "b" in cycle_nodes

    def test_complex_cycle(self):
        """Test 3-node cycle."""
        graph = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"]
        }
        detector = CycleDetector(graph)
        cycle_nodes = detector.get_cycle_nodes()
        assert "a" in cycle_nodes
        assert "b" in cycle_nodes
        assert "c" in cycle_nodes

    def test_cycle_with_linear_tail(self):
        """Test cycle with nodes outside cycle."""
        graph = {
            "x": ["a"],
            "a": ["b"],
            "b": ["a", "z"],
            "z": []
        }
        detector = CycleDetector(graph)
        cycle_nodes = detector.get_cycle_nodes()
        assert "a" in cycle_nodes
        assert "b" in cycle_nodes
        assert "x" not in cycle_nodes


class TestGraphBuilder:
    """Tests for graph building."""

    def test_build_empty_dependencies(self, graph_builder, mock_accessor):
        """Test building graph with no dependencies."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = []

        nodes, edges = graph_builder.build("dbo", "sp_test", "both", 1)

        assert len(nodes) == 1
        assert "dbo.sp_test" in nodes
        assert nodes["dbo.sp_test"].name == "sp_test"

    def test_build_callees_only(self, graph_builder, mock_accessor):
        """Test building callees graph."""
        mock_accessor.get_called_procedures.return_value = [
            {"schema": "dbo", "name": "sp_child", "type": "PROCEDURE"}
        ]
        mock_accessor.get_calling_procedures.return_value = []

        nodes, edges = graph_builder.build("dbo", "sp_parent", "callees", 1)

        assert len(nodes) == 2
        assert "dbo.sp_parent" in nodes
        assert "dbo.sp_child" in nodes
        assert "dbo.sp_parent" in edges
        assert "dbo.sp_child" in edges["dbo.sp_parent"]

    def test_build_callers_only(self, graph_builder, mock_accessor):
        """Test building callers graph."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = [
            {"schema": "dbo", "name": "sp_caller", "type": "PROCEDURE"}
        ]

        nodes, edges = graph_builder.build("dbo", "sp_child", "callers", 1)

        assert len(nodes) == 2
        assert "dbo.sp_child" in nodes
        assert "dbo.sp_caller" in nodes
        assert "dbo.sp_caller" in edges
        assert "dbo.sp_child" in edges["dbo.sp_caller"]

    def test_build_respects_max_depth(self, graph_builder, mock_accessor):
        """Test depth limit is respected."""
        mock_accessor.get_called_procedures.return_value = [
            {"schema": "dbo", "name": "sp_b", "type": "PROCEDURE"}
        ]

        nodes, edges = graph_builder.build("dbo", "sp_a", "callees", 1)

        assert len(nodes) == 2
        assert "dbo.sp_a" in nodes
        assert "dbo.sp_b" in nodes

    def test_build_both_directions(self, graph_builder, mock_accessor):
        """Test building graph in both directions."""
        mock_accessor.get_called_procedures.return_value = [
            {"schema": "dbo", "name": "sp_child", "type": "PROCEDURE"}
        ]
        mock_accessor.get_calling_procedures.return_value = [
            {"schema": "dbo", "name": "sp_parent", "type": "PROCEDURE"}
        ]

        nodes, edges = graph_builder.build("dbo", "sp_middle", "both", 1)

        assert len(nodes) == 3
        assert "dbo.sp_parent" in nodes
        assert "dbo.sp_middle" in nodes
        assert "dbo.sp_child" in nodes

    def test_cross_schema_names(self, graph_builder, mock_accessor):
        """Test fully qualified cross-schema names."""
        mock_accessor.get_called_procedures.return_value = [
            {"schema": "app", "name": "sp_app", "type": "PROCEDURE"}
        ]
        mock_accessor.get_calling_procedures.return_value = []

        nodes, edges = graph_builder.build("dbo", "sp_test", "both", 1)

        assert "app.sp_app" in nodes
        assert nodes["app.sp_app"].display_name == "app.sp_app"

    def test_duplicate_edges_removed(self, graph_builder, mock_accessor):
        """Test duplicate edges are removed."""
        mock_accessor.get_called_procedures.return_value = [
            {"schema": "dbo", "name": "sp_child", "type": "PROCEDURE"}
        ]
        mock_accessor.get_calling_procedures.return_value = []

        nodes, edges = graph_builder.build("dbo", "sp_parent", "both", 1)

        parent_edges = edges["dbo.sp_parent"]
        assert parent_edges.count("dbo.sp_child") == 1


class TestDependencyGraphWidget:
    """Tests for graph widget."""

    def test_widget_creation(self, qapp, mock_accessor):
        """Test widget initialization."""
        widget = DependencyGraphWidget(mock_accessor, "TestDB")
        assert widget.database == "TestDB"
        assert widget.current_routine is None

    def test_load_routine(self, qapp, mock_accessor):
        """Test loading routine."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = []

        widget = DependencyGraphWidget(mock_accessor, "TestDB")
        widget.load_routine("dbo", "sp_test")

        assert widget.current_routine == ("dbo", "sp_test")

    def test_direction_change_updates_graph(self, qapp, mock_accessor):
        """Test direction combo change triggers refresh."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = []

        widget = DependencyGraphWidget(mock_accessor, "TestDB")
        widget.load_routine("dbo", "sp_test")

        initial_callers_count = mock_accessor.get_calling_procedures.call_count
        widget.direction_combo.setCurrentText("Callers")

        assert mock_accessor.get_calling_procedures.call_count > initial_callers_count

    def test_depth_change_updates_graph(self, qapp, mock_accessor):
        """Test depth spin change triggers refresh."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = []

        widget = DependencyGraphWidget(mock_accessor, "TestDB")
        widget.load_routine("dbo", "sp_test")

        initial_call_count = mock_accessor.get_called_procedures.call_count
        widget.depth_spin.setValue(2)

        assert mock_accessor.get_called_procedures.call_count > initial_call_count

    def test_cleanup(self, qapp, mock_accessor):
        """Test cleanup removes temp files."""
        mock_accessor.get_called_procedures.return_value = []
        mock_accessor.get_calling_procedures.return_value = []

        widget = DependencyGraphWidget(mock_accessor, "TestDB")
        widget.load_routine("dbo", "sp_test")

        temp_path = widget.temp_html_path
        widget.cleanup()

        import os
        assert not os.path.exists(temp_path) or temp_path is None
