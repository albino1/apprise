# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function
from os import chmod
from os import getuid
from os.path import dirname
from apprise import Apprise
from apprise import AppriseAsset
from apprise.utils import compat_is_basestring
from apprise.Apprise import SCHEMA_MAP
from apprise import NotifyBase
from apprise import NotifyType
from apprise import NotifyFormat
from apprise import NotifyImageSize
from apprise import __version__
from apprise.Apprise import __load_matrix
import pytest


def test_apprise():
    """
    API: Apprise() object

    """
    # Caling load matix a second time which is an internal function causes it
    # to skip over content already loaded into our matrix and thefore accesses
    # other if/else parts of the code that aren't otherwise called
    __load_matrix()

    a = Apprise()

    # no items
    assert(len(a) == 0)

    # Create an Asset object
    asset = AppriseAsset(theme='default')

    # We can load the device using our asset
    a = Apprise(asset=asset)

    # We can load our servers up front as well
    servers = [
        'faast://abcdefghijklmnop-abcdefg',
        'kodi://kodi.server.local',
    ]

    a = Apprise(servers=servers)

    # 3 servers loaded
    assert(len(a) == 2)

    # We can add another server
    assert(
        a.add('mmosts://mattermost.server.local/'
              '3ccdd113474722377935511fc85d3dd4') is True)
    assert(len(a) == 3)

    # We can empty our set
    a.clear()
    assert(len(a) == 0)

    # An invalid schema
    assert(
        a.add('this is not a parseable url at all') is False)
    assert(len(a) == 0)

    # An unsupported schema
    assert(
        a.add('invalid://we.just.do.not.support.this.plugin.type') is False)
    assert(len(a) == 0)

    # A poorly formatted URL
    assert(
        a.add('json://user:@@@:bad?no.good') is False)
    assert(len(a) == 0)

    # Add a server with our asset we created earlier
    assert(
        a.add('mmosts://mattermost.server.local/'
              '3ccdd113474722377935511fc85d3dd4', asset=asset) is True)

    # Clear our server listings again
    a.clear()

    # No servers to notify
    assert(a.notify(title="my title", body="my body") is False)

    class BadNotification(NotifyBase):
        def __init__(self, **kwargs):
            super(BadNotification, self).__init__()

            # We fail whenever we're initialized
            raise TypeError()

    class GoodNotification(NotifyBase):
        def __init__(self, **kwargs):
            super(GoodNotification, self).__init__(
                notify_format=NotifyFormat.HTML)

        def notify(self, **kwargs):
            # Pretend everything is okay
            return True

    # Store our bad notification in our schema map
    SCHEMA_MAP['bad'] = BadNotification

    # Store our good notification in our schema map
    SCHEMA_MAP['good'] = GoodNotification

    # Just to explain what is happening here, we would have parsed the
    # url properly but failed when we went to go and create an instance
    # of it.
    assert(a.add('bad://localhost') is False)
    assert(len(a) == 0)

    assert(a.add('good://localhost') is True)
    assert(len(a) == 1)

    # Bad Notification Type is still allowed as it is presumed the user
    # know's what their doing
    assert(a.notify(
        title="my title", body="my body", notify_type='bad') is True)

    # No Title/Body combo's
    assert(a.notify(title=None, body=None) is False)
    assert(a.notify(title='', body=None) is False)
    assert(a.notify(title=None, body='') is False)

    # As long as one is present, we're good
    assert(a.notify(title=None, body='present') is True)
    assert(a.notify(title='present', body=None) is True)
    assert(a.notify(title="present", body="present") is True)

    # Clear our server listings again
    a.clear()

    class ThrowNotification(NotifyBase):
        def notify(self, **kwargs):
            # Pretend everything is okay
            raise TypeError()

    class RuntimeNotification(NotifyBase):
        def notify(self, **kwargs):
            # Pretend everything is okay
            raise RuntimeError()

    class FailNotification(NotifyBase):

        def notify(self, **kwargs):
            # Pretend everything is okay
            return False

    # Store our bad notification in our schema map
    SCHEMA_MAP['throw'] = ThrowNotification

    # Store our good notification in our schema map
    SCHEMA_MAP['fail'] = FailNotification

    # Store our good notification in our schema map
    SCHEMA_MAP['runtime'] = RuntimeNotification

    assert(a.add('runtime://localhost') is True)
    assert(a.add('throw://localhost') is True)
    assert(a.add('fail://localhost') is True)
    assert(len(a) == 3)

    # Test when our notify both throws an exception and or just
    # simply returns False
    assert(a.notify(title="present", body="present") is False)

    # Create a Notification that throws an unexected exception
    class ThrowInstantiateNotification(NotifyBase):
        def __init__(self, **kwargs):
            # Pretend everything is okay
            raise TypeError()
    SCHEMA_MAP['throw'] = ThrowInstantiateNotification

    # Reset our object
    a.clear()
    assert(len(a) == 0)

    # Instantiate a good object
    plugin = a.instantiate('good://localhost')
    assert(isinstance(plugin, NotifyBase))

    # We an add already substatiated instances into our Apprise object
    a.add(plugin)
    assert(len(a) == 1)

    # Reset our object again
    a.clear()
    try:
        a.instantiate('throw://localhost', suppress_exceptions=False)
        assert(False)

    except TypeError:
        assert(True)
    assert(len(a) == 0)

    assert(a.instantiate(
        'throw://localhost', suppress_exceptions=True) is None)
    assert(len(a) == 0)


