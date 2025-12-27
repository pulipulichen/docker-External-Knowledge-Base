# docker-External-Knowledge-Base
Hosting external knowledge base for Dify.


----

# Reference

https://docs.dify.ai/en/guides/knowledge-base/external-knowledge-api

----

# Testing

- Postman Interceptor https://chromewebstore.google.com/detail/postman-interceptor/aicmkgpgakddgnaphhhpliifpcfhicfo?hl=en-US&utm_source=ext_sidebar


# Mount


NFS

```bash
mkdir ./knowledge_base_files/documents
mount -t nfs 192.168.1.1:/documents ./knowledge_base_files/documents
```

Rclone

```bash
rclone config
rclone mount nas-documents: ./knowledge_base_files/documents --daemon
```

檔案名稱變成亂碼的處理方式

```bash
apt update
apt install -y locales
sed -i 's/^# zh_TW.UTF-8/zh_TW.UTF-8/' /etc/locale.gen
locale-gen
locale-gen en_US.UTF-8
export LC_ALL=en_US.UTF-8
echo "LANG=en_US.UTF-8" > /etc/default/locale
echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale
```