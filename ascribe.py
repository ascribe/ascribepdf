
from io import BytesIO
from time import strptime, strftime
from urllib.request import urlretrieve

import json

from PIL import Image as PILImage

# pip install git+https://github.com/brechtm/rinohtype.git@ascribe
from rinoh.font import TypeFace
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, MEDIUM

from rinoh.layout import Container, DownExpandingContainer, Chain
from rinoh.dimension import CM, PT, PERCENT
from rinoh.document import Document, Page, LANDSCAPE
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher
from rinoh.backend import pdf
from rinoh.flowable import GroupedFlowablesStyle
from rinoh.paragraph import Paragraph
from rinoh.structure import FieldList, LabeledFlowable
from rinoh.styles import ParagraphStyle
from rinoh.annotation import AnnotatedText, HyperLink
from rinoh.float import Image

from rinoh.text import BOLD, TextStyle, SingleStyledText, StyledText
from rinoh.draw import HexColor

from rinohlib.fonts.texgyre.pagella import typeface as pagella

from flask import Flask, request, send_file
app = Flask(__name__)


# sample JSON input
# {
#   "image_url": "https:\/\/ascribe0.s3.amazonaws.com\/media\/thumbnails\/14171888825\/b55dcae37fa6b9c82330fd5d6800a15ee14ca41cdd0bcb592579cf9eba16c11f.png",
#   "artist": "Terry Artist",
#   "crypto_id": "jisadf8734hf83hsdfjklshdf3",
#   "title": "Lakeside",
#   "ownership_history": [
#     [
#       "2014\/11\/13 07:11",
#       "John Artist",
#       "john@artist.com"
#     ]
#   ],
#   "owner": [
#     "John Artist",
#     "john@artist.com"
#   ],
#   "editions": [
#     1,
#     10
#   ],
#   "status": "Loaning",
#   "loan_history": [
#     [
#       "2014\/11\/13 11:11",
#       "John Artist",
#       "larry@gallery.com"
#     ]
#   ],
#   "year": 1998
# }


DATETIME_IN_FMT = '%Y/%m/%d %H:%M'

DATETIME_OUT_FMT = '%b. %d, %Y, %I:%M %p'


MATCHER = StyledMatcher()
MATCHER['logo'] = Paragraph.like('logo')
MATCHER['logotype'] = StyledText.like('logotype')

MATCHER['image'] = Image

MATCHER['default'] = Paragraph
MATCHER['artist'] = Paragraph.like('artist')
MATCHER['title'] = Paragraph.like('title')
MATCHER['year'] = Paragraph.like('year')
MATCHER['field list'] = FieldList
MATCHER['section title'] = Paragraph.like('section title')


MERCURY_TYPEFACE = TypeFace('Mercury', OpenTypeFont('Mercury_Medium.otf',
                                                    weight=MEDIUM))
ASCRIBE_TYPEFACE = TypeFace('ascribe', OpenTypeFont('ascribe.ttf',
                                                    weight=REGULAR))
ASCRIBE_GREEN = HexColor('48DACB')


STYLESHEET = StyleSheet('ascribe', matcher=MATCHER)
STYLESHEET['logo'] = ParagraphStyle(typeface=MERCURY_TYPEFACE,
                                    font_size=26*PT,
                                    font_color=HexColor('222222'),
                                    space_below=36*PT)
STYLESHEET['logotype'] = TextStyle(typeface=ASCRIBE_TYPEFACE,
                                   font_size=23*PT,
                                   font_color=ASCRIBE_GREEN)

STYLESHEET['default'] = ParagraphStyle(typeface=pagella,
                                       font_size=12*PT,
                                       space_below=6*PT)
STYLESHEET['artist'] = ParagraphStyle(base='default',
                                      font_size=14*PT)
STYLESHEET['title'] = ParagraphStyle(base='default',
                                     font_weight=BOLD,
                                     font_size=18*PT,
                                     space_below=10*PT)
