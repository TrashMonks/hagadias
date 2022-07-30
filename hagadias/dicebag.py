import re


class DiceBag:
    """Loads a dice string and provides methods to roll or analyze that string.

    Parameters:
        dice_string: a dice string, such as '1d4', '3d6+1-2d2', or '17'.
    """

    class Die:
        """Represents a single segment of a larger dice string. Numeric values are converted to dice
        rolls for simplicity - for example, '7' becomes '7d1'.

        Parameters:
            quantity: the number of times to roll the die (i.e. '2' if the die string is '2d6')
            size: the number of sides on the die (i.e. '6' if the die string is '2d6')
        """

        def __init__(self, quantity, size):
            # since the DiceBag might be used in e.g. a Discord bot, do some sanity checks on input
            quantity = int(quantity)
            if abs(quantity) > 5000:
                raise ValueError(f"{abs(quantity)} is too many dice to roll")
            if size < 1:
                raise ValueError(f"{size} is too low for the number of sides on a die")
            if size > 500:
                raise ValueError(f"{size} is too high for the number of sides on a die")
            self.quantity = quantity
            self.size = size

        def __repr__(self) -> str:
            return f"Die({self.quantity}, {self.size})"

        def __str__(self) -> str:
            return f"{self.quantity}d{self.size}"

    # static regex patterns:
    # valid dice string must contain only 0-9, +, -, d, or spaces
    pattern_valid_dice = re.compile(r"[\d\sd+-]+")
    # any dice string segment, generally delimited by + or - (examples: 1d6, +3d2, -4)
    pattern_dice_segment = re.compile(r"[+-]?[^+-]+")
    # a dice string segment that includes 'd' and represents a die roll (examples: 2d3, -1d2)
    pattern_die_roll = re.compile(r"^([+-]?\d+)d(\d+)$")
    # a dice string segment that represents a numeric bonus or malus (examples: +3, -1)
    pattern_die_bonus = re.compile(r"^([+-]?\d+)$")
    # each valid die segment MUST be in [-+]NUM or [-+]NUMdNUM, or throw value error
    pattern_valid_die = re.compile(r"^([-+]?\d+d\d+|[-+]?\d+)$")
    # - and + cannot be clumped together unless cases like 9+-2, else throw value error
    pattern_invalid_op = re.compile(r"\+{2,}|\-[-+]+")

    def __init__(self, dice_string: str):
        if self.pattern_valid_dice.match(dice_string) is None:
            raise ValueError(
                f"Invalid string for DiceBag ({dice_string})"
                " - dice string must contain only 0-9, +, -, d, or spaces"
            )
        self.dice_bag = []
        dice_string = "".join(dice_string.split())  # strip all whitespace from dice_string
        if self.pattern_invalid_op.match(dice_string) is not None:
            raise ValueError(
                f"Invalid string for DiceBag ({dice_string})"
                " - dice string cannot have multiple operators in a row"
            )
        dice_iter = self.pattern_dice_segment.finditer(dice_string)
        for die in dice_iter:
            if self.pattern_valid_die.match(die.group(0)) is None:
                raise ValueError(f"{die.group(0)} must be in format (number) or (number)d(number)")
            m = self.pattern_die_roll.match(die.group(0))
            if m:
                self.dice_bag.append(DiceBag.Die(float(m.group(1)), float(m.group(2))))
            else:
                m = self.pattern_die_bonus.match(die.group(0))
                if m:
                    self.dice_bag.append(DiceBag.Die(float(m.group(1)), 1.0))
                else:
                    raise ValueError(f"DiceBag created with segment of unsupported format: {die}")
        self.dice_string = dice_string

    def average(self) -> float:
        """Return the average value that is rolled from this dice string."""
        val = 0.0
        for die in self.dice_bag:
            val += die.quantity * (1.0 + die.size) / 2.0
        return val

    def minimum(self) -> int:
        """Return the minimum value that can be rolled from this dice string."""
        val = 0.0
        for die in self.dice_bag:
            if die.quantity >= 0:
                val += die.quantity * 1
            else:
                val += die.quantity * die.size
        return int(val)

    def maximum(self) -> int:
        """Return the maximum value that can be rolled from this dice string."""
        val = 0.0
        for die in self.dice_bag:
            if die.quantity >= 0:
                val += die.quantity * die.size
            else:
                val += die.quantity * 1
        return int(val)

    def shake(self) -> int:
        """Simulate and return a random roll for this dice string."""
        from random import randrange

        val = 0
        for die in self.dice_bag:
            q = int(die.quantity)
            s = int(die.size)
            if q > 0:
                for i in range(q):
                    val += randrange(s) + 1
            elif q < 0:
                for i in range(abs(q)):
                    val -= randrange(s) + 1
        return val

    def __repr__(self) -> str:
        return f"DiceBag('{self.dice_string}')"

    def __str__(self) -> str:
        return self.dice_string
