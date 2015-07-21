from io import BytesIO
from time import strptime, strftime
import requests

import json

from PIL import Image as PILImage

# pip install git+https://github.com/brechtm/rinohtype.git@ascribe
from rinoh.font import TypeFace, ITALIC
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, MEDIUM
from rinoh.font.type1 import Type1Font

from rinoh.layout import Container, DownExpandingContainer, Chain, UpExpandingContainer
from rinoh.dimension import CM, PT, PERCENT
from rinoh.document import Document, Page, LANDSCAPE
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher
from rinoh.backend import pdf
from rinoh.flowable import GroupedFlowablesStyle, GroupedFlowables
from rinoh.paragraph import Paragraph
from rinoh.structure import FieldList, LabeledFlowable
from rinoh.styles import ParagraphStyle
from rinoh.annotation import AnnotatedText, HyperLink
from rinoh.float import Image

from rinoh.text import BOLD, TextStyle, SingleStyledText, StyledText
from rinoh.draw import HexColor

from rinohlib.fonts.texgyre.pagella import typeface as pagella
from rinohlib.fonts.texgyre.cursor import typeface as cursor
# from rinoh.fonts.adobe14 import times, courier, helvetica

from flask import Flask, request, send_file
app = Flask(__name__)


# sample JSON input
data_json = '{"title": "Coa", ' \
            '"artist_name": "Coa Tester met Ü", ' \
            '"edition_number": 1, "num_editions": 3, "yearAndEdition_str": "2012, 1/3", ' \
            '"bitcoin_ID_noPrefix": "1GETTkZMXZEWQfBHWDkMiQX97N7P5USDRQ", ' \
            '"owner": "coatest@mailinator.com", ' \
            '"ownershipHistory": [["Mar. 16, 2015, 08:42:57", "Registered by coatest@mailinator.com"]], ' \
            '"thumbnail": "https://ascribe0.s3.amazonaws.com/live/coatest@mailinator.com/2014-10-28 12.47.09 hdr/thumbnailfile/2014-10-28 12.47.09 hdr.jpg.png", ' \
            '"digital_work": {"user": "coatest@mailinator.com", "url": "https://ascribe0.s3.amazonaws.com/live/coatest@mailinator.com/2014-10-28 12.47.09 hdr/digitalworkfile/2014-10-28 12.47.09 hdr.jpg", "url_safe": "https://ascribe0.s3.amazonaws.com/live%2Fcoatest%40mailinator.com%2F2014-10-28+12.47.09+hdr%2Fdigitalworkfile%2F2014-10-28+12.47.09+hdr.jpg", "hash": "a349f07b43c65d23541a70d20d9aa817", "mime": "image", "encoding_urls": null, "isEncoding": false}, ' \
            '"crypto_message": "Coa Tester*Coa*1/3*2012*2015Mar16-08:42:57", ' \
            '"crypto_signature": "A28AF3F40B45060110512E07E62954BFC88D450753FDA4645318BFAEDE2581941AA3BBD547C4D8262221E8896594AD3AC26937825AA013D1B28C7FA11CA7197A8A0DACA16ED99C61A1E44412C8C96246460D8EA916BBA4BB758101DE21938FD73A528A1C69282EB162D88FD6585B77E768CB479EE80501647B14DCA8B9BAC876L"}'

