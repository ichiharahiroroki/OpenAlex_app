
import requests
def get_instance_id():
    try:
        # メタデータサービスのトークン取得エンドポイント
        token_url = "http://169.254.169.254/latest/api/token"
        metadata_url = "http://169.254.169.254/latest/meta-data/instance-id"

        # トークンを取得
        token_response = requests.put(
            token_url, 
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, 
            timeout=5
        )
        token_response.raise_for_status()
        token = token_response.text

        # メタデータを取得
        response = requests.get(
            metadata_url, 
            headers={"X-aws-ec2-metadata-token": token}, 
            timeout=5
        )
        response.raise_for_status()
        return response.text  # インスタンスIDを返す

    except requests.RequestException:
        # EC2メタデータにアクセスできない場合、ローカル環境と判断
        return "local"

if __name__ == "__main__":
    instance_id = get_instance_id()
    print(f"Instance ID: {instance_id}")