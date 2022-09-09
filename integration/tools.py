# See LICENSE file for full copyright and licensing details.

import base64
from itertools import groupby
from operator import attrgetter
from collections import namedtuple, defaultdict, OrderedDict

from cerberus import Validator

from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError
from odoo import _


IS_TRUE = '1'
IS_FALSE = '0'


def _guess_mimetype(data):
    if not data:
        return None

    raw = base64.b64decode(data)
    mimetype = guess_mimetype(raw)
    return mimetype


def not_implemented(method):
    def wrapper(self, *args, **kw):
        raise ValidationError(_(
            '[Debug] This feature is still not implemented (%s.%s()).'
            % (self.__class__.__name__, method.__name__)
        ))
    return wrapper


class TemplateHub:
    """Validate products before import."""

    _schema = OrderedDict({
        'id': {'type': 'string', 'required': True},
        'barcode': {'type': 'string', 'required': True},
        'ref': {'type': 'string', 'required': True},
        'parent_id': {'type': 'string', 'required': True},
        'skip_ref': {'type': 'boolean', 'required': True},
    })

    def __init__(self, input_list):
        assert type(input_list) == list
        # Because it works very slow with big pack of data
        # self._validate_input(input_list)

        self.ptuple = namedtuple('Product', self._schema.keys())
        self.product_list = self._convert_to_clean(input_list)

    def __iter__(self):
        for rec in self.product_list:
            yield rec

    def get_empty_ref_ids(self):
        """
        :result: ([1, 2, 3], [4, 5, 6])
        """
        templates, variants = self._split_products(
            [x for x in self if not x.ref and not x.skip_ref]
        )
        return [self._format_rec(t) for t in templates], [self._format_rec(v) for v in variants]

    def get_dupl_refs(self):
        """
        :result: {'BAR': [1, 2], 'FOO': [1, 2, 3]}
        """
        products = [x for x in self if x.ref and not x.skip_ref]
        return self._group_by(products, 'ref', level=2)

    def get_dupl_barcodes(self):
        """
        :result: {'XX01': [1, 2], 'XX02': [1, 2, 3]}
        """
        products = [x for x in self if x.barcode]
        return self._group_by(products, 'barcode', level=2)

    @classmethod
    def from_odoo(cls, search_list):
        """Make class instance from odoo search."""
        def parse_args(rec):
            return {
                'id': str(rec['id']),
                'barcode': rec['barcode'] or str(),
                'ref': rec['default_code'] or str(),
                'parent_id': str(rec['product_tmpl_id'][0]),
                'skip_ref': False,
            }
        return cls([parse_args(rec) for rec in search_list])

    @classmethod
    def get_ref_intersection(cls, self_a, self_b):
        """Find references intersection of different instances."""
        def parse_ref(self_):
            return {x.ref for x in self_ if x.ref and not x.skip_ref}

        def filter_records(scope):
            return [x for x in self_a if x.ref in scope], [x for x in self_b if x.ref in scope]

        joint_ref = parse_ref(self_a) & parse_ref(self_b)
        records_a, records_b = filter_records(joint_ref)

        return self_a._group_by(records_a, 'ref'), self_b._group_by(records_b, 'ref')

    def _validate_input(self, input_list):
        frame = Validator(self._schema)
        for record in input_list:
            if not frame.validate(record):
                raise ValidationError(_(
                    'Invalid product serialization: %s' % str(record)
                ))

    def _convert_to_clean(self, input_list):
        """Convert to namedtuple for convenient handling."""
        return [self._serialize_by_scheme(rec) for rec in input_list]

    def _serialize_by_scheme(self, record):
        args_list = [record[key] for key in self._schema.keys()]
        return self.ptuple(*args_list)

    @staticmethod
    def _format_rec(rec):
        return f'{rec.parent_id} - {rec.id}' if rec.parent_id else rec.id

    @staticmethod
    def _split_products(records):
        templates = [x for x in records if not x.parent_id]
        variants = [x for x in records if x.parent_id]
        return templates, variants

    def _group_by(self, records, attr, level=False):
        dict_ = defaultdict(list)
        [
            [dict_[key].append(self._format_rec(x)) for x in grouper]
            for key, grouper in groupby(records, key=attrgetter(attr))
        ]
        if level:
            return {
                key: val for key, val in dict_.items() if len(val) >= level
            }
        return dict(dict_)
