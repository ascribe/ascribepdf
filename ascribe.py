from io import BytesIO, StringIO
import qrcode
import requests
import os

import json

from rinoh.font import TypeFace
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, LIGHT

from rinoh.layout import Container, DownExpandingContainer, UpExpandingContainer
from rinoh.layout import FlowablesContainer, ChainedContainer
from rinoh.dimension import DimensionUnit, PT, INCH, CM
from rinoh.document import DocumentSection, Page, PORTRAIT
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher, Var
from rinoh.backend import pdf
from rinoh.flowable import GroupedFlowables, CENTER, RIGHT
from rinoh.paragraph import Paragraph, LEFT, SINGLE
from rinoh.structure import LabeledFlowable, HorizontalRule, ListItem
from rinoh.styles import ParagraphStyle
from rinoh.float import Image, FIT

from rinoh.text import StyledText
from rinoh.color import HexColor

from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.templates.base import DocumentTemplate, ContentsPart, DocumentOptions
from rinohlib.stylesheets.matcher import matcher

from flask import Flask, request, send_file
from jinja2 import Environment, PackageLoader

app = Flask(__name__)

PATH = os.path.dirname(os.path.realpath(__file__))
FONT_PATH = os.path.join(PATH, 'fonts')

jinja_env = Environment(loader=PackageLoader(__name__, '.'))

TEMPLATE = jinja_env.get_template('template.rst')

# sample JSON input
data_test = {'owner_timestamp': 'October 27, 2015 17:36:00 GMT',
             'verify_owner_url': 'http://www.ascribe.io/verify/ax43',
             'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/local%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2Fe65f70f5-1201-4f92-bc9c-f1ce5ac40025%2Fthumbnail%2F600x600%2Fthumbnail.png',
             'title': 'Life is Ephemeral',
             'num_editions': 10,
             'edition_number': 1,
             'artist_name': 'Ham Burger',
             'owner': 'Thom Stevens',
             'bitcoin_id': '1ECqK66oqyJguVuuJfyoSdsdnsc6kFZKQ7',
             'filename': 'filename.zip',
             'filesize': '54.231 MB',
             'ownership_history': [['Aug. 24, 2015, 13:05:31', 'Registered by Tom Stevens'],
                                   ['Sep 12, 2015, 13:05:31', 'Transferred to bruce@gmail.com']],
             'check_stamp_url': 'http://www.ascribe.io/check-stamp/3212DFSDF2',
             'crypto_signature': 'AA59A221B5DFADC1BA5B976226A34BEFFDFCF29A8631817C63B0B1063C159A76590E0D15E63A909B701FF33CBFD4B7193689CA39CB27EA84CB79E5744589923DE9A9C91237D7C0C79A11ED1A3E60E1E15357D188A248DBED9E2818F6E60FB3F947C2F28B65C7D4B337716CB735BBCA6174942692281172B5EDF5A79D2564733FL',
             'crypto_message': '1 wide*1 wide*7/12*111*2015Jul21-21:07:59'}



def font(filename):
    return os.path.join(FONT_PATH, filename)


GIBSON = TypeFace('Gibson',
                  OpenTypeFont(font('Gibson-Regular.ttf'), weight=REGULAR),
                  OpenTypeFont(font('Gibson-Light.ttf'), weight=LIGHT))
ASCRIBE = TypeFace('ascribe-logo',
                   OpenTypeFont(font('ascribe-logo.ttf'), weight=REGULAR))

PX = DimensionUnit(1 / 96 * INCH)

MATCHER = StyledMatcher()

header = GroupedFlowables.like('header')
footer = GroupedFlowables.like('footer')
crypto = GroupedFlowables.like(classes=['crypto'])

MATCHER['title'] = header / Paragraph.like('title')
MATCHER['header paragraph'] = header / ... / Paragraph
MATCHER['header verify'] = header / ... / Paragraph.like(classes=['verify'])
MATCHER['header rule'] = header / HorizontalRule

