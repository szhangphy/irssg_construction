import numpy as np
from numpy.linalg import norm
from pymatgen.io.cif import CifParser
from collections import OrderedDict


def _parse_float_tokens(tokens):
    values = []
    for token in tokens:
        token = token.replace("D", "E").replace("d", "e")
        try:
            values.append(float(token))
        except ValueError:
            pass
    return values


def _parse_int_tokens(tokens):
    values = []
    for token in tokens:
        try:
            values.append(int(token))
        except ValueError:
            return None
    return values


def _scale_lattice(lattice, scale_values):
    if len(scale_values) == 1:
        scale = scale_values[0]
        if scale > 0:
            return lattice * scale, scale
        if scale < 0:
            volume = abs(np.linalg.det(lattice))
            if volume <= 0:
                raise ValueError("Invalid POSCAR lattice volume")
            factor = (abs(scale) / volume) ** (1.0 / 3.0)
            return lattice * factor, factor
        raise ValueError("Invalid POSCAR scale factor 0")

    if len(scale_values) == 3:
        scale = np.array(scale_values, dtype=float)
        if np.any(scale <= 0):
            raise ValueError("Three POSCAR scale factors must be positive")
        return lattice * scale.reshape(3, 1), scale

    raise ValueError("POSCAR scale line must contain one or three numbers")


def _read_poscar_common(file_name="POSCAR"):
    with open(file_name, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) < 8:
        raise ValueError("Invalid POSCAR input: too few lines")

    scale_values = _parse_float_tokens(lines[1].split())
    lattice = np.array(
        [[float(c) for c in lines[i].split()[:3]] for i in range(2, 5)],
        dtype=float,
    )
    lattice, cart_scale = _scale_lattice(lattice, scale_values)

    idx = 5
    maybe_counts = _parse_int_tokens(lines[idx].split())
    if maybe_counts is None:
        elements = lines[idx].split()
        idx += 1
        counts = _parse_int_tokens(lines[idx].split())
        if counts is None:
            raise ValueError("Invalid POSCAR atom-count line")
    else:
        counts = maybe_counts
        elements = [f"X{i + 1}" for i in range(len(counts))]

    idx += 1
    if idx < len(lines) and lines[idx].lower().startswith("s"):
        idx += 1

    if idx >= len(lines):
        raise ValueError("Invalid POSCAR input: missing coordinate mode")

    mode = lines[idx].lower()
    if mode.startswith("d"):
        coord_mode = "direct"
    elif mode.startswith("c") or mode.startswith("k"):
        coord_mode = "cartesian"
    else:
        raise ValueError(f"Unknown POSCAR coordinate mode: {lines[idx]}")
    idx += 1

    numbers = []
    for itype, count in enumerate(counts):
        numbers.extend([itype + 1] * count)

    num_of_points = sum(counts)
    if len(lines) < idx + num_of_points:
        raise ValueError("Invalid POSCAR input: not enough atomic coordinate lines")

    positions = np.zeros((num_of_points, 3))
    mag = []
    inv_lattice = np.linalg.inv(lattice)

    for atom_idx in range(num_of_points):
        line_no = idx + atom_idx + 1
        values = _parse_float_tokens(lines[idx + atom_idx].split())
        if len(values) < 3:
            raise ValueError(f"Invalid input format at line {line_no}")

        coord = np.array(values[:3], dtype=float)
        if coord_mode == "cartesian":
            coord = coord * cart_scale
            coord = coord @ inv_lattice
        positions[atom_idx, :] = coord

        if len(values) >= 6:
            mag.append(values[-3:])
        else:
            mag.append([0, 0, 0])

    return lattice, positions, numbers, elements, np.array(mag)


# ************************ function read_poscar ****************************
# 
# > Input POSCAR, can with MAGMOM   x  y  z  mz  my  mz
# > (lattice, positions, numbers, mag) 
# > (lattice, positions, numbers, mag) = read_poscar() 
# 
# ***********************************************************************
def read_poscar(file_name = 'POSCAR'): 
    lattice, positions, numbers, elements, mag = _read_poscar_common(file_name)
    return (lattice, positions, numbers, elements, mag)


def read_poscar_no_elements(file_name='POSCAR'):
    """
    Read POSCAR file to extract crystal structure and magnetic moments.
    
    Args:
        file_name: Path to POSCAR file (default: 'POSCAR')
        
    Returns:
        tuple: (cell, elements)
            - cell: Tuple of (lattice, positions, numbers, magmoms)
            - elements: List of element symbols
    """
    lattice, positions, numbers, elements, mag = _read_poscar_common(file_name)
    cell = (lattice, positions, numbers, mag)
    return cell, elements


# ************************ function write_poscar ****************************
# 
# > input cell = (lattice, positions, numbers, mag) 
# > write a POSCAR file using the cell 
# 
# ***********************************************************************
def write_poscar(cell, file_name='POSCAR.pos2ssg'):

    lattice, positions, numbers,element, mag = cell
    
    positions = np.array(positions)
    mag = np.array(mag)

    # get numbers of the cell
    unique_numbers = []
    for n in numbers:
        if np.int32(n) not in unique_numbers:
            unique_numbers.append(np.int32(n))
    
    numbers = [[np.int32(nums)] for nums in numbers]

    # numbers of elements
    element_counts = [numbers.count(t) for t in unique_numbers]
    # write POSCAR
    with open(file_name, 'w') as f:
        f.write("Generated by write_poscar\n")
        f.write("1.0\n")
        for vec in lattice:
            f.write("  {:.16f}  {:>.16f}  {:>.16f}\n".format(*vec))
        f.write("  " + "  ".join(t for t in element) + "\n")
        f.write("  " + "  ".join(str(c) for c in element_counts) + "\n")
        f.write("Direc\n")

        for i in range(len(positions)):
            pos_str = "  {: .16f}  {: .16f}  {: .16f}".format(*positions[i])
            if mag is not None and len(mag) > 0:
                mag_str = "  {: .6f}  {: .6f}  {: .6f}".format(*mag[i])
                if norm(mag[i]) > 1e-5:
                    f.write(pos_str + mag_str + "\n")
                else:
                    f.write(pos_str + "\n")
            else:
                f.write(pos_str + "\n")


def mcif2cell(file_name):
    cc = CifParser(file_name)
    structure = cc.get_structures(primitive=False)[0]
    atom_types = [site.species_string for site in structure]
    atom_map = list(OrderedDict.fromkeys(atom_types))
    element_map = {element: i+1 for i, element in enumerate(atom_map)}
    numbers = [element_map[site.species_string] for site in structure]
    elements = list(structure.symbol_set)

    lattice = structure.lattice.matrix
    position = structure.frac_coords
    m = structure.site_properties['magmom']
    mag = []
    for i in m:
        mag.append(i.moment)
    
    # Get unique element symbols (no duplicates)
    element_symbols = list(OrderedDict.fromkeys([site.species_string for site in structure]))
    
    cell = (lattice, position, numbers, mag)
    return cell, element_symbols