data_json_faulty = '{"title": "Bellowing Shaman", "artist_name": "Alex Broudy", "edition_number": 1, "num_editions": 1, "yearAndEdition_str": "2011, 1/1", "bitcoin_ID_noPrefix": "1Pz4aYLG9NyV7XGhvUqLwTRwiujzmTF3oB", "owner": "info-0", "ownershipHistory": [["May. 18, 2015, 15:21:55", "Registered by info-0"]], "thumbnail": "https://d1qjsxua1o9x03.cloudfront.net/live/info-0/bellowing shaman/thumbnail/bellowing shaman.png.png", "digital_work": {"url": "https://d1qjsxua1o9x03.cloudfront.net/live/info-0/bellowing shaman/digitalwork/bellowing shaman.png", "url_safe": "https://d1qjsxua1o9x03.cloudfront.net/live%2Finfo-0%2Fbellowing+shaman%2Fdigitalwork%2Fbellowing+shaman.png", "mime": "image", "hash": "7f412c4c809f5826c7b8a28db133b572", "encoding_urls": null, "isEncoding": 0}, "crypto_message": "Alex Broudy*Bellowing Shaman*1/1*2011*2015May18-15:21:55", "crypto_signature": "31C0BE79370593A43049378751D860F1B0280F5B1B6286E3E1615BD6A735EAF744B30F8A920A6695CF87996561F11A8BF2AFAA518936F39F76B3435DAD8ABFB532DCC88538F2EFD6FB7EEF7DA5B6F717E07A8010AE57B36B464CAD112A61206CEDDB9A318F1BFD05BC5F940E53A1329556056FC0FEDD870F6121AE52D3798C90L"}'

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
MATCHER['footer label'] = FieldList.like('footer fieldlist')/LabeledFlowable/Paragraph
MATCHER['footer content'] = FieldList.like('footer fieldlist')/LabeledFlowable/GroupedFlowables/Paragraph


times_regular = Type1Font('fonts/n021003l', weight=REGULAR)
times_italic = Type1Font('fonts/n021023l', weight=REGULAR, slant=ITALIC)
times_bold = Type1Font('fonts/n021004l', weight=BOLD)
times_bold_italic = Type1Font('fonts/n021024l', weight=BOLD, slant=ITALIC)

times = TypeFace('URW Times', times_regular, times_italic, times_bold, times_bold_italic)

nimbus_medium = Type1Font('fonts/n022003l', weight=MEDIUM)
nimbus_bold = Type1Font('fonts/n022004l', weight=BOLD)
nimbus_mono = TypeFace('URW Nimbus', nimbus_medium, nimbus_bold)

MERCURY_TYPEFACE = TypeFace('Mercury', Type1Font('fonts/mercurymedium', weight=MEDIUM))
# MERCURY_TYPEFACE = TypeFace('Mercury', OpenTypeFont('fonts/Mercury_Medium.otf',weight=MEDIUM))
ASCRIBE_TYPEFACE = TypeFace('ascribe', OpenTypeFont('fonts/ascribe.ttf', weight=REGULAR))
ASCRIBE_GREEN = HexColor('48DACB')


STYLESHEET = StyleSheet('ascribe', matcher=MATCHER)
STYLESHEET['logo'] = ParagraphStyle(typeface=MERCURY_TYPEFACE,
                                    font_size=26*PT,
                                    font_color=HexColor('222222'),
                                    space_below=36*PT)
STYLESHEET['logotype'] = TextStyle(typeface=ASCRIBE_TYPEFACE,
                                   font_size=23*PT,
                                   font_color=ASCRIBE_GREEN)

STYLESHEET['default'] = ParagraphStyle(typeface=times,
                                       font_size=12*PT,
                                       space_below=6*PT)
