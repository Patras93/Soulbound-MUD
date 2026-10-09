"""Large-integer combat helpers.

Damage remains an unbounded Python integer. Multipliers are finite decimal
coefficients; normal gameplay is unchanged while int-to-float overflow is
avoided for extraordinarily large builds.
"""
from decimal import Decimal, ROUND_HALF_EVEN, localcontext


def decimal_value(value):
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    else:
        result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Non-finite combat coefficient")
    return result


def rounded_product(*values):
    if not values:
        return 0
    factors = [decimal_value(value) for value in values]
    if any(value < 0 for value in factors):
        raise ValueError("Negative combat value")
    # Dynamic context handles integer portions above the native float range.
    precision = max(60, sum(max(1, len(x.as_tuple().digits)) for x in factors) + 25)
    with localcontext() as ctx:
        ctx.prec = precision
        result = Decimal(1)
        for factor in factors:
            result *= factor
        return int(result.to_integral_value(rounding=ROUND_HALF_EVEN))


def safe_success_ratio(actual, possible):
    """Return [0, 2] for a successful attack without float(big_int)."""
    actual = max(0, int(actual))
    possible = max(1, int(possible))
    if actual >= 2 * possible:
        return 2.0
    with localcontext() as ctx:
        ctx.prec = 32
        return float(Decimal(actual) / Decimal(possible))
