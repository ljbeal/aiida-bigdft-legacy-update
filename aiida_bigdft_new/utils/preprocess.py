def check_ortho(structure, coerce=False):
    """
    Check that a structure is orthorhombic, forcing it to be so if coerce=True
    """
    if structure.cell_angles == [90.0, 90.0, 90.0]:
        return structure
    if not coerce:
        raise ValueError("non orthorhombic cells are not supported")

    ase_lattice = structure.get_ase().get_cell().get_bravais_lattice()

    lattice_variant = ase_lattice.variant

    print(lattice_variant)

    raise NotImplementedError(
        f"cannot transform to " f"orthogonal for {lattice_variant}"
    )
