"""Dependency graph visualization using interactive network graph."""

import os
import tempfile
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QComboBox,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from pyvis.network import Network
from app.db_accessor import DatabaseAccessor


@dataclass
class GraphNode:
    """Represents a node in the dependency graph."""
    node_id: str
    name: str
    schema: str
    node_type: str
    is_unresolved: bool = False

    @property
    def display_name(self) -> str:
        """Get fully qualified name."""
        return f"{self.schema}.{self.name}"


class CycleDetector:
    """Detects cycles in dependency graph using DFS."""

    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph
        self.cycles: List[List[str]] = []
        self._detect_cycles()

    def _detect_cycles(self):
        """Find all cycles in graph."""
        visited = set()

        for node in self.graph:
            if node not in visited:
                self._dfs(node, visited, set(), [])

    def _dfs(self, node: str, visited: Set[str], rec_stack: Set[str], path: List[str]):
        """DFS to detect cycles."""
        rec_stack.add(node)
        path.append(node)

        for neighbor in self.graph.get(node, []):
            if neighbor not in rec_stack:
                if neighbor not in visited:
                    self._dfs(neighbor, visited, rec_stack, path)
            else:
                cycle_start_idx = path.index(neighbor)
                cycle = path[cycle_start_idx:] + [neighbor]
                self.cycles.append(cycle)

        visited.add(node)
        rec_stack.remove(node)
        path.pop()

    def get_cycle_nodes(self) -> Set[str]:
        """Get all nodes that are part of any cycle."""
        nodes = set()
        for cycle in self.cycles:
            nodes.update(cycle[:-1])
        return nodes

    def get_cycle_edges(self) -> Set[Tuple[str, str]]:
        """Get edges that form cycle paths."""
        edges = set()
        for cycle in self.cycles:
            for i in range(len(cycle) - 1):
                edges.add((cycle[i], cycle[i + 1]))
        return edges


class GraphBuilder:
    """Builds dependency graph from database queries."""

    def __init__(self, accessor: DatabaseAccessor, database: str):
        self.accessor = accessor
        self.database = database
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, List[str]] = {}
        self.visited: Set[str] = set()
        self.max_depth = 3

    def _make_node_id(self, schema: str, name: str) -> str:
        """Create unique node ID."""
        return f"{schema}.{name}"

    def build(self, schema: str, routine_name: str, direction: str = "both",
              depth: int = 1) -> Tuple[Dict[str, GraphNode], Dict[str, List[str]]]:
        """Build graph starting from routine.

        Args:
            schema: Schema containing routine
            routine_name: Routine name
            direction: "callers", "callees", or "both"
            depth: Recursion depth (1-3)
        """
        self.max_depth = min(depth, 3)
        self.nodes.clear()
        self.edges.clear()
        self.visited.clear()

        root_id = self._make_node_id(schema, routine_name)
        root_node = GraphNode(
            node_id=root_id,
            name=routine_name,
            schema=schema,
            node_type="PROCEDURE"
        )
        self.nodes[root_id] = root_node
        self.edges[root_id] = []

        if direction in ("callees", "both"):
            self._load_callees(schema, routine_name, depth=1)
        if direction in ("callers", "both"):
            self._load_callers(schema, routine_name, depth=1)

        return self.nodes, self.edges

    def _load_callees(self, schema: str, routine_name: str, depth: int):
        """Load procedures/functions called by this routine."""
        if depth > self.max_depth:
            return

        node_id = self._make_node_id(schema, routine_name)

        try:
            deps = self.accessor.get_called_procedures(self.database, schema, routine_name)
            for dep in deps:
                child_id = self._make_node_id(dep['schema'], dep['name'])

                if child_id not in self.nodes:
                    self.nodes[child_id] = GraphNode(
                        node_id=child_id,
                        name=dep['name'],
                        schema=dep['schema'],
                        node_type=dep['type'],
                        is_unresolved=False
                    )

                if node_id not in self.edges:
                    self.edges[node_id] = []
                if child_id not in self.edges[node_id]:
                    self.edges[node_id].append(child_id)

                if child_id not in self.edges:
                    self.edges[child_id] = []

                if depth < self.max_depth and child_id not in self.visited:
                    self.visited.add(child_id)
                    self._load_callees(dep['schema'], dep['name'], depth + 1)
        except Exception:
            pass

    def _load_callers(self, schema: str, routine_name: str, depth: int):
        """Load procedures/functions that call this routine."""
        if depth > self.max_depth:
            return

        node_id = self._make_node_id(schema, routine_name)

        try:
            callers = self.accessor.get_calling_procedures(self.database, schema, routine_name)
            for caller in callers:
                parent_id = self._make_node_id(caller['schema'], caller['name'])

                if parent_id not in self.nodes:
                    self.nodes[parent_id] = GraphNode(
                        node_id=parent_id,
                        name=caller['name'],
                        schema=caller['schema'],
                        node_type=caller['type'],
                        is_unresolved=False
                    )

                if parent_id not in self.edges:
                    self.edges[parent_id] = []
                if node_id not in self.edges[parent_id]:
                    self.edges[parent_id].append(node_id)

                if node_id not in self.edges:
                    self.edges[node_id] = []

                if depth < self.max_depth and parent_id not in self.visited:
                    self.visited.add(parent_id)
                    self._load_callers(caller['schema'], caller['name'], depth + 1)
        except Exception:
            pass


