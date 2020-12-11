# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Render semantic ui styling for forms."""

from wtforms.widgets import HTMLString


class SelectSUI(object):
    """Renders a select field with Semantic UI styling."""

    def __init__(self, multiple=False):
        """Init."""
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        """Render select field."""
        html = [u'<div class="ui fluid selection dropdown">']
        html.append(u'<input type="hidden" name="{0}">'.format(field.name))
        html.append(u'<i class="dropdown icon"></i>')
        items_html = []
        default_text_html = []
        for val, label, selected in field.iter_choices():
            if selected:
                default_text_html = [
                    u'<div class="text">{0}</div><div class="menu">'
                    .format(label)
                ]
            items_html.append(self.render_option(val, label, selected))
        items_html.append(u"</div></div>")
        html = html + default_text_html + items_html
        return HTMLString("".join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        """Render option."""
        return HTMLString(
            '<div class="item" data-value="{0}">{1}</div>'.format(value, label)
        )