STYLESHEET['year'] = ParagraphStyle(base='default',
                                     space_below=10*PT)
STYLESHEET['field list'] = GroupedFlowablesStyle(space_below=15*PT)
STYLESHEET['section title'] = ParagraphStyle(base='default',
                                             font_weight=BOLD,
                                             font_size=16*PT,
                                             space_above=6*PT,
                                             space_below=8*PT)


class AscribePage(Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM
    left_column_width = 10*CM
    column_spacing = 1*CM

    def __init__(self, document):
        super().__init__(document, A4, LANDSCAPE)
        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        body = Container('body', self, self.leftmargin, self.topmargin,
                         body_width, body_height)

        self.header = DownExpandingContainer('header', body, 0*PT, 0*PT)
        logotype = SingleStyledText('\ue603', style='logotype')
        self.header << Paragraph('ascribe ' + logotype, style='logo')

        self.column1 = Container('column1', body, 0*PT, self.header.bottom,
                                 width=self.left_column_width,
                                 chain=document.image)
        self.column2 = Container('column2', body,
                                 self.left_column_width + self.column_spacing,
                                 self.header.bottom,
                                 chain=document.text)


class AscribeCertificate(Document):
    namespace = 'http://www.mos6581.org/ns/rficpaper'

    def __init__(self, data):
        title = ' - '.join((data['artist'], data['title']))
        super().__init__(STYLESHEET, backend=pdf, title=title)

        image_data = BytesIO()
        f, _ = urlretrieve(data['image_url'])
        input_image = PILImage.open(f)
        if 'transparency' in input_image.info:
            print('TRANSP')
            foreground = input_image.convert('RGBA')
            background = PILImage.new('RGBA', foreground.size, (255, 255, 255, 255))
            input_image = PILImage.alpha_composite(background, foreground)
        input_image.convert('RGB').save(image_data, 'PDF') #, **pilim.info) #, Quality=100)
        self.image = Chain(self)
        self.image << Image(image_data, width=100*PERCENT)

        self.text = Chain(self)
        self.text << Paragraph(data['artist'], style='artist')
        self.text << Paragraph(data['title'], style='title')
        self.text << Paragraph(str(data['year']), style='year')

        fields = []
        nr_edition, total_editions = data['editions']
        fields.append(LabeledFlowable(Paragraph('Editions:'),
                                      Paragraph('{}/{}'.format(nr_edition,
                                                               total_editions))))
        fields.append(LabeledFlowable(Paragraph('Status:'),
                                      Paragraph(data['status'])))
        owner_name, owner_email = data['owner']
        email_link = AnnotatedText(owner_email,
                                   annotation=HyperLink('mailto:' + owner_email))
        fields.append(LabeledFlowable(Paragraph('Owner:'),
                                      Paragraph(owner_name + ', ' + email_link)))
        fields.append(LabeledFlowable(Paragraph('Crypto ID:'),
                                      Paragraph(data['crypto_id'])))
        self.text << FieldList(fields)

        self.text << Paragraph('Provenance/Ownership History',
                               style='section title')
        self._history(data['ownership_history'],
                      'ownership ascribed to')

        self.text << Paragraph('Consignment/Loan History',
                               style='section title')
        self._history(data['loan_history'], 'loaned to')

    def _history(self, items, action):
        for dtime_str, name, email in items:
            dtime = strptime(dtime_str, DATETIME_IN_FMT)
            self.text << Paragraph(strftime(DATETIME_OUT_FMT, dtime) +
                                   ' ' + action + ' ' + name + ', ' + email)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


@app.route('/', methods=['POST'])
def certificate():
    json_data = request.form['data']
    data = json.loads(json_data)
    certificate = AscribeCertificate(data)
    pdf_file = certificate.render()
    return send_file(pdf_file,
                     attachment_filename='certificate.pdf',
                     mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)
