# -*- coding: utf-8 -*-
"""
    flask_admin_impexp
    ~~~~~~~~~~~~~~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2016 by Saurabh Gupta.
    :license: MIT, see LICENSE for more details.
"""

from werkzeug.utils import secure_filename
import csv
import tablib
import mimetypes

from flask import Response, stream_with_context, jsonify, make_response, json
from flask_admin.babel import gettext
from sqlalchemy.exc import OperationalError, IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import UnmappedInstanceError
from flask_admin.helpers import get_redirect_target
from sqlalchemy.sql.sqltypes import  JSON, ARRAY
import flask_excel as excel

from flask import request, flash, redirect
from flask_admin.base import expose
from flask_admin.contrib import sqla


class AdminImportExport(sqla.ModelView):
    can_export = True
    export_types = ('csv',)

    @expose('/export/<export_type>/')
    def export(self, export_type):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_export or (export_type not in self.export_types):
            flash(gettext('Permission denied.'), 'error')
            return redirect(return_url)

        if export_type == 'csv':
            return self._export_csv(return_url)
        else:
            return self._export_tablib(export_type, return_url)

    def _export_csv(self, return_url):
        count, data = self._export_data()

        class Echo(object):

            def write(self, value):
                return value

        writer = csv.writer(Echo())

        def generate():
            # Append the column titles at the beginning
            titles = [i.name for i in self.model.__table__.columns]
            yield writer.writerow(titles)

            for row in data:
                vals = [getattr(row, c)
                        for c in titles]
                yield writer.writerow(vals)

        filename = self.get_export_name(export_type='csv')

        disposition = 'attachment;filename=%s' % (secure_filename(filename),)

        return Response(
            stream_with_context(generate()),
            headers={'Content-Disposition': disposition},
            mimetype='text/csv'
        )

    def _export_tablib(self, export_type, return_url):
        """
            Exports a variety of formats using the tablib library.
        """
        if tablib is None:
            flash(gettext('Tablib dependency not installed.'), 'error')
            return redirect(return_url)

        filename = self.get_export_name(export_type)

        disposition = 'attachment;filename=%s' % (secure_filename(filename),)

        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '%s; charset=%s' % (mimetype, encoding)

        ds = tablib.Dataset(headers=[c[0] for c in self._export_columns])
        count, data = self._export_data()

        for row in data:
            vals = [self.get_export_value(row, c[0]) for c in self._export_columns]
            ds.append(vals)
        try:
            try:
                response_data = ds.export(format=export_type)
            except AttributeError:
                response_data = getattr(ds, export_type)
        except (AttributeError, tablib.UnsupportedFormat):
            flash(gettext('Export type "%(type)s not supported.',
                          type=export_type), 'error')
            return redirect(return_url)

        return Response(
            response_data,
            headers={'Content-Disposition': disposition},
            mimetype=mimetype,
        )

    def __init__(self, model, session, schema=None, **kwargs):
        self.schema = schema
        super(AdminImportExport, self).__init__(model, session, **kwargs)

    @expose('/import', methods=['POST'])
    def import_excel(self):
        data = request.get_records(field_name='files')
        try:
            self.save_to_database(data)
        except (InvalidRequestError, IntegrityError, OperationalError, UnmappedInstanceError) as e:
            self.session.rollback()
            flash(str(e))
            return make_response(jsonify({'errors': str(e)}), 400)
        else:
            flash('Uploaded Successfully')
            return redirect(self.url)

    list_template = 'list_template.html'

    def save_to_database(self, data):
        bulk_updates = []
        bulk_add = []
        primary_keys = self.get_primary_key()
        json_columns = self.get_json_columns()
        for row in data:
            row = {k: self.convert_type(k, v, json_columns) for k, v in row.items()}
            filters = self.get_primary_filters(primary_keys, row)
            if None not in filters.values():
                if self.get_instance(**filters):
                    bulk_updates.append(row)
                else:
                    bulk_add.append(row)
            else:
                [row.pop(k) for k in filters.keys()]
                bulk_add.append(row)
        try:
            self.session.bulk_update_mappings(self.model, bulk_updates)
            self.session.bulk_insert_mappings(self.model, bulk_add)
            self.session.commit()
        except (UnmappedInstanceError, OperationalError, IntegrityError, InvalidRequestError) as e:
            raise e

    def get_primary_key(self):

        mapper = self.model.__mapper__
        return [
            mapper.get_property_by_column(column)
            for column in mapper.primary_key
            ]

    def get_instance(self, **filters):
        return self.session.query(self.model.query.filter_by(**filters).exists()).scalar()

    @staticmethod
    def get_primary_filters(primary_keys, row):
        return {
            prop.key: row.get(prop.key) if row.get(prop.key) else None
            for prop in primary_keys
        }

    def get_json_columns(self):
        mapper = self.model.__mapper__
        return [key for key, value in mapper.columns.items() if isinstance(value.type, JSON) or
                isinstance(value.type, ARRAY)]

    @staticmethod
    def convert_type(k, v, json_columns):
        if v is not None and v != '':
            if k in json_columns:
                v = json.loads(v)
            return v
        else:
            return None