def test_apprise_notify_formats(tmpdir):
    """
    API: Apprise() TextFormat tests

    """
    # Caling load matix a second time which is an internal function causes it
    # to skip over content already loaded into our matrix and thefore accesses
    # other if/else parts of the code that aren't otherwise called
    __load_matrix()

    a = Apprise()

    # no items
    assert(len(a) == 0)

    class TextNotification(NotifyBase):
        # set our default notification format
        notify_format = NotifyFormat.TEXT

        def __init__(self, **kwargs):
            super(TextNotification, self).__init__()

        def notify(self, **kwargs):
            # Pretend everything is okay
            return True

    class HtmlNotification(NotifyBase):

        # set our default notification format
        notify_format = NotifyFormat.HTML

        def __init__(self, **kwargs):
            super(HtmlNotification, self).__init__()

        def notify(self, **kwargs):
            # Pretend everything is okay
            return True

    class MarkDownNotification(NotifyBase):

        # set our default notification format
        notify_format = NotifyFormat.MARKDOWN

        def __init__(self, **kwargs):
            super(MarkDownNotification, self).__init__()

        def notify(self, **kwargs):
            # Pretend everything is okay
            return True

    # Store our notifications into our schema map
    SCHEMA_MAP['text'] = TextNotification
    SCHEMA_MAP['html'] = HtmlNotification
    SCHEMA_MAP['markdown'] = MarkDownNotification

    # Test Markdown; the above calls the markdown because our good://
    # defined plugin above was defined to default to HTML which triggers
    # a markdown to take place if the body_format specified on the notify
    # call
    assert(a.add('html://localhost') is True)
    assert(a.add('html://another.server') is True)
    assert(a.add('html://and.another') is True)
    assert(a.add('text://localhost') is True)
    assert(a.add('text://another.server') is True)
    assert(a.add('text://and.another') is True)
    assert(a.add('markdown://localhost') is True)
    assert(a.add('markdown://another.server') is True)
    assert(a.add('markdown://and.another') is True)

    assert(len(a) == 9)

    assert(a.notify(title="markdown", body="## Testing Markdown",
           body_format=NotifyFormat.MARKDOWN) is True)

    assert(a.notify(title="text", body="Testing Text",
           body_format=NotifyFormat.TEXT) is True)

    assert(a.notify(title="html", body="<b>HTML</b>",
           body_format=NotifyFormat.HTML) is True)


