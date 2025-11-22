# docker-External-Knowledge-Base
Hosting external knowledge base for Dify.


----

# Reference

https://docs.dify.ai/en/guides/knowledge-base/external-knowledge-api

----

# Testing

- Postman Interceptor https://chromewebstore.google.com/detail/postman-interceptor/aicmkgpgakddgnaphhhpliifpcfhicfo?hl=en-US&utm_source=ext_sidebar

# Troubleshoot

如果出現
````
[+] Running 1/0                                                                                                                                                 
 ✘ Network docker-external-knowledge-base_docker_external_knowledge_base  Error                                                                            0.0s 
failed to create network docker-external-knowledge-base_docker_external_knowledge_base: Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
````

則清理網路：

````bash
docker network prune
````