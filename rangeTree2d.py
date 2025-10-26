import bisect
from random import shuffle
from typing import List, Optional, Tuple

class Point:
    def __init__(self, coords: List[int]) -> None:
        self.coords: List[int] = coords
        self.dims: int = len(coords)
    
    def __getitem__(self, index: int) -> int:
        return self.coords[index]
    
    def __repr__(self) -> str:
        return f"Point(coords={self.coords})"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Point):
            return False
        return self.coords == value.coords
    
    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Point):
            return NotImplemented
        return self.coords[::-1] < value.coords[::-1]

class RangeTreeNode:
    def __init__(self, points: List[Point], split: int, axis: int, left=None, right=None):
        self.points: List[Point] = sorted(points) # All points in the subtree of this node
        self.split: int = split  # Max coordinate in left subtree for axis
        self.axis = axis    # Axis of division
        self.left: Optional[RangeTreeNode] = left
        self.right: Optional[RangeTreeNode] = right
        self.next_axis_subtree: Optional[RangeTree] = None  # Secondary tree for next axis

    def __repr__(self) -> str:
        return f"RangeTreeNode(axis={self.axis}, max={self.split}, points={self.points}, left={self.left}, right={self.right})"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RangeTreeNode):
            return False
        return self.axis == value.axis and self.split == value.split and self.points == value.points

class RangeTree:
    def __init__(self, points: List[Point], axis: int = 0):
        self.axis: int = axis
        self.root = self._build(points)

    def _build(self, points: List[Point]) -> Optional[RangeTreeNode]:
        return self._build_on_axis(RangeTreeNode(points, 0, self.axis))
    
    def _build_on_axis(self, root: RangeTreeNode) -> Optional[RangeTreeNode]:
        root.points = sorted(root.points, key=lambda p: p[self.axis])
        # Instead we assume that root points are already sorted on all axis from left to right in axis order
        points = root.points
        if not points: return None
        if len(points) == 1:
            result = RangeTreeNode(points, points[0][self.axis], self.axis)
            result.next_axis_subtree = RangeTree(points, self.axis + 1) if self.axis + 1 < points[0].dims else None
            return result
        
        mid_idx = len(points) // 2
        mid = points[mid_idx][self.axis]
        root.split = mid
        root.left = self._build_on_axis(RangeTreeNode(points[:mid_idx], mid, self.axis))
        root.right = self._build_on_axis(RangeTreeNode(points[mid_idx:], mid, self.axis))

        if self.axis + 1 < points[0].dims:
            root.next_axis_subtree = RangeTree(points, self.axis + 1)
        return root
    
    def get_search_path(self, split: int, min: bool) -> List[Tuple[RangeTreeNode, str]]:
        """
        Get the path from root to the leaf node for a given split value.
        Args:
            split: The coordinate value to search for.
            min: If True, find the minimum path (for lower bound), else maximum path (for upper bound).
        Returns:
            List of tuples (RangeTreeNode, direction) representing the path."""
        path = []
        node = self.root
        while node:            
            if split < node.split or (min and split == node.split):
                path.append((node, 'L'))
                node = node.left
            elif split > node.split or (not min and split == node.split):
                path.append((node, 'R'))
                node = node.right
        return path

    def range_query(self, lower: List[int], upper: List[int]) -> List[Point]:
        results = self._range_query(lower, upper, 0)
        pts = []
        for r in results:
            pts.extend([pt for pt in r.points if all(lower[d] <= pt[d] <= upper[d] for d in range(pt.dims))])   # we have to do this because leaf nodes may contain points outside range
        return sorted(pts)


    def _range_query(self, lower: List[int], upper: List[int], axis: int) -> List[RangeTreeNode]:
        if self.root is None:
            return []
        lower_path = self.get_search_path(lower[axis], min=True)
        upper_path = self.get_search_path(upper[axis], min=False)

        # LCA
        split_node = None
        split_node_idx = -1
        for (u_node, _), (l_node, _) in zip(upper_path, lower_path):
            if u_node == l_node:
                split_node = u_node
                split_node_idx += 1
            else:
                break
        if split_node is None:
            raise ValueError("No LCA for nodes")
        
        # Slice paths after split node to just get the path between the two nodes
        lower_path = lower_path[:split_node_idx:-1]
        upper_path = upper_path[split_node_idx+1:]

        nodes: List[RangeTreeNode] = [self.root] if not self.root.left and not self.root.right else []  # because previous part removes the LCA from paths, and root is trivially LCA if it's a leaf
        for node, dir in lower_path:
            if dir == 'L':
                if node.right:
                    nodes.append(node.right)
            if node.right is None and node.left is None:
                nodes.append(node) # include leaf node that may contain points in range
            
        for node, dir in upper_path:
            if dir == 'R':
                if node.left:
                    nodes.append(node.left)
            if node.right is None and node.left is None:
                nodes.append(node) # include leaf node that may contain points in range
            
        
        result = []
        for n in nodes:
            # print(n.next_axis_subtree.root if n.next_axis_subtree else None)
            result.extend(n.next_axis_subtree._range_query(lower, upper, axis + 1) if n.next_axis_subtree else [n])
        
        return result


def generate_sample_data(start: tuple[int, ...], end: tuple[int, ...]) -> List[Point]:
    """Generate all points within the given range."""
    from itertools import product
    coords = [range(start[i], end[i] + 1) for i in range(len(start))]
    points = [Point(list(c)) for c in product(*coords)]
    return points

if __name__ == "__main__":
    boxes: List[Point] = generate_sample_data((1, 1), (100, 100))
    print("Generated Boxes")

    tree = RangeTree(boxes)
    print("Built Tree")
    results = tree._range_query([2, 2], [4, 5], 0)
    boxes = []
    for r in results:
        for pt in r.points:
            print(pt)