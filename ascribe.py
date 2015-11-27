from io import BytesIO
import requests
import os

import json

from rinoh.font import TypeFace, ITALIC
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, MEDIUM, LIGHT

from rinoh.layout import Container, DownExpandingContainer, UpExpandingContainer
from rinoh.layout import FlowablesContainer, ChainedContainer
from rinoh.dimension import DimensionUnit, CM, PT, INCH
from rinoh.document import DocumentSection, Page, PORTRAIT
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher, Var
from rinoh.backend import pdf
from rinoh.flowable import (GroupedFlowablesStyle, GroupedFlowables,
                            HorizontallyAlignedFlowableStyle, CENTER)
from rinoh.paragraph import Paragraph, LEFT, SINGLE
from rinoh.structure import FieldList, LabeledFlowable, HorizontalRule, ListItem
from rinoh.styles import ParagraphStyle
from rinoh.float import Image, FIT

from rinoh.text import BOLD, TextStyle, SingleStyledText, StyledText
from rinoh.color import HexColor

from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.templates.base import DocumentTemplate, ContentsPart, DocumentOptions
from rinohlib.stylesheets.matcher import matcher

from flask import Flask, request, send_file

app = Flask(__name__)


# sample JSON input
data_test = {'digital_work': {'hash': '08efe77013e52d0a372e7bb611d982c9', 'mime': 'image', 'isEncoding': 0,
                              'encoding_urls': None,
                              'url_safe': 'https://d1qjsxua1o9x03.cloudfront.net/local%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2Fe65f70f5-1201-4f92-bc9c-f1ce5ac40025%2Fdigitalwork%2Fe65f70f5-1201-4f92-bc9c-f1ce5ac40025.jpg',
                              'url': 'https://d1qjsxua1o9x03.cloudfront.net/local/b6d767d2f8ed5d21a44b0e5886680cb9/e65f70f5-1201-4f92-bc9c-f1ce5ac40025/digitalwork/e65f70f5-1201-4f92-bc9c-f1ce5ac40025.jpg',
                              'id': 2309},
             'ownership_history': [['Jul. 21, 2015, 21:07:59', 'Registered by Schweinehund']],
             'bitcoin_id': '1ECqK66oqyJguVuuJfyoSdsdnsc6kFZKQ7',
             'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/local%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2Fe65f70f5-1201-4f92-bc9c-f1ce5ac40025%2Fthumbnail%2F600x600%2Fthumbnail.png',
             'num_editions': 12, 'edition_number': 7, 'owner': 'Schweinehund',
             'crypto_signature': 'AA59A221B5DFADC1BA5B976226A34BEFFDFCF29A8631817C63B0B1063C159A76590E0D15E63A909B701FF33CBFD4B7193689CA39CB27EA84CB79E5744589923DE9A9C91237D7C0C79A11ED1A3E60E1E15357D188A248DBED9E2818F6E60FB3F947C2F28B65C7D4B337716CB735BBCA6174942692281172B5EDF5A79D2564733FL',
             'crypto_message': '1 wide*1 wide*7/12*111*2015Jul21-21:07:59', 'artist_name': '1 wide',
             'yearAndEdition_str': '111, 7/12', 'title': '1 wide'}

data_faulty = {'yearAndEdition_str': '111, 1/12', 'bitcoin_id': '1LaemJEou4pYLDCw3Eot9ZGrBS7gAtJTT4',
               'artist_name': '1 long', 'owner': 'Schweinehund', 'num_editions': 12,
               'crypto_message': '1 long*1 long*1/12*111*2015Jul21-21:08:16', 'edition_number': 1,
               'ownership_history': [['Jul. 21, 2015, 21:08:16', 'Registered by Schweinehund']],
               'digital_work': {'mime': 'image', 'hash': 'd51eb8656b3cc68545e92746594f6e4c',
                                'encoding_urls': None,
                                'url_safe': 'https://d1qjsxua1o9x03.cloudfront.net/local%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F4998038c-3ea0-4502-9a3a-4e2ae6c761f2%2Fdigitalwork%2F4998038c-3ea0-4502-9a3a-4e2ae6c761f2.jpg',
                                'url': 'https://d1qjsxua1o9x03.cloudfront.net/local/b6d767d2f8ed5d21a44b0e5886680cb9/4998038c-3ea0-4502-9a3a-4e2ae6c761f2/digitalwork/4998038c-3ea0-4502-9a3a-4e2ae6c761f2.jpg',
                                'id': 2310, 'isEncoding': 0}, 'title': '1 long',
               'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/local%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F4998038c-3ea0-4502-9a3a-4e2ae6c761f2%2Fthumbnail%2F600x600%2Fthumbnail.png',
               'crypto_signature': '65312234EDEFE06054DCDEE309ED3EDDAE91CC7D542D5F7085CB40F0CA24A24642787AF8C798BE4AD122E6A40E7BE9D0B44AA75CB5D839133098D49D4E1A4AB5BE9CF7262089258460E2C61B3C810DBCA053F3844A93022A33037661414219B84CAFB5E0CB19C2688AA8C2134FDF69AE9C49714EE4E039A8D342D6F8D276A4BDL'}


