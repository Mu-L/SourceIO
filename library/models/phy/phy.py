from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from SourceIO.library.utils.tiny_path import TinyPath
from SourceIO.library.shared.types import Vector3, Vector4
from SourceIO.library.utils import Buffer, FileBuffer


@dataclass(slots=True)
class Header:
    size: int
    id: int
    solid_count: int
    checksum: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        size = buffer.read_uint32()
        ident = buffer.read_uint32()
        solid_count = buffer.read_uint32()
        checksum = buffer.read_uint32()
        return cls(size, ident, solid_count, checksum)


@dataclass(slots=True)
class ConvexTriangle:
    pad: int
    edges: tuple[int, ...]

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        pad, *edges = buffer.read_fmt('i6h')
        return cls(pad, edges)

    def get_vertex_id(self, index):
        return self.edges[index * 2]

    @property
    def vertex_ids(self):
        return self.edges[::2]


@dataclass(slots=True)
class ConvexLeaf:
    is_root: bool
    _entry: int = 0
    vertex_offset: int = 0
    bone_id: int = 0
    flags: int = 0
    triangle_count: int = 0
    unused: int = 0
    triangles: list = field(default_factory=list)
    unique_vertices: set = field(default_factory=set)

    @classmethod
    def from_buffer(cls, buffer: Buffer, is_root: bool):
        entry = buffer.tell()
        vertex_offset, bone_id, flags, triangle_count, unused = buffer.read_fmt(
            '3i2h')
        triangles = []
        unique_vertices = set()
        for _ in range(triangle_count):
            tri = ConvexTriangle.from_buffer(buffer)
            triangles.append(tri.vertex_ids)
            unique_vertices.update(tri.vertex_ids)
        return cls(is_root, entry, vertex_offset, bone_id, flags, triangle_count, unused, triangles, unique_vertices)

    def child_node(self, buffer: Buffer):
        if self.has_children:
            with buffer.save_current_offset():
                buffer.seek(self._entry + self.bone_id)
                child = TreeNode.from_buffer(buffer)
            return child

    @property
    def has_children(self):
        return (self.flags >> 0) & 3

    @property
    def is_compact(self):
        return (self.flags >> 2) & 3

    @property
    def dummy(self):
        return (self.flags >> 4) & 15

    @property
    def size_div_16(self):
        return (self.flags >> 8) & 0xFF_FF_FF_FF

    @property
    def vertex_data_offset(self):
        return self._entry + self.vertex_offset


@dataclass(slots=True)
class TreeNode:
    center: Vector3[float]
    radius: float
    bbox_size: Vector4[int]
    left_node: Optional['TreeNode'] = field(default=None)
    right_node: Optional['TreeNode'] = field(default=None)
    convex_leaf: ConvexLeaf | None = field(default=None)

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        entry_offset = buffer.tell()
        right_node_offset, convex_offset, *center, radius = buffer.read_fmt('2i4f')
        bbox_size = buffer.read_fmt('4B')
        is_leaf = right_node_offset == 0
        convex_leaf: ConvexLeaf | None = None
        with buffer.save_current_offset():
            if convex_offset:
                with buffer.save_current_offset():
                    buffer.seek(entry_offset + convex_offset)
                    convex_leaf = ConvexLeaf.from_buffer(buffer, not is_leaf)
                if is_leaf:
                    return cls(center, radius, bbox_size, None, None, convex_leaf)
            left_node = TreeNode.from_buffer(buffer)
            with buffer.save_current_offset():
                buffer.seek(entry_offset + right_node_offset)
                right_node = TreeNode.from_buffer(buffer)
        return cls(center, radius, bbox_size, left_node, right_node, convex_leaf)


@dataclass(slots=True)
class CollisionModel:
    values: tuple[float, ...]
    surface: int
    offset_tree: int
    root_tree: TreeNode

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        entry_offset = buffer.tell()
        values = buffer.read_fmt('7f')
        surface, offset_tree, *_ = buffer.read_fmt('4I')
        ivps_magic = buffer.read_fourcc()
        assert ivps_magic == 'IVPS'
        with buffer.save_current_offset():
            buffer.seek(entry_offset + offset_tree)
            root_tree = TreeNode.from_buffer(buffer)
        return cls(values, surface, offset_tree, root_tree)

    @staticmethod
    def get_vertex_data(buffer: Buffer, convex_leaf: ConvexLeaf, vertex_count):
        with buffer.save_current_offset():
            buffer.seek(convex_leaf.vertex_data_offset)
            vertex_data = np.frombuffer(buffer.read(4 * 4 * vertex_count), np.float32).copy()
            vertex_data = vertex_data.reshape((-1, 4))[:, :3]

            y = vertex_data[:, 1].copy()
            z = vertex_data[:, 2].copy()
            vertex_data[:, 1] = z
            vertex_data[:, 2] = y

        return vertex_data


@dataclass(slots=True)
class SolidHeader:
    solid_size: int
    version: int
    type: int
    size: int
    areas: Vector3[float]
    axis_map_size: int
    collision_model: CollisionModel

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        solid_size = buffer.read_uint32()
        ident = buffer.read_fourcc()
        assert ident == 'VPHY'
        version = buffer.read_uint16()
        type = buffer.read_uint16()
        size = buffer.read_uint32()
        areas = buffer.read_fmt('3f')
        axis_map_size = buffer.read_uint32()
        collision_model = CollisionModel.from_buffer(buffer)
        return cls(solid_size, version, type, size, areas, axis_map_size, collision_model)

    def end(self):
        return self.solid_size + 4


@dataclass(slots=True)
class Phy:
    header: Header
    solids: list[SolidHeader]
    kv: str

    @classmethod
    def from_filepath(cls, filepath: TinyPath):
        return cls.from_buffer(FileBuffer(filepath))

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        header = Header.from_buffer(buffer)
        buffer.seek(header.size)
        solids = []
        solid_start = buffer.tell()
        for _ in range(header.solid_count):
            solid = SolidHeader.from_buffer(buffer)
            buffer.seek(solid_start + solid.end())
            solid_start = buffer.tell()
            solids.append(solid)
        # if solids:
        #     buffer.seek(solid_start + solids[-1].end())
        kv = buffer.read_ascii_string()
        return cls(header, solids, kv)
