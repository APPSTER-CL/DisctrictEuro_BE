import decimal

from rest_framework import fields

from core import models


class CustomDecimalField(fields.DecimalField):
    def __init__(self, *args, **kwargs):
        max_digits = self.Meta.max_digits
        decimal_places = self.Meta.decimal_places
        if len(args) > 0:
            max_digits = args[0]
        if len(args) > 1:
            decimal_places = args[1]
        kwargs['max_digits'] = kwargs.get('max_digits', max_digits)
        kwargs['decimal_places'] = kwargs.get('decimal_places', decimal_places)
        super(CustomDecimalField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        """
        Validate that the input is a decimal number and return a Decimal
        instance.
        """
        if self.decimal_places:
            truncate = decimal.Decimal(10) ** - self.decimal_places
        else:
            truncate = decimal.Decimal(1)

        try:
            value = decimal.Decimal(data).quantize(truncate)
        except decimal.DecimalException:
            self.fail('invalid')

        # Check for NaN. It is the only value that isn't equal to itself,
        # so we can use this to identify NaN values.
        if value != value:
            self.fail('invalid')

        # Check for infinity and negative infinity.
        if value in (decimal.Decimal('Inf'), decimal.Decimal('-Inf')):
            self.fail('invalid')

        return self.validate_precision(value)

    class Meta:
        max_digits = None
        decimal_places = None


class MoneyField(CustomDecimalField):
    class Meta:
        max_digits = models._max_digits
        decimal_places = models._decimal_places