with open('template.rst') as file:
    TEMPLATE = ReStructuredTextParser().parse(file)


FONT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')

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
MATCHER['header verify'] = header / ...  / Paragraph.like(classes=['verify'])
MATCHER['header rule'] = header / HorizontalRule

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
                                       font_size=9*PT,
                                       line_spacing=SINGLE,
                                       indent_first=0*PT,
                                       space_above=0*PT,
                                       space_below=0*PT,
                                       justify=LEFT,
                                       kerning=True,
                                       ligatures=True,
                                       hyphenate=False,
                                       hyphen_lang='en_US',
                                       hyphen_chars=4)

STYLESHEET('title',
           typeface=GIBSON,
           font_weight=LIGHT,
           font_size=29*PT,
           font_color=HexColor('#D8127D'),
           space_above=0,
           space_below=8*PT)

STYLESHEET('body',
           base='default',
           font_color=Var('grey'),
           space_above=5*PT,
           space_below=0*PT)

STYLESHEET('header paragraph',
           base='body',
           font_size=9.5*PT,
           space_above=1*PT)

STYLESHEET('header verify',
           base='header paragraph',
           font_color=Var('blue'))

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
           font_size=8*PT,
           font_color=Var('blue'))

STYLESHEET('crypto field paragraph',
           base='body',
           font_size=8*PT,
           font_color=Var('grey'))

STYLESHEET('heading level 1',
           typeface=GIBSON,
           font_weight=LIGHT,
           font_size=18*PT,
           font_color=HexColor('#121417'),
           line_spacing=SINGLE,
           space_above=0,
           space_below=4*PT,
           number_format=None)

STYLESHEET('heading level 2',
           base='heading level 1',
           font_weight=REGULAR,
           font_size=9*PT,
           space_above=8*PT)

STYLESHEET('image',
           horizontal_align=CENTER)

STYLESHEET('footer paragraph',
           base='default',
           justify=CENTER)

STYLESHEET('logo',
           typeface=ASCRIBE,
           font_weight=REGULAR)

STYLESHEET('horizontal rule',
           stroke_width=1*PX,
           stroke_color=HexColor('#CECECE'),
           space_above=8*PT,
           space_below=0)

STYLESHEET('header rule',
           stroke_width=1*PX,
           stroke_color=HexColor('#D6D6D6'),
           space_above=10*PT,
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
        yield document.image


class AscribePage(Page):
    padding = 30 * PX
    topmargin = padding
    bottommargin = padding
    leftmargin = rightmargin = padding
    column_spacing = padding
    split_ratio = 50 # (%) artwork - meta

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
                                          bottom=self.footer.top - 20*PT,
                                          width=column_width)
        self.column1 << ArtworkFlowables()
        self.column2 = ChainedContainer('column2', body, chain,
                                        left=column_width + self.column_spacing,
                                        top=self.header.bottom
                                            + self.padding,
                                        bottom=self.footer.top - 20*PT)


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
        thumbnail = requests.get(data['thumbnail'])
        image_data = BytesIO(thumbnail.content)
        image_data.seek(0)
        self.image = Image(image_data, scale=FIT)
        super().__init__(TEMPLATE, options=OPTIONS, backend=pdf)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


def render_and_send_certificate(data):
    certificate = AscribeCertificate(data)
    pdf_file = BytesIO()
    print('Start pdf rendering')
    certificate.render(file=pdf_file)
    print('Render complete')
    pdf_file.seek(0)
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
        print('Error: ' + str(e))
        pass


@app.route('/', methods=['GET'])
def test():
    try:
        return render_and_send_certificate(data_test)
    except Exception as e:
        print('Error: ' + str(e))
        pass


if __name__ == "__main__":
    app.run(debug=True)
