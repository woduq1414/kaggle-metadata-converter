# html fastapi 전송방법

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
import xml.etree.ElementTree as ET

import os
from pprint import pprint

from config import KAGGLE_USERNAME, KAGGLE_KEY

os.environ['KAGGLE_USERNAME'] = KAGGLE_USERNAME
os.environ['KAGGLE_KEY'] = KAGGLE_KEY

from kaggle.api.kaggle_api_extended import KaggleApi

templates = Jinja2Templates(directory="templates")

app = FastAPI(docs_url="/documentation", redoc_url=None)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/convert")
async def convert_endpoint(request: Request):
    # get query param
    url = request.query_params.get("url")
    schema = request.query_params.get("schema")

    result = convert(url, schema)

    return {
        "result": result

    }


def convert(url, schema):
    # example url : https://www.kaggle.com/shaunthesheep/microsoft-catsvsdogs-dataset
    # example url : https://www.kaggle.com/kmader/colorectal-histology-mnist

    url = url.replace("kaggle.com/datasets", "kaggle.com")
    owner = url.split('/')[3]
    datasetName = url.split('/')[4]

    api = KaggleApi()
    api.authenticate()

    metadata = api.metadata_get(owner, datasetName)
    pprint(metadata)

    def convert_metadata_to_mods(metadata):
        # Create MODS root element
        mods = ET.Element('mods', {
            'xmlns': 'http://www.loc.gov/mods/v3',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-7.xsd',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink'
        })
        # Add title
        title_info = ET.SubElement(mods, 'titleInfo')
        title = ET.SubElement(title_info, 'title')
        title.text = metadata['info']['title']

        # Add subtitle
        if 'subtitle' in metadata['info']:
            subtitle_info = ET.SubElement(mods, 'titleInfo')
            subtitle = ET.SubElement(subtitle_info, 'subtitle')
            subtitle.text = metadata['info']['subtitle']

        if 'datasetSlug' in metadata['info']:
            subtitle_info2 = ET.SubElement(mods, 'titleInfo')
            subtitle2 = ET.SubElement(subtitle_info2, 'subtitle')
            subtitle2.text = metadata['info']['datasetSlug']

        # Add Name

        name = ET.SubElement(mods, 'name', type='personal')
        name_part = ET.SubElement(name, 'namePart')
        name_part.text = metadata['info']['ownerUser']
        role = ET.SubElement(name, 'role')
        role_term = ET.SubElement(role, 'roleTerm', type='text')
        role_term.text = 'creator'

        # Add Collaborators

        if 'collaborators' in metadata['info']:
            for collaborator in metadata['info']['collaborators']:
                name = ET.SubElement(mods, 'name', type='personal')
                name_part = ET.SubElement(name, 'namePart')
                name_part.text = collaborator["username"]
                role = ET.SubElement(name, 'role')
                role_term = ET.SubElement(role, 'roleTerm', type='text')
                role_term.text = collaborator["role"]

        # Add typeOfResource
        type_of_resource = ET.SubElement(mods, 'typeOfResource')
        type_of_resource.text = 'classificationDataset'

        # Add subject keywords
        if 'keywords' in metadata['info']:
            for keyword in metadata['info']['keywords']:
                subject = ET.SubElement(mods, 'subject')
                topic = ET.SubElement(subject, 'topic')
                topic.text = keyword

        note = ET.SubElement(mods, 'note', type='format')
        note.text = "integer"

        if 'licenses' in metadata['info']:
            for license in metadata['info']['licenses']:
                note = ET.SubElement(mods, 'note', type='license')
                note.text = license['name']

        # Add usage notes
        usage_notes = [
            ('Total Downloads', str(metadata['info']['totalDownloads'])),
            ('Total Views', str(metadata['info']['totalViews'])),
            ('Total Votes', str(metadata['info']['totalVotes'])),
            ('Usability Rating', str(metadata['info']['usabilityRating'])),
        ]
        for note_type, note_value in usage_notes:
            note = ET.SubElement(mods, 'note', type='usage')
            note.text = f'{note_type}: {note_value}'

        # Add origin info
        origin_info = ET.SubElement(mods, 'originInfo')
        publisher = ET.SubElement(origin_info, 'publisher')
        publisher.text = metadata['info']['ownerUser']

        identifier = ET.SubElement(mods, 'identifier', type='url')
        identifier.text = url

        identifier2 = ET.SubElement(mods, 'identifier', type='id')
        identifier2.text = str(metadata['info']['datasetId'])

        # Add abstract
        abstract = ET.SubElement(mods, 'abstract')
        abstract.text = metadata['info']['description']

        # Convert MODS element tree to string
        mods_string = ET.tostring(mods, encoding='utf-8', method='xml').decode('utf-8')

        return '<?xml version="1.0" encoding="UTF-8"?>' + mods_string

    def convert_metadata_to_dublin_core(metadata):
        # Create Dublin Core root element

        metadata = metadata["info"]

        rdf_root = ET.Element('rdf:RDF', {
            'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
            , 'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })

        dublin_core = ET.SubElement(rdf_root, 'rdf:Description')

        # Title
        title_element = ET.SubElement(dublin_core, 'dc:title')
        title_element.text = metadata['title']

        # subtitle

        if 'subtitle' in metadata:
            subtitle_element = ET.SubElement(dublin_core, 'dc:title')
            subtitle_element.text = metadata['subtitle']

        if 'datasetSlug' in metadata:
            subtitle_element2 = ET.SubElement(dublin_core, 'dc:title')
            subtitle_element2.text = metadata['datasetSlug']

        # Creator
        creator_element = ET.SubElement(dublin_core, 'dc:creator')
        creator_element.text = metadata['ownerUser']

        # Contributor

        if 'collaborators' in metadata:
            for collaborator in metadata['collaborators']:
                contributor_element = ET.SubElement(dublin_core, 'dc:contributor')
                contributor_element.text = collaborator["username"]

        # Description
        description_element = ET.SubElement(dublin_core, 'dc:description')
        description_element.text = metadata['description']

        # Add usage notes
        usage_notes = [
            ('Total Downloads', str(metadata['totalDownloads'])),
            ('Total Views', str(metadata['totalViews'])),
            ('Total Votes', str(metadata['totalVotes'])),
            ('Usability Rating', str(metadata['usabilityRating'])),
        ]
        desc_text = ""
        for note_type, note_value in usage_notes:
            desc_text += f'{note_type}: {note_value}\n'
        description_elemment2 = ET.SubElement(dublin_core, 'dc:description')
        description_elemment2.text = desc_text

        # Subjects
        for keyword in metadata['keywords']:
            subject_element = ET.SubElement(dublin_core, 'dc:subject')
            subject_element.text = keyword

        # Identifier
        identifier_element = ET.SubElement(dublin_core, 'dc:identifier')
        identifier_element.text = str(metadata['datasetId'])

        identifier_element2 = ET.SubElement(dublin_core, 'dc:identifier')
        identifier_element2.text = url

        # Publisher
        publisher_element = ET.SubElement(dublin_core, 'dc:publisher')
        publisher_element.text = metadata['ownerUser']

        # Format
        format_element = ET.SubElement(dublin_core, 'dc:format')
        format_element.text = 'integer'

        # Type

        type_element = ET.SubElement(dublin_core, 'dc:type')
        type_element.text = 'classificationDataset'

        # Rights

        rights_element = ET.SubElement(dublin_core, 'dc:rights')
        for license in metadata['licenses']:
            rights_element.text = license['name']

        # Create XML tree
        tree = ET.ElementTree(dublin_core)

        # Return XML string
        return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(dublin_core, encoding='unicode')

    if schema == 'mods':

        mods_metadata = convert_metadata_to_mods(metadata)
        print(mods_metadata)

        return {
            "origin": metadata,
            "converted": mods_metadata
        }
    elif schema == "dc":

        dc_metadata = convert_metadata_to_dublin_core(metadata)
        print(dc_metadata)

        return {
            "origin": metadata,
            "converted": dc_metadata
        }