class DependencyGraphWidget(QWidget):
    """Widget for displaying dependency graphs with pyvis."""

    def __init__(self, accessor: DatabaseAccessor, database: str):
        super().__init__()
        self.accessor = accessor
        self.database = database
        self.builder = GraphBuilder(accessor, database)
        self.cycle_detector: Optional[CycleDetector] = None
        self.current_routine = None
        self.web_view = None
        self.temp_html_path = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout(self)

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Both", "Callers", "Callees"])
        self.direction_combo.currentTextChanged.connect(self._on_direction_changed)
        controls_layout.addWidget(self.direction_combo)

        controls_layout.addWidget(QLabel("Depth:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setMinimum(1)
        self.depth_spin.setMaximum(3)
        self.depth_spin.setValue(1)
        self.depth_spin.valueChanged.connect(self._on_depth_changed)
        controls_layout.addWidget(self.depth_spin)

        self.refresh_btn = QPushButton("Refresh Graph")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        controls_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("Export DOT")
        self.export_btn.clicked.connect(self._on_export_clicked)
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view)
        self.setLayout(main_layout)

    def load_routine(self, schema: str, routine_name: str):
        """Load and display dependency graph for routine."""
        self.current_routine = (schema, routine_name)
        self._render_graph()

    def _on_direction_changed(self):
        """Handle direction combo change."""
        if self.current_routine:
            self._render_graph()

    def _on_depth_changed(self):
        """Handle depth spin change."""
        if self.current_routine:
            self._render_graph()

    def _on_refresh_clicked(self):
        """Handle refresh button."""
        if self.current_routine:
            self._render_graph()

    def _render_graph(self):
        """Render dependency graph using pyvis."""
        if not self.current_routine:
            return

        schema, routine_name = self.current_routine
        direction_map = {
            "Both": "both",
            "Callers": "callers",
            "Callees": "callees"
        }
        direction = direction_map.get(self.direction_combo.currentText(), "both")
        depth = self.depth_spin.value()

        nodes, edges = self.builder.build(schema, routine_name, direction, depth)

        self.cycle_detector = CycleDetector(edges)
        cycle_nodes = self.cycle_detector.get_cycle_nodes()
        cycle_edges = self.cycle_detector.get_cycle_edges()

        net = Network(directed=True, notebook=False, height="100%", width="100%",
                      cdn_resources='in_line')

        for node_id, node in nodes.items():
            color = "#ff6b6b" if node_id in cycle_nodes else "#4ecdc4"
            if node_id == f"{schema}.{routine_name}":
                color = "#ffe66d"

            net.add_node(
                node_id,
                label=node.display_name,
                title=f"{node.node_type} ({node.schema}.{node.name})",
                color=color,
                size=25
            )

        for source, targets in edges.items():
            for target in targets:
                if (source, target) in cycle_edges:
                    net.add_edge(source, target, color="#ff4444", width=3, title="Cycle edge")
                else:
                    net.add_edge(source, target, color="#cccccc", width=1)

        net.show_buttons(filter_=['physics'])

        self.temp_html_path = os.path.join(tempfile.gettempdir(), f"proc_viz_graph_{id(self)}.html")
        with open(self.temp_html_path, 'w', encoding='utf-8') as f:
            f.write(net.html)

        self.web_view.load(f"file://{self.temp_html_path}")

    def _on_export_clicked(self):
        """Export graph as DOT format."""
        if not self.current_routine:
            return

        schema, routine_name = self.current_routine
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", f"{routine_name}_graph.dot",
            "Graphviz Files (*.dot);;All Files (*)"
        )

        if not filename:
            return

        try:
            nodes, edges = self.builder.nodes, self.builder.edges
            with open(filename, 'w') as f:
                f.write("digraph proc_dependencies {\n")
                f.write("    rankdir=LR;\n")

                for node_id, node in nodes.items():
                    label = node.display_name
                    node_type = node.node_type.lower()
                    f.write(f"    \"{node_id}\" [label=\"{label}\", shape=box];\n")

                for source, targets in edges.items():
                    for target in targets:
                        f.write(f"    \"{source}\" -> \"{target}\";\n")

                f.write("}\n")

            QMessageBox.information(self, "Export Successful", f"Graph exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting graph:\n{str(e)}")

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_html_path and os.path.exists(self.temp_html_path):
            try:
                os.remove(self.temp_html_path)
            except Exception:
                pass
