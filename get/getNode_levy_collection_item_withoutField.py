import requests
import pandas as pd
import secrets

secretsVersion = input('To edit production server, enter secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        print('Editing Stage')
else:
    print('Editing Stage')

baseURL = secrets.baseURL

type = 'jsonapi/node/levy_collection_item'
field = 'field_publish_date_year'
ext = '?filter[a-label][condition][path]='+field+'&filter[a-label][condition][operator]=IS NULL'

# List of single value fields
relation_dict = ['node_type', 'field_pdf', 'field_publisher']
# List of repeatable fields
relation_list = ['field_subjects', 'field_people',
                 'field_instrumentation_metadata', 'field_images',
                 'field_duplicates', 'field_composition_metadata']
# List of fields not to record
skip_fields = ['body', 'revision_timestamp', 'revision_log', 'path',
               'revision_translation_affected', 'drupal_internal__vid',
               'promote', 'sticky', 'default_langcode']


def fetchData(data):
    for entry in data:
        item = {}
        type = entry.get('type')
        id = entry.get('id')
        item['type'] = type
        item['id'] = id
        attributes = entry.get('attributes')
        relationships = entry.get('relationships')
        for key, value in attributes.items():
            if key in skip_fields:
                pass
            else:
                item[key] = value
        for relation in relation_dict:
            data = relationships[relation]['data']
            if data:
                rel_type = relationships[relation]['data']['type']
                rel_id = relationships[relation]['data']['id']
                item[relation] = rel_type+':::'+rel_id
        for relation in relation_list:
            rel_list = relationships[relation]['data']
            if rel_list:
                for x in rel_list:
                    rel_type = x.get('type')
                    rel_id = x.get('id')
                    if rel_id:
                        existing = item.get(relation)
                        if existing:
                            item[relation] = existing+'|'+rel_type+':::'+rel_id
                        else:
                            item[relation] = rel_type+':::'+rel_id
                if relation == 'field_people':
                    print(relationships[relation])
                    print(id)
        allItems.append(item)


# Loop through item and grabs metadata, chuck into DataFrame.
allItems = []
totalItemCount = 0
nextList = []
while totalItemCount < 10000:
    if not nextList:
        r = requests.get(baseURL+type+ext).json()
    else:
        next = nextList[0]
        r = requests.get(next).json()
    data = r.get('data')
    item_count = (len(data))
    totalItemCount = item_count + totalItemCount
    fetchData(data)
    nextList.clear()
    links = r.get('links')
    nextDict = links.get('next')
    if nextDict:
        next = nextDict.get('href')
        nextList.append(next)
    else:
        break
print('')


all_items = pd.DataFrame.from_dict(allItems)
print(all_items.head)

# Create CSV for new DataFrame.
all_items.to_csv('levyCollectionItemsWithout'+field+'.csv', index=False)
