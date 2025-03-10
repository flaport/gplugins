"""Preprocessing involving only the LayerStack."""
from __future__ import annotations

import numpy as np
from gdsfactory.technology import LayerStack


def list_unique_layerstack_z(
    layerstack: LayerStack,
) -> list[float]:
    """List all unique LayerStack z coordinates.

    Args:
        layerstack: LayerStack
    Returns:
        Sorted set of z-coordinates for this layerstack
    """
    thicknesses = [layer.thickness for layer in layerstack.layers.values()]
    zmins = [layer.zmin for layer in layerstack.layers.values()]
    zmaxs = [sum(value) for value in zip(zmins, thicknesses)]

    return sorted(set(zmins + zmaxs))


def map_unique_layerstack_z(
    layerstack: LayerStack,
    include_zmax: bool = True,
):
    """Map unique LayerStack z coordinates to various layers.

    Args:
        layerstack: LayerStack
        include_zmax: if True, will map a layername to its zmax coordinate, otherwise not
    Returns:
        Dict with layernames as keys and set of unique z-values where the layer is present
    """
    z_levels = list_unique_layerstack_z(layerstack)
    layer_dict = layerstack.to_dict()
    unique_z_dict = {}
    for layername, layer in layer_dict.items():
        zmin = layer["zmin"]
        zmax = layer["zmin"] + layer["thickness"]
        z_start, z_end = sorted([zmin, zmax])
        if include_zmax:
            unique_z_dict[layername] = {
                z for z in z_levels if (z >= z_start and z <= z_end)
            }
        else:
            unique_z_dict[layername] = {
                z for z in z_levels if (z >= z_start and z < z_end)
            }

    return unique_z_dict


def get_layer_overlaps_z(
    layerstack: LayerStack,
    include_zmax: bool = True,
):
    """Maps layers to unique LayerStack z coordinates.

    Args:
        layerstack: LayerStack
    Returns:
        Dict with unique z-positions as keys, and list of layernames as entries
    """
    z_grid = list_unique_layerstack_z(layerstack)
    unique_z_dict = map_unique_layerstack_z(layerstack, include_zmax)
    intersection_z_dict = {}
    for z in z_grid:
        current_layers = {
            layername for layername, layer_zs in unique_z_dict.items() if z in layer_zs
        }
        intersection_z_dict[z] = current_layers

    return intersection_z_dict


def get_layers_at_z(layerstack: LayerStack, z: float):
    """Returns layers present at a given z-position.

    Args:
        layerstack: LayerStack
    Returns:
        List of layers
    """
    intersection_z_dict = get_layer_overlaps_z(layerstack)
    all_zs = list_unique_layerstack_z(layerstack)
    if z < np.min(all_zs):
        raise ValueError("Requested z-value is below the minimum layerstack z")
    elif z > np.max(all_zs):
        raise ValueError("Requested z-value is above the minimum layerstack z")
    for z_unique in intersection_z_dict.keys():
        if z <= z_unique:
            return intersection_z_dict[z_unique]
    raise AssertionError("Could not find z-value in layerstack z-range.")


def order_layerstack(layerstack: LayerStack):
    """Orders layerstack according to mesh_order.

    Args:
        layerstack: LayerStack.

    Returns:
        List of layernames: layerlevels dicts sorted by their mesh_order.
    """
    layers = layerstack.to_dict()
    mesh_orders = [value["mesh_order"] for value in layers.values()]
    return [x for _, x in sorted(zip(mesh_orders, layers))]


if __name__ == "__main__":
    import gdsfactory as gf

    waveguide = gf.components.straight_pin(length=1, taper=None)
    waveguide.show()

    from gdsfactory.pdk import get_layer_stack

    filtered_layerstack = LayerStack(
        layers={
            k: get_layer_stack().layers[k] for k in ("core", "via_contact", "slab90")
        }
    )

    ret = order_layerstack(
        filtered_layerstack,
    )
    print(ret)