def test_apprise_asset(tmpdir):
    """
    API: AppriseAsset() object

    """
    a = AppriseAsset(theme=None)
    # Default theme
    assert(a.theme == 'default')

    a = AppriseAsset(
        theme='dark',
        image_path_mask='/{THEME}/{TYPE}-{XY}{EXTENSION}',
        image_url_mask='http://localhost/{THEME}/{TYPE}-{XY}{EXTENSION}',
    )

    a.default_html_color = '#abcabc'
    a.html_notify_map[NotifyType.INFO] = '#aaaaaa'

    assert(a.color('invalid', tuple) == (171, 202, 188))
    assert(a.color(NotifyType.INFO, tuple) == (170, 170, 170))

    assert(a.color('invalid', int) == 11258556)
    assert(a.color(NotifyType.INFO, int) == 11184810)

    assert(a.color('invalid', None) == '#abcabc')
    assert(a.color(NotifyType.INFO, None) == '#aaaaaa')
    # None is the default
    assert(a.color(NotifyType.INFO) == '#aaaaaa')

    # Invalid Type
    try:
        a.color(NotifyType.INFO, dict)
        # We should not get here (exception should be thrown)
        assert(False)

    except ValueError:
        # The exception we expect since dict is not supported
        assert(True)

    except Exception:
        # Any other exception is not good
        assert(False)

    assert(a.image_url(NotifyType.INFO, NotifyImageSize.XY_256) ==
           'http://localhost/dark/info-256x256.png')

    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=False) == '/dark/info-256x256.png')

    # This path doesn't exist so image_raw will fail (since we just
    # randompyl picked it for testing)
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is None)

    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is None)

    # Create a new object (with our default settings)
    a = AppriseAsset()

    # Our default configuration can access our file
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is not None)

    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is not None)

    # Create a temporary directory
    sub = tmpdir.mkdir("great.theme")

    # Write a file
    sub.join("{0}-{1}.png".format(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
    )).write("the content doesn't matter for testing.")

    # Create an asset that will reference our file we just created
    a = AppriseAsset(
        theme='great.theme',
        image_path_mask='%s/{THEME}/{TYPE}-{XY}.png' % dirname(sub.strpath),
    )

    # We'll be able to read file we just created
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is not None)

    # We can retrieve the filename at this point even with must_exist set
    # to True
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is not None)

    # If we make the file un-readable however, we won't be able to read it
    # This test is just showing that we won't throw an exception
    if getuid() == 0:
        # Root always over-rides 0x000 permission settings making the below
        # tests futile
        pytest.skip('The Root user can not run file permission tests.')

    chmod(dirname(sub.strpath), 0o000)
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is None)

    # Our path doesn't exist anymore using this logic
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is None)

    # Return our permission so we don't have any problems with our cleanup
    chmod(dirname(sub.strpath), 0o700)

    # Our content is retrivable again
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is not None)

    # our file path is accessible again too
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is not None)

    # We do the same test, but set the permission on the file
    chmod(a.image_path(NotifyType.INFO, NotifyImageSize.XY_256), 0o000)

    # our path will still exist in this case
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=True) is not None)

    # but we will not be able to open it
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is None)

    # Restore our permissions
    chmod(a.image_path(NotifyType.INFO, NotifyImageSize.XY_256), 0o640)

    # Disable all image references
    a = AppriseAsset(image_path_mask=False, image_url_mask=False)

    # We always return none in these calls now
    assert(a.image_raw(NotifyType.INFO, NotifyImageSize.XY_256) is None)
    assert(a.image_url(NotifyType.INFO, NotifyImageSize.XY_256) is None)
    assert(a.image_path(NotifyType.INFO, NotifyImageSize.XY_256,
           must_exist=False) is None)
    assert(a.image_path(NotifyType.INFO, NotifyImageSize.XY_256,
           must_exist=True) is None)

    # Test our default extension out
    a = AppriseAsset(
        image_path_mask='/{THEME}/{TYPE}-{XY}{EXTENSION}',
        image_url_mask='http://localhost/{THEME}/{TYPE}-{XY}{EXTENSION}',
        default_extension='.jpeg',
    )
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        must_exist=False) == '/default/info-256x256.jpeg')

    assert(a.image_url(
        NotifyType.INFO,
        NotifyImageSize.XY_256) == 'http://localhost/'
                                   'default/info-256x256.jpeg')

    # extension support
    assert(a.image_path(
        NotifyType.INFO,
        NotifyImageSize.XY_128,
        must_exist=False,
        extension='.ico') == '/default/info-128x128.ico')

    assert(a.image_url(
        NotifyType.INFO,
        NotifyImageSize.XY_256,
        extension='.test') == 'http://localhost/'
                              'default/info-256x256.test')


def test_apprise_details():
    """
    API: Apprise() Details

    """

    # Caling load matix a second time which is an internal function causes it
    # to skip over content already loaded into our matrix and thefore accesses
    # other if/else parts of the code that aren't otherwise called
    __load_matrix()

    a = Apprise()

    # Details object
    details = a.details()

    # Dictionary response
    assert isinstance(details, dict)

    # Apprise version
    assert 'version' in details
    assert details.get('version') == __version__

    # Defined schemas identify each plugin
    assert 'schemas' in details
    assert isinstance(details.get('schemas'), list)

    # We have an entry per defined plugin
    assert 'asset' in details
    assert isinstance(details.get('asset'), dict)
    assert 'app_id' in details['asset']
    assert 'app_desc' in details['asset']
    assert 'default_extension' in details['asset']
    assert 'theme' in details['asset']
    assert 'image_path_mask' in details['asset']
    assert 'image_url_mask' in details['asset']
    assert 'image_url_logo' in details['asset']

    # All plugins must have a name defined; the below generates
    # a list of entrys that do not have a string defined.
    assert(not len([x['service_name'] for x in details['schemas']
                   if not compat_is_basestring(x['service_name'])]))
