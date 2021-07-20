from encoding import u256_to_u8s, u8s_to_u256, compare, SignTable, check_add, AdditionTable
import pytest


@pytest.mark.parametrize("u256,u8s", (
    (1, (1, ) + (0, )*31),
    ((1 << 256) - 1, (255,) * 32),
    (1 << 248, (0, )*31 + (1, )),
))
def test_u256_and_u8s_conversion(u256, u8s):
    assert u256_to_u8s(u256) == u8s
    assert u8s_to_u256(u8s) == u256


def test_table_sizes():
    assert len(SignTable()) == 2**18 - 1
    assert len(AdditionTable()) == 2**17


NASTY_AB_VALUES = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
    (255, 0),
    (0, 255),
    (255, 255),
    (256, 0),
    (0, 256),
    (256, 256),
    (260, 513),
    (65535, 0),
    (0, 65535),
    (65535, 65535),
    (65536, 0),
    (0, 65536),
    (65536, 65536),
    ((1 << 256) - 1, (1 << 256) - 2),
    ((1 << 256) - 2, (1 << 256) - 1)
)


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_comparator(a, b):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    sign_table = SignTable()
    result = [0]*17
    for i in reversed(range(0, 32, 2)):
        a16 = a8s[i] + 256 * a8s[i + 1]
        b16 = b8s[i] + 256 * b8s[i + 1]
        _sum = a16 - b16 + 2**16 * result[i//2+1]
        result[i//2] = (_sum > 0) - (_sum < 0)

    result = result[:16]

    sign = compare(a8s, b8s, result, sign_table)
    if a > b:
        assert sign == 1
    elif a == b:
        assert sign == 0
    else:
        assert sign == -1


@pytest.mark.parametrize("a,b", NASTY_AB_VALUES)
def test_addition(a, b):
    a8s = u256_to_u8s(a)
    b8s = u256_to_u8s(b)
    addition_table = AdditionTable()
    _carry = [0] * 17
    sum8s = [0] * 32
    for i in range(0, 32, 2):
        low = a8s[i] + b8s[i] + _carry[i//2]
        sum8s[i] = low % 256
        high = low // 256 + a8s[i + 1] + b8s[i + 1]
        sum8s[i + 1] = high % 256
        _carry[i//2 + 1] = high // 256

    carry = _carry[1:]

    # Check if the circuit works
    check_add(a8s, b8s, sum8s, carry, addition_table)

    # Check if the witness works
    sum256 = u8s_to_u256(sum8s)
    assert a + b == sum256 + (carry[-1] << 256)