MATCHER['QR image'] = Image.like('QR code')

MATCHER['footer paragraph'] = footer / ... / Paragraph
MATCHER['logo'] = StyledText.like(classes=['logofont'])

MATCHER['list item'] = ListItem
MATCHER['crypto paragraph'] = crypto / ... / Paragraph
MATCHER['crypto field paragraph'] = (crypto / ... / LabeledFlowable
                                     / GroupedFlowables / Paragraph)

base_stylesheet = StyleSheet('base', matcher=matcher)
STYLESHEET = StyleSheet('ascribe', base=base_stylesheet, matcher=MATCHER)

STYLESHEET.variables['grey'] = HexColor('#747474')
STYLESHEET.variables['blue'] = HexColor('#68A8DE')

STYLESHEET['default'] = ParagraphStyle(typeface=GIBSON,
                                       font_weight=LIGHT,
                                       font_size=9 * PT,
                                       line_spacing=SINGLE,
                                       indent_first=0 * PT,
                                       space_above=0 * PT,
                                       space_below=0 * PT,
                                       justify=LEFT,
                                       kerning=True,
                                       ligatures=True,
                                       hyphenate=False,
                                       hyphen_lang='en_US',
                                       hyphen_chars=4)

STYLESHEET('title',
           typeface=GIBSON,
           font_weight=LIGHT,
           font_size=29 * PT,
           font_color=HexColor('#D8127D'),
           space_above=0,
           space_below=8 * PT)

STYLESHEET('body',
           base='default',
           font_color=Var('grey'),
           space_above=5 * PT,
           space_below=0 * PT)

STYLESHEET('header paragraph',
           base='body',
           font_size=9.5 * PT,
           space_above=1 * PT)

STYLESHEET('header verify',
           base='header paragraph',
           font_color=Var('blue'))

STYLESHEET('QR image',
           horizontal_align=RIGHT)

STYLESHEET('bulleted list',
           ordered=False,
           bullet='',
           label_suffix=None)

STYLESHEET('list item',
           label_spacing=0,
           label_min_width=0,
           label_max_width=0)

STYLESHEET('crypto paragraph',
           base='body',
           font_size=8 * PT,
           font_color=Var('blue'))

STYLESHEET('crypto field paragraph',
           base='body',
           font_size=8 * PT,
           font_color=Var('grey'))

STYLESHEET('heading level 1',
           typeface=GIBSON,
           font_weight=LIGHT,
           font_size=18 * PT,
           font_color=HexColor('#121417'),
           line_spacing=SINGLE,
           space_above=0,
           space_below=4 * PT,
           number_format=None)

STYLESHEET('heading level 2',
           base='heading level 1',
           font_weight=REGULAR,
           font_size=9 * PT,
           space_above=8 * PT)

STYLESHEET('image',
           horizontal_align=CENTER)

STYLESHEET('footer paragraph',
           base='default',
           justify=CENTER)

STYLESHEET('logo',
           typeface=ASCRIBE,
           font_weight=REGULAR)

STYLESHEET('horizontal rule',
           stroke_width=1 * PX,
           stroke_color=HexColor('#CECECE'),
           space_above=8 * PT,
           space_below=0)

STYLESHEET('header rule',
           stroke_width=1 * PX,
           stroke_color=HexColor('#D6D6D6'),
           space_above=10 * PT,
           space_below=0)


class HeaderFlowables(GroupedFlowables):
    def __init__(self):
        super().__init__(style='header')

    def flowables(self, document):
        yield Paragraph(document.metadata['title'], style='title')
        yield document.metadata['header']
        yield HorizontalRule()


class QRFlowables(GroupedFlowables):
    def flowables(self, document):
        img = qrcode.make(document.data['check_stamp_url'])
        output = BytesIO()
        img.save(output)
        output.flush()
        output.seek(0)
        yield Image(output, scale=FIT, style='QR code')


