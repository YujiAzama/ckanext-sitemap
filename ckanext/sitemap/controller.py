import logging

from ckan.lib.base import BaseController
from ckan.lib.helpers import url_for
from ckan.model import Session, Package
from lxml import etree
from pylons import config, response
from pylons.decorators.cache import beaker_cache


SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

XHTML_NS = "http://www.w3.org/1999/xhtml"

log = logging.getLogger(__file__)

locales = config.get('ckan.locales_offered', '').split()


class SitemapController(BaseController):

    @staticmethod
    def _create_language_alternatives(link, url):

        for lang in locales:
            attrib = {"rel": "alternate", "hreflang": lang, "href":
                      config.get('ckan.site_url') + '/' + lang + link}
            etree.SubElement(url, '{http://www.w3.org/1999/xhtml}link', attrib)

    @beaker_cache(expire=3600*24, type='dbm', invalidate_on_startup=True)
    def _render_sitemap(self):
        root = etree.Element("urlset", nsmap={None: SITEMAP_NS, 'xhtml': XHTML_NS})
        top_url = etree.SubElement(root, 'url')
        loc = etree.SubElement(top_url, 'loc')
        loc.text = config.get('ckan.site_url')
        self._create_language_alternatives(config.get('ckan.site_url'), top_url)

        packages = Session.query(Package) \
                       .filter(Package.type=='dataset') \
                       .filter(Package.private != True) \
                       .filter(Package.state == 'active') \
                       .all()

        for package in packages:
            url = etree.SubElement(root, 'url')
            loc = etree.SubElement(url, 'loc')
            package_url = "/dataset/" + package.id
            loc.text = config.get('ckan.site_url') + package_url
            lastmod = etree.SubElement(url, 'lastmod')
            lastmod.text = package.metadata_modified.strftime('%Y-%m-%d')
            self._create_language_alternatives(package_url, url)

            for resource in package.resources:
                url = etree.SubElement(root, 'url')
                loc = etree.SubElement(url, 'loc')
                resource_url = package_url + '/resource/' + resource.id
                loc.text = config.get('ckan.site_url') + resource_url
                lastmod = etree.SubElement(url, 'lastmod')
                lastmod.text = resource.metadata_modified.strftime('%Y-%m-%d')
                self._create_language_alternatives(resource_url, url)

        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(root, encoding='utf-8',
                              xml_declaration=True, pretty_print=True)

    def view(self):
        return self._render_sitemap()
