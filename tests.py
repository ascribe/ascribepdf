import json

import pytest


piece_data = {
    'title': 'Alice in Cryptoland',
    'filesize': 370611,
    #'edition_number': -1,
    'check_stamp_query': '?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    'owner_timestamp': 'Jul. 29 2015, 16:21:51',
    'artist_name': 'Alice',
    'digital_work': {
        'isEncoding': 0,
        'mime': 'image',
        'hash': '16a78cd2bb628fd6fb14582668ed72d7',
        'encoding_urls': None,
        'id': 2509,
        'url_safe': 'https://d1qjsxua1o9x03.cloudfront.net/live%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F589566d5-5452-48ef-a7c9-88f5f4aefb86%2Fdigitalwork%2F589566d5-5452-48ef-a7c9-88f5f4aefb86.png',
        'url': 'https://d1qjsxua1o9x03.cloudfront.net/live/b6d767d2f8ed5d21a44b0e5886680cb9/589566d5-5452-48ef-a7c9-88f5f4aefb86/digitalwork/589566d5-5452-48ef-a7c9-88f5f4aefb86.png',
    },
    'bitcoin_id': '1FE7GhESMTN5tUS3TSma4CqTtgZVTV9fnR',
    'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/live%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F589566d5-5452-48ef-a7c9-88f5f4aefb86%2Fthumbnail%2F600x600%2Fthumbnail.png',
    'owner': 'Alice',
    'crypto_message': '1111111111*111111111*10/13*2015*2015Jul29-16:21:51',
    'crypto_signature': '2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    #'yearAndEdition_str': '2015, 10/13',
    'year_created': '2016',
    'filename': '.png',
    'check_stamp_url': 'http://localhost.com:3000/coa_verify/?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    'ownership_history': [['Jul. 29, 2015, 16:21:51', 'Registered by Schweinehund']],
    'num_editions': -1,
    'verify_owner_url': 'http://localhost.com:3000/coa_verify/',
}

edition_data = {
    'title': '111111111',
    'filesize': 370611,
    'edition_number': 10,
    'check_stamp_query': '?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    'owner_timestamp': 'Jul. 29 2015, 16:21:51',
    'artist_name': '1111111111',
    'digital_work': {
        'isEncoding': 0,
        'mime': 'image',
        'hash': '16a78cd2bb628fd6fb14582668ed72d7',
        'encoding_urls': None,
        'id': 2509,
        'url_safe': 'https://d1qjsxua1o9x03.cloudfront.net/live%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F589566d5-5452-48ef-a7c9-88f5f4aefb86%2Fdigitalwork%2F589566d5-5452-48ef-a7c9-88f5f4aefb86.png',
        'url': 'https://d1qjsxua1o9x03.cloudfront.net/live/b6d767d2f8ed5d21a44b0e5886680cb9/589566d5-5452-48ef-a7c9-88f5f4aefb86/digitalwork/589566d5-5452-48ef-a7c9-88f5f4aefb86.png',
    },
    'bitcoin_id': '1FE7GhESMTN5tUS3TSma4CqTtgZVTV9fnR',
    'thumbnail': 'https://d1qjsxua1o9x03.cloudfront.net/live%2Fb6d767d2f8ed5d21a44b0e5886680cb9%2F589566d5-5452-48ef-a7c9-88f5f4aefb86%2Fthumbnail%2F600x600%2Fthumbnail.png',
    'owner': 'Schweinehund',
    'crypto_message': '1111111111*111111111*10/13*2015*2015Jul29-16:21:51',
    'crypto_signature': '2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    'yearAndEdition_str': '2015, 10/13',
    'filename': '.png',
    'check_stamp_url': 'http://localhost.com:3000/coa_verify/?message=1111111111%2A111111111%2A10%2F13%2A2015%2A2015Jul29-16%3A21%3A51&signature=2CEC38ACD51F91D0A38CF85E8092C337CC18C4ADE1E0F86563D28A97C0442F9EF9202E25E95D85BB1BA5AC3FB18E290E51BC9D1A410D065C7EF716168A13C44F7FA1431404367A4934ECCCE3AA0DA6921A908909B0134A10D4CDBD372C53967FD02760B99FDBE21E1DEB64532305351CFB35E0245B26D54682CAF01F359DD0EDL',
    'ownership_history': [['Jul. 29, 2015, 16:21:51', 'Registered by Schweinehund']],
    'num_editions': 13,
    'verify_owner_url': 'http://localhost.com:3000/coa_verify/',
}


def test_app(app):
    assert app.debug
    assert app.testing


def test_post_edition_certificate(client):
    response = client.post('/', data={'data': json.dumps(edition_data)})
    assert response.status_code == 200


def test_post_piece_certificate(client):
    response = client.post('/piece',
                           data=json.dumps(piece_data),
                           content_type='application/json')
    assert response.status_code == 200
