import json
import time

import requests
from tqdm import tqdm
from datetime import datetime

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
           print(error.get('error_msg', 'Ошибка авторизации'))
           exit()

       if len(response_json.get('response', [])) == 0:
           print(f'Пользователь с ID {user_id} не найден')
           exit()

    def get_list_url_foto(self, max_foto=5):
       url = 'https://api.vk.com/method/photos.get'
       params = {'extended': 1, 'album_id': 'profile', 'owner_id': self.id}
       response = requests.get(url, params={**self.params, **params})

       response_foto = response.json()
       if response_foto.get('response', '') == '':
           if type(response_foto.get('error', '')) == dict:
               print(response_foto['error'].get('error_msg', 'Не известная ошибка'))
           else:
               print('Не известная ошибка')
           exit()

       data_foto = response_foto['response']

       max_items = data_foto['items'][:max_foto]

       list_file_name = []
       list_url = []
       for item in tqdm(max_items, desc = 'Получение списка фотографий с VK'):
           sizes = sorted(item['sizes'], key=lambda i: (i['height'], i['width']), reverse=True)
           attr_list = sizes[0]["url"].split("?")[0].split(".")
           exp = attr_list[len(attr_list) - 1]
           date_file = datetime.utcfromtimestamp(item['date']).strftime('%Y_%m_%d_%H_%M_%S')
           file_name = f'{item.get("likes", {}).get("count", 0)}'
           if file_name in list_file_name:
               file_name = file_name + '_' + date_file
           else:
               list_file_name.append(file_name)

           file_name = f'{file_name}.{exp}'
           list_url.append({'url': sizes[0].get('url', ''), 'size': sizes[0].get('type', ''), 'file_name': file_name})

       return list_url

class YD:

    def __init__(self):
        self.base_url = 'https://cloud-api.yandex.net'

    def check_folder(self, access_token, folder_name, headers, params):

        response = requests.get(self.base_url + '/v1/disk/resources', headers = headers, params = params)
        if response.status_code == 404:
            response = requests.put(self.base_url + '/v1/disk/resources', headers=headers, params=params)
            if not response.status_code == 201:
                print("При обращении к Яндекс Диску произошла ошибка: " + response.json().get('message', f'Ошибка создания каталога {folder_name}'))
                exit()

    def upload_file_list(self, access_token, folder_name, file_list):

        headers = {
            'Authorization': access_token
        }
        params = {
            'path': folder_name
        }

        self.check_folder(access_token, folder_name, headers, params)

        response_list = []
        for item in tqdm(file_list, desc='Загрузка списка фотографий на YD'):
            params['url'] = item['url']
            params['path'] = f'{folder_name}/{item["file_name"]}'
            response = requests.post(self.base_url + '/v1/disk/resources/upload', headers=headers, params=params)
            time.sleep(1)
            response_list.append({
                'file_name': item["file_name"],
                'size': item["size"],
            })

        with open('results.json', 'w') as f:
            f.writelines(json.dumps(response_list))
            f.close()


if __name__ == '__main__':

    access_token_VK = ''
    user_id = input('Введите ID пользователя VK: ')
    access_token_YD = input('Введите токен с Полигона Яндекс.Диска: ')

    vk = VK(access_token_VK, user_id)
    vk.users_info()

    # Получим список словарей фоток: (file_name, size, url)
    list_url_foto = vk.get_list_url_foto()

    yd = YD()
    response_list = yd.upload_file_list(access_token_YD, 'Image_VK', list_url_foto)
