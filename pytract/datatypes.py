# subscriptable classes
import typing

@typing._LiteralSpecialForm
def int128(self, *parameters):
    parameters = typing._flatten_literal_params(parameters)

    try:
        parameters = tuple(
            p
            for p, _ in typing._deduplicate(
                list(typing._value_and_type_iter(parameters))
            )
        )
    except TypeError:  # unhashable parameters
        pass

    for p in parameters:
        assert type(p) == int
    return typing._LiteralGenericAlias(self, parameters)


@typing._LiteralSpecialForm
def bytes32(self, *parameters):
    parameters = typing._flatten_literal_params(parameters)

    try:
        parameters = tuple(
            p
            for p, _ in typing._deduplicate(
                list(typing._value_and_type_iter(parameters))
            )
        )
    except TypeError:  # unhashable parameters
        pass

    for p in parameters:
        assert type(p) == int
    return typing._LiteralGenericAlias(self, parameters)


@typing._LiteralSpecialForm
def Bytes(self, *parameters):
    parameters = typing._flatten_literal_params(parameters)

    try:
        parameters = tuple(
            p
            for p, _ in typing._deduplicate(
                list(typing._value_and_type_iter(parameters))
            )
        )
    except TypeError:  # unhashable parameters
        pass

    for p in parameters:
        assert type(p) == int
    return typing._LiteralGenericAlias(self, parameters)



@typing._LiteralSpecialForm
def String(self, *parameters):
    parameters = typing._flatten_literal_params(parameters)

    try:
        parameters = tuple(
            p
            for p, _ in typing._deduplicate(
                list(typing._value_and_type_iter(parameters))
            )
        )
    except TypeError:  # unhashable parameters
        pass

    for p in parameters:
        assert type(p) == int
    return typing._LiteralGenericAlias(self, parameters)

HashMap = typing.Dict