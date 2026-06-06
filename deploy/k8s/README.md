# K8s 部署模板

这些 YAML 是生产化展示模板，适合说明 API 服务如何接入探针、Secret、ConfigMap 和审计持久化。真实生产环境仍应接入公司的镜像仓库、网关、日志平台、密钥系统和集中数据库。

## 应用顺序

```bash
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secret.example.yaml
kubectl apply -f deploy/k8s/pvc.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
```

## 检查

```bash
kubectl rollout status deployment/im-guard-api
kubectl get pods -l app=im-guard-api
kubectl logs deploy/im-guard-api --tail=100
kubectl port-forward svc/im-guard-api 8000:8000
curl http://127.0.0.1:8000/ready
```

## 更新与回滚

```bash
kubectl set image deployment/im-guard-api im-guard-api=ai-im-guard-ml:next
kubectl rollout status deployment/im-guard-api
kubectl rollout undo deployment/im-guard-api
```

## 停止展示环境

```bash
kubectl delete -f deploy/k8s/service.yaml
kubectl delete -f deploy/k8s/deployment.yaml
kubectl delete -f deploy/k8s/pvc.yaml
kubectl delete -f deploy/k8s/secret.example.yaml
kubectl delete -f deploy/k8s/configmap.yaml
```

## 注意

- `secret.example.yaml` 只作模板，生产化展示优先注入 `IM_GUARD_API_TOKEN_HASHES`，真实 token 应由密钥系统或网关托管。
- SQLite PVC 适合单服务展示，不适合多副本高并发生产写入；真实生产建议换成 PostgreSQL 或日志平台。
- 多副本 API 如需共享审计查询，应使用集中存储。
