def check_orthorhombic(structure, coerce=False):
    """
    Check that a structure is orthorhombic, forcing it to be so if coerce=True
    """
    if structure.cell_angles == [90.0, 90.0, 90.0]:
        return structure
    elif not coerce:
        raise ValueError('non orthorhombic cells are not supported')

    struct_id = Identifier(*structure.cell_lengths,
                           *structure.cell_angles)

    print(struct_id.identity, struct_id)

    raise NotImplementedError(f'cannot transform to orthogonal for {struct_id}')


class Identifier:
    """
    Class        Lengths            Angles
    Cubic        (a = b = c)	 	(a = b = g = 90)
    Tetragonal   (a = b != c)	 	(a = b = g = 90)
    Monoclinic   (a != b != c)	    (a = b = 90 != g        !
    Orthorhombic (a != b != c)	    (a = b = g = 90)
    Rhombohedral (a = b = c)	 	(a = b = g != 90)       !
    Hexagonal    (a = b != c)	 	(a = b = 90, g = 120)   !
    Triclinic    (a != b != c)      (a != b != g != 90)     !
    """

    def __init__(self,
                 a, b, c,
                 alpha, beta, gamma):
        self._len = self._clean([a, b, c])
        self._ang = self._clean([alpha, beta, gamma])

        self._identity = None

    def __repr__(self):
        return f'{self.identity} cell with lengths: {self.lengths}, ' \
               f'angles: {self.angles}'

    @staticmethod
    def _clean(vals):
        return [round(val, 2) for val in vals]

    @property
    def identity(self):
        """
        Attempt to determine the unit cell classification using the rules
        listed in the class.

        Cache value in self._identity so we don't have to go through this
        monstrous if/else chain again.

        There has to be a better way of doing this... - LB
        """
        if self._identity is not None:
            return self._identity

        lens = sorted(self.lengths)
        angs = sorted(self.angles)

        identity = 'Unclassified'

        if lens[0] == lens[1] == lens[2] and \
                angs[0] == angs[1] == angs[2] == 90:
            identity = 'Cubic'

        elif lens[0] == lens[1] != lens[2] and \
                angs[0] == angs[1] == angs[2] == 90:
            identity = 'Tetragonal'

        elif lens[0] != lens[1] == lens[2] and \
                angs[0] == angs[1] == angs[2] == 90:
            identity = 'Tetragonal'

        elif lens[0] != lens[1] != lens[2] and \
                angs[0] == angs[1] == angs[2] and \
                sum(angs) != 270:
            identity = 'Monoclinic'

        elif lens[0] != lens[1] != lens[2] and \
                angs[0] == angs[1] == angs[2] == 90:
            identity = 'Orthorhombic'

        elif lens[0] == lens[1] == lens[2] and \
                angs[0] == angs[1] == angs[2] and \
                sum(angs) != 270:
            identity = 'Rhombohedral'

        elif lens[0] == lens[1] != lens[2] and \
                angs[0] == angs[1] == 90 and \
                angs[2] == 120:
            identity = 'Hexagonal'

        elif lens[0] != lens[1] == lens[2] and \
                angs[0] == angs[1] == 90 and \
                angs[2] == 120:
            identity = 'Hexagonal'

        elif lens[0] == lens[1] != lens[2] and \
                angs[2] == angs[1] == 90 and \
                angs[0] == 120:
            identity = 'Hexagonal'

        elif lens[0] != lens[1] == lens[2] and \
                angs[2] == angs[1] == 90 and \
                angs[0] == 120:
            identity = 'Hexagonal'

        elif lens[0] != lens[1] != lens[2] and \
                angs[0] != angs[1] != angs[2] and \
                sum(angs) != 270:
            identity = 'Triclinic'

        self._identity = identity

        return identity

    @property
    def lengths(self):
        return self._len

    @property
    def angles(self):
        return self._ang