STYLESHEET['artist_name'] = ParagraphStyle(base='default',
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
STYLESHEET['footer title'] = ParagraphStyle(base='section title',
                                             font_size=14*PT,
                                             space_below=5*PT)
STYLESHEET['footer label'] = ParagraphStyle(base='default',
                                             font_size=10*PT,
                                             space_above=1*PT,
                                             font_color=HexColor("#444444"))
STYLESHEET['footer content'] = ParagraphStyle(base='footer label',
                                              font_weight=BOLD,
                                              font_color=HexColor("#48DACB"))

class AscribePage(Page):
    topmargin = 2*CM
    bottommargin = 1*CM
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
        # self.header << Paragraph(logotype, style='logo')

        self.column1 = Container('column1', body, 0*PT, self.header.bottom,
                                 width=self.left_column_width,
                                 chain=document.image)
        self.column2 = Container('column2', body,
                                 self.left_column_width + self.column_spacing,
                                 self.header.bottom,
                                 chain=document.text)

        self.footer = UpExpandingContainer('footer', body, 0*PT, body.height)

        self.footer << Paragraph('Cryptographic Signature', style='footer title')
        fields = []
        fields.append(LabeledFlowable(Paragraph('Message:'),
                                      Paragraph(document.data['crypto_message'],
                                                style=STYLESHEET['footer content'])))
        fields.append(LabeledFlowable(Paragraph('Signature:'),
                                      Paragraph(self._signature(document),
                                                style=ParagraphStyle(base='footer content', typeface=nimbus_mono))))
        self.footer << FieldList(fields, style='footer fieldlist')
        verify_link = AnnotatedText('go to ascribe.io/verify to verify',
                                   annotation=HyperLink('https://www.ascribe.io/verify'))
        self.footer << Paragraph(verify_link, style=STYLESHEET['footer label'])

    def _signature(self, document):
        # TODO: auto-wrap
        signature = str(document.data['crypto_signature'])
        n = 110
        return " ".join([signature[i:i+n] for i in range(0, len(signature), n)])


class AscribeCertificate(Document):
    namespace = 'http://www.mos6581.org/ns/rficpaper'

    def __init__(self, data):
        title = ' - '.join((data['artist_name'], data['title']))
        super().__init__(STYLESHEET, backend=pdf, title=title)
        self.data = data
        image_data = BytesIO()
        r = requests.get(data['thumbnail'])
        buff = BytesIO(r.content)
        buff.seek(0)
        input_image = PILImage.open(buff)
        if 'transparency' in input_image.info:
            print('TRANSP')
            foreground = input_image.convert('RGBA')
            background = PILImage.new('RGBA', foreground.size, (255, 255, 255, 255))
            input_image = PILImage.alpha_composite(background, foreground)
        input_image.convert('RGB').save(image_data, 'PDF') #, **pilim.info) #, Quality=100)
        self.image = Chain(self)
        # assumes max_width < 350
        (_width, _length) = input_image.size
        print('width: %d' % _width)
        print('length: %d' % _length)
        max_length = 400
        if _length > max_length:
            width_pct = int(max_length/_length * 100)
        else:
            width_pct = 100
        print('width_pct: %d' % width_pct)
        self.image << Image(image_data, width=width_pct*PERCENT)
        # import pdb; pdb.set_trace()
        self.text = Chain(self)
        self.text << Paragraph(data['artist_name'], style='artist')
        self.text << Paragraph(data['title'], style='title')
        self.text << Paragraph(data['yearAndEdition_str'], style='year')
        fields = []
        owner_name = data['owner']
        fields.append(LabeledFlowable(Paragraph('Filetype:'), Paragraph(data['digital_work']['mime'])))
        fields.append(LabeledFlowable(Paragraph('Owner:'), Paragraph(owner_name)))
        if 'bitcoin_ID_noPrefix' in data.keys():
            bitcoin_id = data['bitcoin_ID_noPrefix']
        else:
            bitcoin_id = data['bitcoin_id']
        fields.append(LabeledFlowable(Paragraph('Artwork ID:'), Paragraph(bitcoin_id)))
        self.text << FieldList(fields)
        if 'ownershipHistory' in data.keys():
            history = data['ownershipHistory']
        else:
            history = data['ownership_history']
        self.text << Paragraph('Provenance/Ownership History', style='section title')
        self._history(history, 'ownership ascribed to')


        # self.text << Paragraph(data['crypto_signature'])

    def _history(self, items, action):
        for dtime_str, name in items:
            self.text << Paragraph(dtime_str + ' - ' + name)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


@app.route('/', methods=['POST'])
def certificate():
    print(request)
    print(request.form)
    json_data = request.form['data']

    data = json.loads(json_data)

    try:
        certificate = AscribeCertificate(data)
        pdf_file = certificate.render()
        # pdf_file = certificate.render('/home/dimi/coa.pdf')
        response = send_file(pdf_file,
                             attachment_filename='certificate.pdf',
                             mimetype='application/pdf')
        response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
        return response
    except Exception as e:
        print(str(e))
        pass


@app.route('/', methods=['GET'])
def test():
    try:
        json_data = data_json_faulty
        data = json.loads(json_data)
        certificate = AscribeCertificate(data)
        pdf_file = certificate.render()
        # pdf_file = certificate.render('/home/dimi/coa.pdf')
        response = send_file(pdf_file,
                             attachment_filename='certificate.pdf',
                             mimetype='application/pdf')
        response.headers.add('content-length', str(pdf_file.getbuffer().nbytes))
        return response
    except Exception as e:
        print(str(e))
        pass

if __name__ == "__main__":
    app.run(debug=True)
