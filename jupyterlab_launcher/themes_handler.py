"""Tornado handlers for dynamic theme loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from os import path as osp
import os
import re

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from notebook.base.handlers import FileFindHandler


class ThemesHandler(FileFindHandler):
    """A file handler that mangles local urls in CSS files."""

    def initialize(self, path, default_filename=None,
            no_cache_paths=None, themes_url=None):
        FileFindHandler.initialize(self, path,
            default_filename=default_filename, no_cache_paths=no_cache_paths)
        self.themes_url = themes_url

    def get_content(self, abspath, start=None, end=None):
        """Retrieve the content of the requested resource which is located
        at the given absolute path.

        This method should either return a byte string or an iterator
        of byte strings.
        """
        base, ext = osp.splitext(abspath)
        if ext != '.css':
            return FileFindHandler.get_content(abspath, start, end)

        return self._get_css()

    def get_content_size(self):
        """Retrieve the total size of the resource at the given path."""
        base, ext = osp.splitext(self.absolute_path)
        if ext != '.css':
            return FileFindHandler.get_content_size(self)
        else:
            return len(self._get_css())

    def _get_css(self):
        """Get the mangled css file contents."""
        with open(self.absolute_path, 'rb') as fid:
            data = fid.read().decode('utf-8')

        basedir = osp.dirname(self.path).replace(os.sep, '/')
        basepath = osp.join(self.themes_url, basedir)

        # Replace local paths with mangled paths.
        # We only match strings that are local urls,
        # e.g. `url('../foo.css')`, `url('images/foo.png')`
        pattern = (r"url\('(.*)'\)|"
                   r'url\("(.*)"\)')

        def replacer(m):
            """Replace the matched relative url with the mangled url."""
            group = m.group()
            # Get the part that matched
            part = [g for g in m.groups() if g][0]

            # Ignore urls that start with `/` or have a protocol like `http`.
            parsed = urlparse(part)
            if part.startswith('/') or parsed.scheme:
                return group

            mangled = osp.realpath(osp.join(basepath, part))
            return group.replace(part, mangled)

        return re.sub(pattern, replacer, data).encode('utf-8')
