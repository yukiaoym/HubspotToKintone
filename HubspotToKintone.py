import json
import hubspot
from pprint import pprint
# from hubspot.crm.deals import ApiException
# from hubspot.crm.line_items import ApiException
import requests

hubspot_access_token = ''
client = hubspot.Client.create(access_token=hubspot_access_token)
hubspot_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer %s' % hubspot_access_token
    }
H_BASE_URL = 'https://api.hubapi.com'
    
def getAssociatedIdList(deal_id, object):
    url = '{}/crm/v4/objects/deals/{}/associations/{}'.format(H_BASE_URL, deal_id, object)
    id_list = []
    response = requests.request("GET", url, headers=hubspot_headers)
    j_response = response.json()
    for i in j_response["results"]:
        if object == 'companies':
            for j in i["associationTypes"]:
                if j["label"] == 'Primary':
                    id = i["toObjectId"]
                    id_list.append(id)
        else:
            id = i["toObjectId"]
            id_list.append(id)
    return id_list

def getInfo(id, object, output_list):
    info_dict = {}
    if object == 'companies':
        api_response = client.crm.companies.basic_api.get_by_id(company_id=id, properties=output_list, archived=False)
    elif object == 'contacts':
        api_response = client.crm.contacts.basic_api.get_by_id(contact_id=id, properties=output_list, archived=False)
    elif object == 'line_items':
        api_response = client.crm.line_items.basic_api.get_by_id(line_item_id=id, properties=output_list, archived=False)    
    
    for i in output_list:
        info_dict[i] = api_response.properties[i]
    return info_dict

def paramNone(param):
    if param is None:
        param = ""
    return param
    
def lambda_handler(event, context):
    
    url = 'https://checkip.amazonaws.com/'
    ip_response = requests.get(url)
    print(ip_response.text)

    deal_id = event["deal_id"]
    company_id_list = getAssociatedIdList(deal_id, 'companies')
    contact_id_list = getAssociatedIdList(deal_id, 'contacts')
    line_items_id_list = getAssociatedIdList(deal_id, 'line_items')
    

    import_dict = {}
    if company_id_list:
        company_dict = getInfo(company_id_list[0], 'companies', ["name", "domain"])
        import_dict['ご契約社名'] = {'value': company_dict['name']}
        import_dict['ドメイン'] = {'value': company_dict['domain']}
    
    if contact_id_list:
        contact_output_list = ["company", "lastname", "firstname", "email", "phone"]
        contact_dict = getInfo(contact_id_list[0], 'contacts', contact_output_list)
        import_dict['開通通知用_会社名'] = {'value': contact_dict['company']}
        import_dict['開通通知用_担当者名'] = {'value':  paramNone(contact_dict['lastname']) + " " + paramNone(contact_dict['firstname'])}
        import_dict['開通通知用_TO宛先'] = {'value': contact_dict['email']}
    
    if line_items_id_list:
        table_list = []
        for i in line_items_id_list:
            output_list = ["name", "deal_type", "price", "quantity"]
            items_dict = getInfo(i, 'line_items', output_list)
            tmp_dict = {
                '商品名': {'value': items_dict['name']},
                '案件分類': {'value': items_dict['deal_type']},
                '数量': {'value': items_dict['quantity']},
                '単価': {'value': items_dict['price']}
            }
            table_dict = {"value": tmp_dict}
            table_list.append(table_dict)
        import_dict['商品一覧'] = {'value': table_list}

    
    import_data = {
        "app": 55,
        "record": import_dict
    }
    #print(import_data)
    
    kin_headers = {'Content-Type': 'application/json', 'X-Cybozu-API-Token': ''}
    K_BASE_URL = 'https://hoge.cybozu.com/k/v1'
    import_url = '{}/record.json'.format(K_BASE_URL)
    response = requests.post(import_url, headers=kin_headers, json=import_data)
    print(response.text)

    return {
        'statusCode': 200,
        'body': ip_response.text
    }
    
