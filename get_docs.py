import requests
import time
from config import APP_ID, APP_SECRET

# 飞书API的基本URL
BASE_URL = 'https://open.feishu.cn/open-apis'

# 获取 tenant_access_token
def get_tenant_access_token():
    url = f'{BASE_URL}/auth/v3/tenant_access_token/internal/'
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    payload = {
        'app_id': APP_ID,
        'app_secret': APP_SECRET
    }
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    # 检查访问令牌是否成功获取
    if response_data.get('code') != 0:
        raise Exception(f"Failed to get tenant access token: {response_data}")
    print('tenant_access_token:', response_data['tenant_access_token'])
    return response_data['tenant_access_token']

# 获取文件夹中的文件列表
def get_folder_docs(folder_token, tenant_access_token):
    url = f'{BASE_URL}/drive/v1/files?direction=DESC&folder_token={folder_token}&order_by=EditedTime'
    headers = {
        'Authorization': f'Bearer {tenant_access_token}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print("Response text:", response.text)
        return []
    
    try:
        data = response.json()
        fileList = data.get('data', {}).get('files', [])
        print('fileList:', [el["name"] for el in fileList])
        return fileList
    except ValueError:
        print("Error: Failed to parse JSON response.")
        print("Response text:", response.text)
        return []
    
# 创建导出任务
# https://open.feishu.cn/document/server-docs/docs/drive-v1/export_task/create?appId=cli_a7a99766a47f900c
def create_export_task(doc_token, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }

    payload = {
        'file_extension': 'docx',
        'token': doc_token,
        'type': 'docx'
    }

    response = requests.post('https://open.feishu.cn/open-apis/drive/v1/export_tasks', json=payload, headers=headers)

    print(response.json())
    response_data = response.json()
    if response_data.get('code') != 0:
        raise Exception(f"Failed to get tenant access token: {response_data.get('msg')} (code: {response_data.get('code')})")

    return response_data['data']['ticket']
    
def request_task_progress(ticket, doc_token, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}'
    }
    response = requests.get(f'https://open.feishu.cn/open-apis/drive/v1/export_tasks/{ticket}?token={doc_token}', headers=headers)
    
    print(response.json())
    response_data = response.json()
    if(response_data.get('code') == 0):
        if(response_data['data']['result']['job_status'] == 0):
          file_token = response_data['data']['result']['file_token']
          download_exported_file(file_token, tenant_access_token)
        
def download_exported_file(file_token, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}'
    }

    response = requests.get(f'https://open.feishu.cn/open-apis/drive/v1/export_tasks/file/{file_token}/download', headers=headers)
    
    # print(response.json())

    save_path = './test.docx'
    # 检查响应状态
    if response.status_code == 200:
        # 打开文件并以二进制写入模式保存内容
        with open(save_path, 'wb') as file:
            file.write(response.content)  # 写入二进制流
        print(f"文件已成功保存为: {save_path}")
    else:
        print(f"下载失败，状态码: {response.status_code}")
        print("响应内容:", response.text)


# 主程序
if __name__ == "__main__":
    folder_token = 'SEsjfIT2kllhAgdvFPIcVDVenrC'  # 替换为你的文件夹token
    tenant_access_token = get_tenant_access_token()
    docs = get_folder_docs(folder_token, tenant_access_token)
    doc_token = docs[1]['token']
    ticket = create_export_task(doc_token, tenant_access_token)

    # 每隔1秒查询一次
    time.sleep(10)
    request_task_progress(ticket, doc_token, tenant_access_token)
