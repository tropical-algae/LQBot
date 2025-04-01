from minio import Minio
from datetime import timedelta
from qq_bot.utils.config import settings


class MinioServer:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        buckets: list[str],
    ):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False  # 使用http
        )
        self.buckets = buckets
        self._init_bucket()

    def _init_bucket(self):
        for bkt_name in self.buckets:
            if not self.client.bucket_exists(bkt_name):
                self.client.make_bucket(bkt_name)

    def upload_files(
        self, 
        bucket: str, 
        upload_file: dict[str, str]
    ) -> list[str]:
        """上传文件

        Args:
            bucket (str): 桶名
            upload_file (dict[str, str]): 上传的文件映射，key为本地文件路径，value为云端文件路径

        Returns:
            str: _description_
        """
        results = []
        for file_path, object_name in upload_file.items():
            result = self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path
            )
            results.append(result)
        return results

    def get_file_url(self, bucket: str, object_path: str | list[str]) -> str | list[str]:
        
        assert isinstance(object_path, str) or isinstance(object_path, list)

        result = []
        if isinstance(object_path, str):
            data = [object_path]
        else:
            data = object_path

        for d in data:
            result.append(
                self.client.presigned_get_object(
                    bucket, d, expires=timedelta(days=1)
                )
            )
        return result[0] if isinstance(object_path, str) else result

minio = MinioServer(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SCCRET_KEY,
    buckets=[
        settings.MINIO_JM_BOCKET_NAME, 
        settings.MINIO_RANDOM_PIC_BOCKET_NAME, 
        settings.MINIO_RANDOM_SETU_BOCKET_NAME
    ],
)

# def upload_file():
#     # 创建minio客户端
#     client = Minio(endpoint="xxx.xxx.xxx.xxx:xxxxx",
#                    access_key='xxxxx',
#                    secret_key='xxxxx',
#                    secure=False  # 使用http
#                    )
#     # 创建桶
#     client.make_bucket(bucket_name=settings.MINIO_JM_BOCKET_NAME)

#     # 删除桶
#     client.remove_bucket(barrel)

#     # 获取桶列表
#     barrel_list = client.list_buckets()
#     print(barrel_list)

#     # 获取桶中的数据信息,不查子文件夹中的数据
#     bucket_objects = client.list_objects(barrel)
#     for bucket_object in bucket_objects:
#         print(bucket_object.object_name)

#     # 列出名称以1-4开头的数据信息
#     bucket_objects = client.list_objects(barrel, prefix="1-4")
#     for bucket_object in bucket_objects:
#         print(bucket_object)

#     # 递归遍历桶中的数据信息,读取子文件夹下的文件
#     bucket_objects = client.list_objects(barrel, recursive=True)
#     for bucket_object in bucket_objects:
#         print(bucket_object.object_name)

#     # 递归查找以/data开头的数据信息
#     data = list()
#     for root in ["/data1"]:
#         bucket_objects = client.list_objects(barrel, prefix=root, recursive=True)
#         for bucket_object in bucket_objects:
#             data.append(bucket_object.object_name)
#             # print(bucket_object.object_name)
#     print(len(data))

#     # 递归查找以data1同一层级的数据信息
#     bucket_objects = client.list_objects(barrel, recursive=True, start_after="data1")
#     for bucket_object in bucket_objects:
#         print(bucket_object.object_name)

#     # 上传文件, bucket_name: 桶名称, object_name:上传到桶中完整的文件路径, file_path:文件本地所在完整路径
#     result = client.fput_object(bucket_name=barrel, object_name="data1/" + file_name,
#     file_path=file_path + "/" + file_name)
#     print(result.object_name, result.bucket_name, result.etag)

#     # 下载文件,bucket_name: 桶名称, object_name:被下载文件完整路径, file_path:保存到本地的完整路径
#     result = client.fget_object(bucket_name=barrel, object_name="data1/60719d5c50e833d4fa8af3b7412d40000a2.jpg",
#                                 file_path=r"E:\集成资料\测试项目\minio\1.jpg")
#     print(result.object_name, result.content_type, result.owner_name)

#     # 判断桶是否存在
#     check_bucket = client.bucket_exists(barrel)
#     if not check_bucket:  # 不存在则创建桶
#         client.make_bucket(barrel)