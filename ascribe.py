from io import BytesIO
import requests
import os

import json

from rinoh.font import TypeFace, ITALIC
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, MEDIUM, LIGHT
from rinoh.font.type1 import Type1Font

from rinoh.layout import Container, DownExpandingContainer, UpExpandingContainer
from rinoh.layout import FlowablesContainer, ChainedContainer
from rinoh.dimension import DimensionUnit, CM, PT, INCH
from rinoh.document import DocumentSection, Page, PORTRAIT
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher
from rinoh.backend import pdf
from rinoh.flowable import (GroupedFlowablesStyle, GroupedFlowables,
                            HorizontallyAlignedFlowableStyle, CENTER)
from rinoh.paragraph import Paragraph
from rinoh.structure import FieldList, LabeledFlowable, HorizontalRule
from rinoh.styles import ParagraphStyle
from rinoh.annotation import AnnotatedText, HyperLink
from rinoh.float import Image, FIT

from rinoh.text import BOLD, TextStyle, SingleStyledText, StyledText
from rinoh.color import HexColor

from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.templates.base import DocumentTemplate, ContentsPart, DocumentOptions

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

DATETIME_IN_FMT = '%Y/%m/%d %H:%M'

DATETIME_OUT_FMT = '%b. %d, %Y, %I:%M %p'

MATCHER = StyledMatcher()
MATCHER['logo'] = Paragraph.like('logo')
MATCHER['logotype'] = StyledText.like('logotype')

MATCHER['image'] = Image

MATCHER['default'] = Paragraph
MATCHER['artist_name'] = Paragraph.like('artist_name')
MATCHER['title'] = Paragraph.like('title')
MATCHER['year'] = Paragraph.like('year')
MATCHER['field list'] = FieldList
MATCHER['section title'] = Paragraph.like('section title')
MATCHER['footer title'] = Paragraph.like('footer title')
MATCHER['footer label'] = FieldList.like('footer fieldlist') / LabeledFlowable / Paragraph
MATCHER['footer content'] = FieldList.like('footer fieldlist') / LabeledFlowable / GroupedFlowables / Paragraph

PATH = os.path.dirname(os.path.realpath(__file__))

MERCURY_TYPEFACE = TypeFace('Mercury', Type1Font(PATH + '/fonts/mercurymedium', weight=MEDIUM))
GIBSON_TYPEFACE_REGULAR = TypeFace('Gibson-Regular', OpenTypeFont(PATH + '/fonts/Gibson-Regular.ttf', weight=REGULAR))
GIBSON_TYPEFACE_LIGHT = TypeFace('Gibson-Light', OpenTypeFont(PATH + '/fonts/Gibson-Light.ttf', weight=LIGHT))
# MERCURY_TYPEFACE = TypeFace('Mercury', OpenTypeFont('fonts/Mercury_Medium.otf',weight=MEDIUM))
ASCRIBE_TYPEFACE = TypeFace('ascribe', OpenTypeFont(PATH + '/fonts/ascribe.ttf', weight=REGULAR))
ASCRIBE_NEW_TYPEFACE = TypeFace('ascribe-new', OpenTypeFont(PATH + '/fonts/ascribe-logo.ttf', weight=REGULAR))
ASCRIBE_GREEN = HexColor('003C69')
ASCRIBE_BLACK = HexColor('1E1E1E')

PX = DimensionUnit(1 / 96 * INCH)

STYLESHEET = StyleSheet('ascribe', matcher=MATCHER)
STYLESHEET['logo'] = ParagraphStyle(typeface=MERCURY_TYPEFACE,
                                    font_size=26 * PT,
                                    font_color=HexColor('222222'),
                                    space_below=36 * PT)
STYLESHEET['logotype'] = TextStyle(typeface=ASCRIBE_NEW_TYPEFACE,
                                   font_size=23 * PT,
                                   font_color=ASCRIBE_BLACK)

STYLESHEET['default'] = ParagraphStyle(typeface=GIBSON_TYPEFACE_REGULAR,
                                               font_size=12 * PT,
                                               space_below=6 * PT)
STYLESHEET['default-light'] = ParagraphStyle(typeface=GIBSON_TYPEFACE_LIGHT,
                                             font_size=12 * PT,
                                             space_below=6 * PT)

STYLESHEET['artist_name'] = ParagraphStyle(base='default-light',
                                           font_size=14 * PT)
STYLESHEET['title'] = ParagraphStyle(base='default',
                                     font_weight=BOLD,
                                     font_size=18 * PT,
                                     space_below=10 * PT)

STYLESHEET['year'] = ParagraphStyle(base='default-light',
                                    font_size=11 * PT,
                                    space_below=10 * PT)
STYLESHEET['field list'] = GroupedFlowablesStyle(space_below=15 * PT)
STYLESHEET['section title'] = ParagraphStyle(base='default',
                                             font_weight=BOLD,
                                             font_size=14 * PT,
                                             space_above=6 * PT,
                                             space_below=8 * PT)
STYLESHEET['footer title'] = ParagraphStyle(base='section title',
                                            font_size=14 * PT,
                                            space_below=5 * PT)
STYLESHEET['footer label'] = ParagraphStyle(base='default-light',
                                            font_size=10 * PT,
                                            space_above=1 * PT,
                                            font_color=ASCRIBE_BLACK)
STYLESHEET['footer content'] = ParagraphStyle(base='footer label',
                                              font_weight=BOLD,
                                              font_color=HexColor("003C69"))
STYLESHEET['image'] = HorizontallyAlignedFlowableStyle(horizontal_align=CENTER)


class TitleFlowables(GroupedFlowables):
    def flowables(self, document):
        meta = document.metadata
        yield Paragraph(meta['title'], style='title')
        yield meta['owner']
        yield meta['verify']
        yield HorizontalRule()


class ArtworkFlowables(GroupedFlowables):
    def flowables(self, document):
        yield document.image


class FooterFlowables(GroupedFlowables):
    def flowables(self, document):
        yield document.metadata['footer']


class AscribePage(Page):
    topmargin = 22 * PX
    bottommargin = 1 * CM
    leftmargin = rightmargin = 40 * PX
    padding = 40 * PX
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
        self.header << TitleFlowables()
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
