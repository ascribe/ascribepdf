from io import BytesIO, StringIO

import json
import requests
import os


import qrcode

from docutils import nodes
from docutils.parsers import rst

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
from rinoh.frontend.rst.nodes import Image as rstImage

from rinohlib.templates.base import DocumentTemplate, ContentsPart, DocumentOptions
from rinohlib.stylesheets.matcher import matcher

from flask import Flask, request, send_file
from jinja2 import Environment, PackageLoader

app = Flask(__name__)
app.config.from_object(
    os.environ.get('ASCRIBEPDF_CONFIG_MODULE', 'config.Prod'))

PATH = os.path.dirname(os.path.realpath(__file__))
FONT_PATH = os.path.join(PATH, 'fonts')

jinja_env = Environment(loader=PackageLoader(__name__))

DEFAULT_TEMPLATE_FILENAME = 'edition.rst'
TEMPLATE_DIAMOND = jinja_env.get_template('diamond.rst')

# sample JSON input
data_test = {'title': '111111111', 'filesize': 370611, 'edition_number': 10,
             'check_stamp_query': '?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
             'owner_timestamp': 'Jul. 29 2015, 16:21:51', 'artist_name': '1111111111',
             'digital_work': {'isEncoding': 0, 'mime': 'image', 'hash': '16a78cd2bb628fd6fb14582668ed72d7',
                              'encoding_urls': None, 'id': 2509,
                              'url_safe': 'https://d1qjsxua1o9x03.cloudfront.net/live%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F589566d5-5452-48ef-a7c9-88f5f4aefb86%2Fdigitalwork%2F589566d5-5452-48ef-a7c9-88f5f4aefb86.png',
                              'url': 'https://d1qjsxua1o9x03.cloudfront.net/live/b6d767d2f8ed5d21a44b0e5886680cb9/589566d5-5452-48ef-a7c9-88f5f4aefb86/digitalwork/589566d5-5452-48ef-a7c9-88f5f4aefb86.png'},
             'bitcoin_id': '1FE7GhESMTN5tUS3TSma4CqTtgZVTV9fnR',
             'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/media%2Fthumbnails%2Fc681cdee-f852-4ade-9179-61da68bf7a45%2Fmothership01.jpg',
             'owner': 'Schweinehund', 'crypto_message': '1111111111*111111111*10/13*2015*2015Jul29-16:21:51',
             'crypto_signature': '2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
             'yearAndEdition_str': '2015, 10/13', 'filename': '.png',
             'check_stamp_url': 'http://localhost.com:3000/coa_verify/?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
             'ownership_history': [['Jul. 29, 2015, 16:21:51', 'Registered by Schweinehund']], 'num_editions': 13,
             'verify_owner_url': 'http://localhost.com:3000/coa_verify/'}


class qrimage(nodes.image):
    pass


class QRCode(rst.Directive):
    required_arguments = 1

    def run(self):
        self.options['content'] = rst.directives.uri(self.arguments[0])
        image_node = qrimage(rawsource=self.block_text, **self.options)
        return [image_node]


rst.directives.register_directive('qrcode', QRCode)


class QRImage(rstImage):
    def build_flowable(self):
        img = qrcode.make(self.get('content'))
        output = BytesIO()
        img.save(output)
        output.flush()
        output.seek(0)
        return Image(output, width=3*CM, style='QR code')


def font(filename):
    return os.path.join(FONT_PATH, filename)


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
           horizontal_align=CENTER)

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

    def __init__(self, data, template_filename=None):
        self.data = data
        template_filename = template_filename or DEFAULT_TEMPLATE_FILENAME
        template = jinja_env.get_template(template_filename)
        with StringIO(template.render(**data)) as rst_file:
            content_flowables = ReStructuredTextParser().parse(rst_file)
        super().__init__(content_flowables, options=OPTIONS, backend=pdf)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


class AscribeCertificateDiamond(DocumentTemplate):
    sections = [AscribeCertificateSection]

    def __init__(self, data):
        self.data = data
        with StringIO(TEMPLATE_DIAMOND.render(**data)) as rst_file:
            content_flowables = ReStructuredTextParser().parse(rst_file)
        super().__init__(content_flowables, options=OPTIONS, backend=pdf)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


def render_certificate(data, to_file=False, template_filename=None):
    data['crypto_signature'] = '\N{ZERO WIDTH SPACE}'.join(data['crypto_signature'])
    certificate = AscribeCertificate(data, template_filename=template_filename)
    print('Start pdf rendering')
    if to_file:
        certificate.render('test')
    else:
        pdf_file = BytesIO()
        certificate.render(file=pdf_file)
        pdf_file.seek(0)
        return pdf_file
    print('Render complete')


def render_certificate_diamond(data, to_file=False):
    data['crypto_signature'] = '\N{ZERO WIDTH SPACE}'.join(data['crypto_signature'])
    certificate = AscribeCertificateDiamond(data)
    print('Start pdf rendering')
    if to_file:
        certificate.render('test')
    else:
        pdf_file = BytesIO()
        certificate.render(file=pdf_file)
        pdf_file.seek(0)
        return pdf_file
    print('Render complete')


def render_and_send_certificate(data, template_filename=None):
    pdf_file = render_certificate(data, template_filename=template_filename)
    response = send_file(pdf_file,
                         attachment_filename='certificate.pdf',
                         mimetype='application/pdf')
    response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
    return response


def render_and_send_certificate_diamond(data):
    pdf_file = render_certificate_diamond(data)
    response = send_file(pdf_file,
                         attachment_filename='certificate.pdf',
                         mimetype='application/pdf')
    response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
    return response


@app.route('/piece', methods=['POST'])
def generate_piece_certificate():
    try:
        return render_and_send_certificate(request.json,
                                           template_filename='piece.rst')
    except Exception as e:
        # TODO use logging
        print(e)


@app.route('/', methods=['POST'])
def generate_edition_certificate():
    print(request)
    print(request.form)
    json_data = request.form['data']
    data = json.loads(json_data)
    print(data)
    try:
        return render_and_send_certificate(data,
                                           template_filename='edition.rst')
    except Exception as e:
        # TODO use logging
        print(e)
        pass


@app.route('/', methods=['GET'])
def test():
    try:
        return render_and_send_certificate(data_test)
    except Exception as e:
        print('Error: ' + str(e))
        pass


@app.route('/diamondscoa', methods=['POST'])
def certificate_diamond():
    print(request)
    print(request.form)
    json_data = request.form['data']
    data = json.loads(json_data)
    print(data)
    try:
        return render_and_send_certificate_diamond(data)
    except Exception as e:
        print(e)
        pass


if __name__ == "__main__":
    # render_certificate(data_test, to_file=True
    host = os.environ.get('ASCRIBEPDF_HOST', '127.0.0.1')
    app.run(host=host)