class FooterFlowables(GroupedFlowables):
    def __init__(self):
        super().__init__(style='footer')

    def flowables(self, document):
        yield document.metadata['footer']


class ArtworkFlowables(GroupedFlowables):
    def flowables(self, document):
        thumbnail = requests.get(document.data['thumbnail'])
        image_data = BytesIO(thumbnail.content)
        image_data.seek(0)
        yield Image(image_data, scale=FIT)


class AscribePage(Page):
    padding = 30 * PX
    topmargin = padding
    bottommargin = padding
    leftmargin = rightmargin = padding
    column_spacing = padding
    split_ratio = 50  # (%) artwork - meta

    def __init__(self, document_part, chain):
        options = document_part.document.options
        super().__init__(document_part,
                         options['page_size'], options['page_orientation'])
        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        body = Container('body', self, self.leftmargin, self.topmargin,
                         body_width, body_height)

        self.header = DownExpandingContainer('header', body, 0 * PT, 0 * PT)
        self.header << HeaderFlowables()
        self.qrcode = FlowablesContainer('qr', body, top=0, right=body_width,
                                         width=3 * CM,
                                         height=self.header.height - 10 * PT)
        self.qrcode << QRFlowables()
        self.footer = UpExpandingContainer('footer', body, 0 * PT, body.height)
        self.footer << FooterFlowables()

        column_width = (body_width - self.column_spacing) * (self.split_ratio / 100)
        self.column1 = FlowablesContainer('column1', body, 0 * PT,
                                          top=self.header.bottom
                                              + self.padding,
                                          bottom=self.footer.top - 20 * PT,
                                          width=column_width)
        self.column1 << ArtworkFlowables()
        self.column2 = ChainedContainer('column2', body, chain,
                                        left=column_width + self.column_spacing,
                                        top=self.header.bottom
                                            + self.padding,
                                        bottom=self.footer.top - 20 * PT)


class AscribeCertificatePart(ContentsPart):
    end_at = None

    def new_page(self, chains):
        chain, = chains
        return AscribePage(self, chain)


class AscribeCertificateSection(DocumentSection):
    parts = [AscribeCertificatePart]


OPTIONS = DocumentOptions(stylesheet=STYLESHEET,
                          page_size=A4, page_orientation=PORTRAIT)


class AscribeCertificate(DocumentTemplate):
    sections = [AscribeCertificateSection]

    def __init__(self, data):
        self.data = data
        with StringIO(TEMPLATE.render(**data)) as rst_file:
             content_flowables = ReStructuredTextParser().parse(rst_file)
        super().__init__(content_flowables, options=OPTIONS, backend=pdf)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


def render_certificate(data, to_file=False):
    data['crypto_signature'] = '\N{ZERO WIDTH SPACE}'.join(data['crypto_signature'])
    certificate = AscribeCertificate(data)
    print('Start pdf rendering')
    if to_file:
        certificate.render('test')
    else:
        pdf_file = BytesIO()
        certificate.render(file=pdf_file)
        pdf_file.seek(0)
        return pdf_file
    print('Render complete')


def render_and_send_certificate(data):
    pdf_file = render_certificate(data)
    response = send_file(pdf_file,
                         attachment_filename='certificate.pdf',
                         mimetype='application/pdf')
    response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
    return response


@app.route('/', methods=['POST'])
def certificate():
    print(request)
    print(request.form)
    json_data = request.form['data']
    data = json.loads(json_data)
    print(data)
    try:
        return render_and_send_certificate(data)
    except Exception as e:
        pass


@app.route('/', methods=['GET'])
def test():
    try:
        return render_and_send_certificate(data_test)
    except Exception as e:
        print('Error: ' + str(e))
        pass


if __name__ == "__main__":
    # render_certificate(data_test, to_file=True)
    app.run(debug=True)
