def check_orthorhombic(structure, coerce=False):
    """
    Check that a structure is orthorhombic, forcing it to be so if coerce=True
    """
    if structure.cell_angles == [90.0, 90.0, 90.0]:
        return structure
    elif not coerce:
        raise ValueError('non orthorhombic cells are not supported')

    raise NotImplementedError
