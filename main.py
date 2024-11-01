import requests
import time
from config import APP_ID, APP_SECRET, FOLDER_TOKEN

# 获取 tenant_access_token
def get_tenant_access_token():
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    payload = {
        'app_id': APP_ID,
        'app_secret': APP_SECRET
    }
    response = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/', json=payload, headers=headers)
    response_data = response.json()
    # 检查访问令牌是否成功获取
    if response_data.get('code') != 0:
        raise Exception(f"Failed to get tenant access token: {response_data}")
    
    print('获取tenant_access_token成功:', response_data['tenant_access_token'])
    return response_data['tenant_access_token']

# 获取文件夹中的文件列表
def get_folder_docs(folder_token, tenant_access_token):
    url = f'https://open.feishu.cn/open-apis/drive/v1/files?direction=DESC&folder_token={folder_token}&order_by=EditedTime'
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
        print('获取文件列表成功:', [el["name"] for el in fileList])
        
        # 返回文件列表
        return fileList
    except ValueError:
        print("Error: Failed to parse JSON response.")
        print("Response text:", response.text)
       
        return []
    
# 创建单个导出任务
# https://open.feishu.cn/document/server-docs/docs/drive-v1/export_task/create?appId=cli_a7a99766a47f900c
def create_export_task(doc, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }

    extension = {
        'docx': 'docx',
        'sheet': 'xlsx',
    }
    payload = {
        'file_extension': extension[doc['type']],
        'token': doc['token'],
        'type': doc['type']
    }

    response = requests.post('https://open.feishu.cn/open-apis/drive/v1/export_tasks', json=payload, headers=headers)

    print('创建导出任务成功：', response.json())
    response_data = response.json()
    if response_data.get('code') != 0:
        raise Exception(f"Failed to get tenant access token: {response_data.get('msg')} (code: {response_data.get('code')})")

    return response_data['data']['ticket']

# 批量创建导出任务
def batch_create_export_task(docs, tenant_access_token):
    for doc in docs:
        if doc['type'] not in ['docx', 'sheet']:
            continue
        ticket = create_export_task(doc, tenant_access_token)
        doc['ticket'] = ticket
    return docs

# 批量查询任务进度
def batch_request_task_progress(docs, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}'
    }
    finish_count = 0
    wait_seconds = 10
    while (finish_count < len(docs)):
        print(f'{wait_seconds}秒后查询导出结果……')
        time.sleep(wait_seconds)
        for doc in docs:
            if 'done' not in doc:
                response = requests.get(f'https://open.feishu.cn/open-apis/drive/v1/export_tasks/{doc['ticket']}?token={doc['token']}', headers=headers)
                
                response_data = response.json()
                if((response_data.get('code') == 0) & (response_data['data']['result']['job_status'] == 0)):
                    file_token = response_data['data']['result']['file_token']
                    download_exported_file(file_token, doc, tenant_access_token)
                    doc['done'] = True
                    finish_count += 1
                    print(f'已完成{finish_count}/{len(docs)}')
                
            
# 下载单个文件
def download_exported_file(file_token, doc, tenant_access_token):
    headers = {
        'Authorization': f'Bearer {tenant_access_token}'
    }

    response = requests.get(f'https://open.feishu.cn/open-apis/drive/v1/export_tasks/file/{file_token}/download', headers=headers)
    
    save_path = f'./{doc['name']}.{doc['type']}'
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
    folder_token = FOLDER_TOKEN  # 替换为你的文件夹token
    tenant_access_token = get_tenant_access_token()
    docs = get_folder_docs(folder_token, tenant_access_token) # 获取文件夹中的文件列表
    
    '''
    docs = 
    [{
        'created_time': '1711352459', 
        'modified_time': '1725866769', 
        'name': 'IM每日监控指标', 
        'owner_id': 'ou_a6c5def8ef271d8ec06e191fe1aff102', 
        'parent_token': 'SEsjfIT2kllhAgdvFPIcVDVenrC', 
        'token': 'X1jRbx552miXyjnsHpHcw45QnYg', 
        'type': 'mindnote', 
        'url': 'https://kxc9f7uc79s.feishu.cn/mindnotes/X1jRbx552miXyjnsHpHcw45QnYg'
    }]
    doc_token = docs[1]['token']
    
    解析出数组中的doc_token, 文件名, 文件类型, 批量创建导出任务, 任务的ticket也分别存在各项的ticket字段中
    '''
    docs = batch_create_export_task(docs, tenant_access_token)
    
    print('批量创建导出任务成功')

    # 此时docs数组中包含ticket字段

    batch_request_task_progress(docs, tenant_access_token)
