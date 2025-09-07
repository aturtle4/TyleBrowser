from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt
from Tile import Tile


class Workspace(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)

        self.tiling_mode = "horizontal"
        self.root_splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.root_splitter)

        self.tiles = []
        self.active_tile_index = 0

        # start with one tile
        self.add_tile(["https://www.google.com"])

    # ---------------- Focus ----------------
    def move_focus(self, direction: int):
        if not self.tiles:
            return
        old = self.active_tile_index
        self.active_tile_index = (self.active_tile_index + direction) % len(self.tiles)
        self._update_tile_visuals(old, self.active_tile_index)

    def active_tile(self):
        return self.tiles[self.active_tile_index] if self.tiles else None

    def set_active_tile(self, tile: Tile):
        if tile not in self.tiles:
            return
        old = self.active_tile_index
        self.active_tile_index = self.tiles.index(tile)
        self._update_tile_visuals(old, self.active_tile_index)

    def _update_tile_visuals(self, old_idx: int, new_idx: int):
        if 0 <= old_idx < len(self.tiles):
            self.tiles[old_idx].update_stylesheet(False)
        if 0 <= new_idx < len(self.tiles):
            self.tiles[new_idx].update_stylesheet(True)
            w = self.tiles[new_idx].tabs.currentWidget()
            (w or self.tiles[new_idx]).setFocus()

    # ---------------- Tiles ----------------
    def add_tile(self, urls=None):
        # If explicit empty list → do not create tile
        if urls == []:
            return

        # Default URL = Google if nothing provided
        if urls is None:
            urls = ["https://www.google.com"]

        t = Tile(urls)
        t.on_empty = lambda: self.remove_tile(t)  # hook for deletion

        if self.tiling_mode == "bsp":
            self._add_tile_bsp(t)
        else:
            self.root_splitter.addWidget(t)
            self.tiles.append(t)
            # Initialize equal sizes only once
            if len(self.tiles) > 1:
                sizes = self.root_splitter.sizes()
                if not any(sizes):  # if sizes not initialized
                    self.root_splitter.setSizes([1] * len(self.tiles))

        old = self.active_tile_index
        self.active_tile_index = len(self.tiles) - 1
        self._update_tile_visuals(old, self.active_tile_index)

    def remove_tile(self, tile: Tile):
        """Remove a tile if it has no tabs, but keep at least one alive."""
        if tile not in self.tiles:
            return

        # If this is the only tile, replace with a fresh Google tile
        if len(self.tiles) == 1:
            parent = tile.parentWidget()
            if parent:
                parent_idx = parent.indexOf(tile)
                parent.widget(parent_idx).setParent(None)
            self.tiles.remove(tile)

            # Immediately create a fresh one
            self.add_tile(["https://www.google.com"])
            return

        # Otherwise just remove normally
        parent = tile.parentWidget()
        if parent:
            parent_idx = parent.indexOf(tile)
            parent.widget(parent_idx).setParent(None)

        self.tiles.remove(tile)

        # Adjust focus
        self.active_tile_index = min(self.active_tile_index, len(self.tiles) - 1)
        self._update_tile_visuals(-1, self.active_tile_index)

    def detach_tile(self, tile: Tile):
        """Detach a tile from this workspace and return it, without deleting."""
        if tile not in self.tiles:
            return None

        parent = tile.parentWidget()
        if parent:
            parent_idx = parent.indexOf(tile)
            parent.widget(parent_idx).setParent(None)

        self.tiles.remove(tile)
        self.active_tile_index = min(self.active_tile_index, len(self.tiles) - 1)
        self._update_tile_visuals(-1, self.active_tile_index)

        return tile


    def resize_active_tile(self, delta: int):
        """
        Resize the active tile inside its parent splitter.
        delta: pixels to grow (+) or shrink (-).
        """
        tile = self.active_tile()
        if not tile:
            return

        # find the direct parent splitter
        parent = tile.parentWidget()
        while parent and not isinstance(parent, QSplitter):
            parent = parent.parentWidget()
        if not isinstance(parent, QSplitter):
            return

        idx = parent.indexOf(tile)
        sizes = parent.sizes()
        if not (0 <= idx < len(sizes)):
            return

        new_sizes = sizes[:]
        change = delta

        # grow/shrink active tile
        new_sizes[idx] = max(10, sizes[idx] + change)

        # take/give space from/to a sibling
        for j in range(len(new_sizes)):
            if j != idx and new_sizes[j] > 10:
                new_sizes[j] = max(10, new_sizes[j] - change)
                break

        parent.setSizes(new_sizes)

    def update_tiles(self):
        """Rebuild self.tiles list by walking the splitter tree safely."""
        self.tiles.clear()

        visited = set()

        def walk(w):
            if w is None or id(w) in visited:
                return
            visited.add(id(w))

            if isinstance(w, Tile):
                self.tiles.append(w)
            elif isinstance(w, QSplitter):
                for i in range(w.count()):
                    walk(w.widget(i))

        walk(self.root_splitter)

        if not self.tiles:
            self.add_tile(["https://www.google.com"])

        self.active_tile_index = min(self.active_tile_index, len(self.tiles) - 1) if self.tiles else 0
        self._update_tile_visuals(-1, self.active_tile_index)


    # ---------------- Mode switching ----------------
    def set_tiling_mode(self, mode: str):
        if mode not in ("horizontal", "vertical", "bsp") or mode == self.tiling_mode:
            return
        self._rebuild_layout_preserving_sizes(mode)
        self.tiling_mode = mode
        self.update_tiles()

    # ---------------- Movement -----------------
    def move_tile(self, direction: str):
        """
        Move the active tile within this workspace.
        direction: 'left', 'right', 'up', 'down'
        """
        tile = self.active_tile()
        if not tile:
            return

        # climb to direct parent splitter
        parent = tile.parentWidget()
        while parent and not isinstance(parent, QSplitter):
            parent = parent.parentWidget()
        if not isinstance(parent, QSplitter):
            return

        idx = parent.indexOf(tile)
        if idx == -1:
            return

        horiz = parent.orientation() == Qt.Horizontal
        target_idx = None

        if horiz and direction == "left" and idx > 0:
            target_idx = idx - 1
        elif horiz and direction == "right" and idx < parent.count() - 1:
            target_idx = idx + 1
        elif not horiz and direction == "up" and idx > 0:
            target_idx = idx - 1
        elif not horiz and direction == "down" and idx < parent.count() - 1:
            target_idx = idx + 1

        if target_idx is not None:
            # swap active tile with sibling at target_idx
            sibling = parent.widget(target_idx)
            parent.insertWidget(idx, sibling)
            parent.insertWidget(target_idx, tile)
            parent.setSizes(parent.sizes())  # keep sizes stable
            return

        # If no sibling in this splitter, try climbing up
        grandparent = parent.parentWidget()
        while grandparent and not isinstance(grandparent, QSplitter):
            grandparent = grandparent.parentWidget()
        if isinstance(grandparent, QSplitter):
            # reinsert into grandparent at a new index based on direction
            parent_idx = grandparent.indexOf(parent)
            insert_pos = parent_idx
            if direction in ("right", "down"):
                insert_pos = parent_idx + 1
            grandparent.insertWidget(insert_pos, tile)
            grandparent.setSizes(grandparent.sizes())



    # ---------------- Utilities ----------------
    def _current_tile_weights(self, axis: str):
        """axis: 'H' (widths) or 'V' (heights)"""
        weights = []
        total = 0
        for t in self.tiles:
            s = t.size()
            w = s.width() if axis == 'H' else s.height()
            if w <= 0:
                w = 1
            weights.append(w)
            total += w
        if total <= 0:
            total = len(weights) or 1
            weights = [1] * len(weights)
        return weights, total

    def _detach_tree_recursively(self, widget):
        """
        Recursively detach all Tile widgets from their splitters,
        then detach (and schedule delete) the splitters themselves.
        Ensures Tiles remain alive and can be reattached safely.
        """
        if isinstance(widget, Tile):
            widget.setParent(None)
            return

        if isinstance(widget, QSplitter):
            # Detach children first
            children = [widget.widget(i) for i in range(widget.count())]
            for ch in children:
                if ch is not None:
                    self._detach_tree_recursively(ch)
            # Now detach this splitter from its parent and schedule delete
            widget.setParent(None)
            widget.deleteLater()

    def _clear_root(self):
        """Safely detach everything under root_splitter."""
        # Collect current top-level children and recursively detach them
        top_children = [self.root_splitter.widget(i) for i in range(self.root_splitter.count())]
        for ch in top_children:
            if ch is not None:
                self._detach_tree_recursively(ch)

        # Ensure root has no children left
        while self.root_splitter.count():
            w = self.root_splitter.widget(0)
            if w:
                w.setParent(None)

    def _rebuild_layout_preserving_sizes(self, target_mode: str):
        # Snapshot current tiles (order matters)
        self.update_tiles()
        tiles = self.tiles[:]
        if not tiles:
            return

        # Choose axis for weight sampling
        axis = 'H' if target_mode in ("horizontal", "bsp") else 'V'
        weights, total = self._current_tile_weights(axis)

        # SAFELY clear existing tree (recursively detach tiles before splitters die)
        self._clear_root()

        if target_mode in ("horizontal", "vertical"):
            self.root_splitter.setOrientation(Qt.Horizontal if target_mode == "horizontal" else Qt.Vertical)
            # Tiles are parentless now; reattach directly
            for t in tiles:
                self.root_splitter.addWidget(t)
            sizes = [max(10, int(w * 1000 / max(1, total))) for w in weights]
            self.root_splitter.setSizes(sizes)
        else:
            # BSP: build balanced tree around the detached tiles
            self.root_splitter.setOrientation(Qt.Horizontal)
            bsp = self._build_bsp_tree(tiles, weights, start_horizontal=True)
            self.root_splitter.addWidget(bsp)

    # ---------------- BSP helpers ----------------
    def _add_tile_bsp(self, new_tile):
        """
        Add a new tile into BSP layout without infinite recursion.
        """
        # Make a local copy instead of calling update_tiles()
        tiles = self.tiles[:] + [new_tile]
        weights, _ = self._current_tile_weights('H')
        weights.append(new_tile.size().width() or 1)

        # Detach everything before rebuilding the tree
        self._clear_root()
        self.root_splitter.setOrientation(Qt.Horizontal)
        bsp = self._build_bsp_tree(tiles, weights, start_horizontal=True)
        self.root_splitter.addWidget(bsp)

        # Refresh tiles list properly after rebuild
        self.update_tiles()


    def _build_bsp_tree(self, tiles, weights, start_horizontal=True):
        """
        Build a balanced BSP tree from *detached* tiles + weights.
        Returns a QSplitter (or a Tile when leaf).
        """
        assert len(tiles) == len(weights)
        if len(tiles) == 1:
            return tiles[0]

        mid = len(tiles) // 2
        left_tiles, right_tiles = tiles[:mid], tiles[mid:]
        left_w, right_w = weights[:mid], weights[mid:]

        left_node = self._build_bsp_tree(left_tiles, left_w, not start_horizontal)
        right_node = self._build_bsp_tree(right_tiles, right_w, not start_horizontal)

        splitter = QSplitter(Qt.Horizontal if start_horizontal else Qt.Vertical)
        splitter.addWidget(left_node)
        splitter.addWidget(right_node)
        splitter.setSizes([max(1, sum(left_w)), max(1, sum(right_w))])
        return splitter

    # ---------------- Swap / Cycle ----------------
    def swap_tile(self, direction: int):
        """
        Cycle active tile focus left/right (safer than reordering widgets).
        direction: +1 for next, -1 for previous.
        """
        if len(self.tiles) < 2:
            return
        old_idx = self.active_tile_index
        self.active_tile_index = (self.active_tile_index + direction) % len(self.tiles)
        self._update_tile_visuals(old_idx, self.active_tile_index)

    # ---------------- Persistence ----------------
    def _serialize_node(self, widget):
        """Turn a widget tree (Tile or QSplitter) into a dict."""
        if isinstance(widget, Tile):
            return {"type": "tile", **widget.to_dict()}
        if isinstance(widget, QSplitter):
            return {
                "type": "splitter",
                "orientation": "H" if widget.orientation() == Qt.Horizontal else "V",
                "children": [self._serialize_node(widget.widget(i)) for i in range(widget.count())]
            }
        return None

    def to_dict(self):
        """Export this workspace state to a dict."""
        return {
            "tiling_mode": self.tiling_mode,
            "active_tile_index": max(0, min(self.active_tile_index, max(0, len(self.tiles) - 1))),
            "tree": self._serialize_node(self.root_splitter)
        }

    def _build_from_node(self, node):
        """Rebuild widget(s) from a serialized node dict."""
        if node["type"] == "tile":
            t = Tile()
            t.load_from_dict(node)
            return t
        if node["type"] == "splitter":
            splitter = QSplitter(Qt.Horizontal if node.get("orientation", "H") == "H" else Qt.Vertical)
            for child in node.get("children", []):
                w = self._build_from_node(child)
                splitter.addWidget(w)
            return splitter
        return Tile(["https://www.google.com"])

    def load_from_dict(self, data):
        """Restore this workspace from a dict."""
        self.tiling_mode = data.get("tiling_mode", "horizontal")
        self.active_tile_index = int(data.get("active_tile_index", 0))

        # Fully clear existing tree (detach tiles to avoid deletion)
        self._clear_root()

        # Build UI tree
        tree = data.get("tree")
        if tree:
            rebuilt = self._build_from_node(tree)
            self.root_splitter.addWidget(rebuilt)

        # Refresh lists
        self.update_tiles()
