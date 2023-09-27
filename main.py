import json
import requests
from tqdm import tqdm
from pprint import pprint

class VK:

   def __init__(self, access_token, user_id, version='5.131'):
       self.token = access_token
       self.id = user_id
       self.version = version
       self.params = {'access_token': self.token, 'v': self.version}

   def users_info(self):
       url = 'https://api.vk.com/method/users.get'
       params = {'user_ids': self.id}
       response = requests.get(url, params={**self.params, **params})
       response_json = response.json()
       error = response_json.get('error', '')
       if type(error) == dict:
           return error.get('error_msg', 'Ошибка авторизации')
       return response.json()

   def get_list_url_foto(self, max_foto=5):
       url = 'https://api.vk.com/method/photos.get'
       params = {'extended': 1, 'album_id': 'wall', 'owner_id': self.id}
       response = requests.get(url, params={**self.params, **params})

       response_foto = response.json()
       if response_foto.get('response', '') == '':
           if type(response_foto.get('error', '')) == dict:
               return response_foto['error'].get('error_msg', 'Не известная ошибка')
           return 'Не известная ошибка'

       data_foto = response_foto['response']

       max_items = data_foto['items'][:max_foto]

       list_url = []
       for item in tqdm(max_items, desc = 'Получение списка фотографий с VK'):
           sizes = sorted(item['sizes'], key=lambda i: (i['height'], i['width']), reverse=True)
           sizes[0]['url'].split('?')[0].split('.')
           attr_list = sizes[0]["url"].split("?")[0].split(".")
           exp = attr_list[len(attr_list) - 1]
           list_url.append({'url': sizes[0].get('url', ''), 'size': sizes[0].get('type', ''), 'file_name': f'VK_ID_{self.id}_{max_items.index(item)}_{item.get("likes", {}).get("count", 0)}.{exp}'})

       return list_url

class YD:

    def __init__(self):
        self.base_url = 'https://cloud-api.yandex.net'

    def upload_file_list(self, access_token, folder_name, file_list):
        headers = {
            'Authorization': access_token
        }
        params = {
            'path': '/'
        }

        response = requests.get(self.base_url + '/v1/disk/resources', headers = headers, params = params)
        if not response.status_code == 200:
            return "При обращении к Яндекс Диску произошла ошибка: " + response.json().get('message')

        is_folder = False
        list_folders = response.json().get('_embedded',{}).get('items', [])
        for folder in list_folders:
            if folder.get('name') == folder_name:
                is_folder = True
                break

        if not is_folder:
            response = requests.put(self.base_url + '/v1/disk/resources', headers=headers, params=params)

            if not response.status_code == 201:
                return "При обращении к Яндекс Диску произошла ошибка: " + response.json().get('message', f'Ошибка создания каталога {folder_name}')

        response_list = []
        for item in tqdm(file_list, desc='Загрузка списка фотографий на YD'):
            params['url'] = item['url']
            params['path'] = f'{folder_name}/{item["file_name"]}'
            response = requests.post(self.base_url + '/v1/disk/resources/upload', headers=headers, params=params)
            response_list.append({
                'file_name': item["file_name"],
                'size': item["size"],
            })

        return response_list

if __name__ == '__main__':
    access_token_VK = ''
    user_id = input('Введите ID пользователя VK: ')
    access_token_YD = input('Введите токен с Полигона Яндекс.Диска: ')

    vk = VK(access_token_VK, user_id)
    user_data = vk.users_info()

    if type(user_data) == str:
        print(user_data)
        exit()
    elif len(user_data.get('response', [])) == 0:
        print(f'Пользователь с ID {user_id} не найден')
        exit()

    # Получим список словарей фоток: (file_name, size, url)
    list_url_foto = vk.get_list_url_foto()
    if not type(list_url_foto) == list:
        print(list_url_foto)
        exit()

    yd = YD()
    response_list = yd.upload_file_list(access_token_YD, 'Image_VK', list_url_foto)

    if type(response_list) == list:
        with open('requiremеnts.txt', 'w') as f:
            f.writelines(json.dumps(response_list))
            f.close()
    else:
        pprint(response_list)
