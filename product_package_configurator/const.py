from enum import Enum


class StrEnum(str, Enum):
    pass


class DecimalPrecision(StrEnum):
    SIZE = 'Package Configurator Size'
    PRICE = 'Package Configurator Price'
    COST = 'Package Configurator Cost'


class SetupType(StrEnum):
    SHEET = 'sheet'


class SheetTypeScope(StrEnum):
    GREYBOARD = 'greyboard'
    WRAPPINGPAPER = 'wrappingpaper'


class CirculationSetupPart(StrEnum):
    BASE_GREYBOARD = 'base_greyboard'
    LID_GREYBOARD = 'lid_greyboard'
    BASE_INSIDE_WRAPPING = 'base_inside_wrapping'
    BASE_OUTSIDE_WRAPPING = 'base_outside_wrapping'
    LID_INSIDE_WRAPPING = 'lid_inside_wrapping'
    LID_OUTSIDE_WRAPPING = 'lid_outside_wrapping'


DEFAUL_GLOBAL_BOX_EXTRA = 30  # mm
# Extra size for length and width to compensate, so lid would fit on a
# base!
DEFAULT_LID_EXTRA = 2  # mm
DEFAULT_OUTSIDE_WRAPPING_EXTRA = 20  # mm
MM_TO_SQ_M_COEFFICIENT = 1000000
